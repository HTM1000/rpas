# -*- coding: utf-8 -*-
"""
Google Drive Uploader - Auto Upload de Evidências
==================================================

Este módulo implementa upload automático de evidências para Google Drive com:
- Autenticação OAuth2 (mesmas credenciais do RPA)
- Criação automática de pastas por data (DDMMAAAA)
- Retry em background para uploads falhados
- Organização hierárquica (evidencias / DDMMAAAA / arquivos)

Autor: Claude Code
Data: 2026-01-06
"""

import os
import json
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from typing import Optional, Dict, List
import time


class DriveUploader:
    """
    Uploader automático de evidências para Google Drive.

    Gerencia upload de JSONs e screenshots para pasta organizada por data.
    """

    # Scopes necessários para Google Drive
    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    def __init__(
        self,
        credentials_path: str = "CredenciaisOracle.json",
        token_path: str = "token.json",
        evidencias_folder_id: str = "1SRH4yOJc2DrG0aQspAek7RMH8w6yG_Yj"
    ):
        """
        Inicializa o uploader do Google Drive.

        Args:
            credentials_path: Caminho do arquivo de credenciais OAuth
            token_path: Caminho do token de autenticação
            evidencias_folder_id: ID da pasta raiz de evidências no Drive
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.evidencias_folder_id = evidencias_folder_id

        self.service = None
        self.fila_retry = []  # Fila de uploads para retry

    def _authenticate(self):
        """Autentica no Google Drive usando OAuth2."""
        creds = None

        # Carregar token se existir
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

        # Se não tem credenciais válidas, fazer login
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(f"Arquivo de credenciais não encontrado: {self.credentials_path}")

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)

            # Salvar token para próximas execuções
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        # Construir serviço do Drive
        self.service = build('drive', 'v3', credentials=creds)

    def verificar_criar_pasta(self, nome_pasta: str, parent_id: str) -> str:
        """
        Verifica se pasta existe, se não cria.

        Args:
            nome_pasta: Nome da pasta a verificar/criar
            parent_id: ID da pasta pai

        Returns:
            ID da pasta (existente ou recém-criada)
        """
        if self.service is None:
            self._authenticate()

        # Buscar pasta existente
        query = f"name='{nome_pasta}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"

        try:
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            items = results.get('files', [])

            if items:
                # Pasta existe
                return items[0]['id']
            else:
                # Criar pasta
                file_metadata = {
                    'name': nome_pasta,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [parent_id]
                }

                folder = self.service.files().create(
                    body=file_metadata,
                    fields='id'
                ).execute()

                return folder.get('id')

        except HttpError as error:
            print(f"Erro ao verificar/criar pasta: {error}")
            raise

    def upload_arquivo(
        self,
        file_path: str,
        folder_id: str,
        max_retries: int = 3
    ) -> Optional[Dict]:
        """
        Faz upload de um arquivo para o Google Drive.

        Args:
            file_path: Caminho do arquivo local
            folder_id: ID da pasta de destino no Drive
            max_retries: Número máximo de tentativas

        Returns:
            Dict com informações do arquivo (id, webViewLink) ou None se falhar
        """
        if self.service is None:
            self._authenticate()

        if not os.path.exists(file_path):
            print(f"Arquivo não encontrado: {file_path}")
            return None

        file_name = os.path.basename(file_path)

        # Detectar MIME type
        mime_type = 'application/octet-stream'
        if file_path.endswith('.json'):
            mime_type = 'application/json'
        elif file_path.endswith('.png'):
            mime_type = 'image/png'
        elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
            mime_type = 'image/jpeg'

        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }

        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

        # Tentar upload com retry
        for tentativa in range(max_retries):
            try:
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, webViewLink, webContentLink'
                ).execute()

                return {
                    'file_id': file.get('id'),
                    'webViewLink': file.get('webViewLink'),
                    'webContentLink': file.get('webContentLink'),
                    'nome_arquivo': file_name
                }

            except HttpError as error:
                print(f"Tentativa {tentativa+1}/{max_retries} falhou: {error}")

                if tentativa < max_retries - 1:
                    # Aguardar antes de retry (exponential backoff)
                    time.sleep(2 ** tentativa)
                else:
                    # Última tentativa falhou
                    return None

        return None

    def upload_evidencia_completa(
        self,
        json_path: str,
        screenshot_pre_path: str = None,
        screenshot_pos_path: str = None,
        data_str: str = None
    ) -> Dict:
        """
        Faz upload completo de uma evidência (JSON + screenshots).

        Args:
            json_path: Caminho do JSON de evidência
            screenshot_pre_path: Caminho do screenshot PRÉ-save (opcional)
            screenshot_pos_path: Caminho do screenshot PÓS-save (opcional)
            data_str: String de data (DDMMAAAA), se None usa data de hoje

        Returns:
            Dict com URLs dos arquivos uploaded
        """
        if data_str is None:
            data_str = datetime.now().strftime("%d%m%Y")

        resultado = {
            "sucesso": False,
            "url_json": None,
            "url_screenshot_pre": None,
            "url_screenshot_pos": None,
            "folder_url": None,
            "tentativas": 0,
            "erros": []
        }

        try:
            # 1. Verificar/criar pasta do dia (DDMMAAAA)
            folder_dia_id = self.verificar_criar_pasta(data_str, self.evidencias_folder_id)
            resultado["folder_url"] = f"https://drive.google.com/drive/folders/{folder_dia_id}"

            # 2. Upload JSON
            if os.path.exists(json_path):
                resultado["tentativas"] += 1
                json_upload = self.upload_arquivo(json_path, folder_dia_id)

                if json_upload:
                    resultado["url_json"] = json_upload['webViewLink']
                else:
                    resultado["erros"].append("Falha ao upload JSON")

            # 3. Upload screenshot PRÉ
            if screenshot_pre_path and os.path.exists(screenshot_pre_path):
                resultado["tentativas"] += 1
                pre_upload = self.upload_arquivo(screenshot_pre_path, folder_dia_id)

                if pre_upload:
                    resultado["url_screenshot_pre"] = pre_upload['webViewLink']
                else:
                    resultado["erros"].append("Falha ao upload screenshot PRÉ")

            # 4. Upload screenshot PÓS
            if screenshot_pos_path and os.path.exists(screenshot_pos_path):
                resultado["tentativas"] += 1
                pos_upload = self.upload_arquivo(screenshot_pos_path, folder_dia_id)

                if pos_upload:
                    resultado["url_screenshot_pos"] = pos_upload['webViewLink']
                else:
                    resultado["erros"].append("Falha ao upload screenshot PÓS")

            # Considerar sucesso se pelo menos JSON foi uploaded
            resultado["sucesso"] = resultado["url_json"] is not None

        except Exception as e:
            resultado["erros"].append(str(e))
            resultado["sucesso"] = False

        return resultado

    def adicionar_fila_retry(self, evidencia_info: Dict):
        """
        Adiciona evidência à fila de retry para tentar novamente depois.

        Args:
            evidencia_info: Dict com informações da evidência para retry
        """
        self.fila_retry.append({
            **evidencia_info,
            "timestamp_falha": datetime.now().isoformat()
        })

    def processar_fila_retry(self) -> List[Dict]:
        """
        Processa fila de retry de uploads pendentes.

        Returns:
            Lista de resultados dos uploads
        """
        resultados = []

        for item in self.fila_retry[:]:  # Copiar lista para poder remover durante iteração
            try:
                resultado = self.upload_evidencia_completa(
                    json_path=item.get("json_path"),
                    screenshot_pre_path=item.get("screenshot_pre_path"),
                    screenshot_pos_path=item.get("screenshot_pos_path"),
                    data_str=item.get("data_str")
                )

                resultados.append(resultado)

                # Se sucesso, remover da fila
                if resultado["sucesso"]:
                    self.fila_retry.remove(item)

            except Exception as e:
                resultados.append({
                    "sucesso": False,
                    "erros": [str(e)]
                })

        return resultados


# Exemplo de uso
if __name__ == "__main__":
    print("Testando DriveUploader...\n")

    # Criar uploader
    uploader = DriveUploader()

    print(f"Folder ID: {uploader.evidencias_folder_id}")
    print("\nNota: Para testar upload real, forneça caminhos de arquivos válidos.")
