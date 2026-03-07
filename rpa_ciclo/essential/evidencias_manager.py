# -*- coding: utf-8 -*-
"""
Gerenciador de Evidências - Evidence Management System
========================================================

Este módulo implementa o sistema completo de evidências com:
- Estrutura JSON detalhada para cada item processado
- Checksums SHA256 para integridade criptográfica
- Screenshots PRÉ e PÓS salvamento
- Metadata do sistema (usuário, máquina, versão)
- Organização por data (DDMMAAAA)

Autor: Claude Code
Data: 2026-01-06
"""

import json
import os
import hashlib
from datetime import datetime
from PIL import ImageGrab
from typing import Dict, Optional
import getpass
import socket
import platform
import tempfile
import shutil


class EvidenciasManager:
    """
    Gerenciador central de evidências do RPA Oracle.

    Cria evidências completas e auditáveis para cada item processado,
    com garantias criptográficas de integridade.
    """

    def __init__(
        self,
        base_path: str = "evidencias",
        versao_rpa: str = "Genesys 1.0",
        spreadsheet_id: str = "14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk",
        aba: str = "Ciclo Automacao"
    ):
        """
        Inicializa o gerenciador de evidências.

        Args:
            base_path: Caminho base para salvar evidências
            versao_rpa: Versão do RPA (para metadata)
            spreadsheet_id: ID da planilha Google Sheets
            aba: Nome da aba da planilha
        """
        # NÃO usar pasta local - evidências APENAS no Drive
        # Usar pasta temporária do sistema que será deletada após upload
        self.base_path = tempfile.mkdtemp(prefix="evidencias_")
        self.versao_rpa = versao_rpa
        self.spreadsheet_id = spreadsheet_id
        self.aba = aba

        # Data de hoje (formato DDMMAAAA)
        self.data_hoje = datetime.now().strftime("%d%m%Y")
        self.pasta_hoje = os.path.join(self.base_path, self.data_hoje)

        # Criar pasta temporária
        os.makedirs(self.pasta_hoje, exist_ok=True)

        # Metadata do sistema
        self.usuario_windows = self._get_usuario_windows()
        self.nome_maquina = self._get_nome_maquina()

    def _criar_pasta_se_necessario(self):
        """
        DESABILITADO: Evidências serão salvas APENAS no Google Drive.
        Não cria pasta local para economizar espaço.
        """
        # Pasta local desabilitada - evidências somente no Drive
        pass

    def _get_usuario_windows(self) -> str:
        """Retorna nome do usuário Windows logado."""
        try:
            return getpass.getuser()
        except:
            return "DESCONHECIDO"

    def _get_nome_maquina(self) -> str:
        """Retorna hostname da máquina."""
        try:
            return socket.gethostname()
        except:
            return "DESCONHECIDO"

    def _calcular_hash_arquivo(self, file_path: str) -> str:
        """
        Calcula SHA256 hash de um arquivo.

        Args:
            file_path: Caminho do arquivo

        Returns:
            Hash SHA256 em hexadecimal
        """
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Ler arquivo em chunks para economizar memória
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def _calcular_hash_json(self, data: Dict) -> str:
        """
        Calcula SHA256 hash de um dict JSON.

        Args:
            data: Dict para hash

        Returns:
            Hash SHA256 em hexadecimal
        """
        # Converter para JSON string (ordenado para consistência)
        json_string = json.dumps(data, sort_keys=True, ensure_ascii=False)

        # Calcular hash
        sha256_hash = hashlib.sha256(json_string.encode('utf-8'))
        return sha256_hash.hexdigest()

    def capturar_screenshot(
        self,
        item: str,
        quantidade: str,
        referencia: str,
        sufixo: str = "PRE"
    ) -> str:
        """
        Captura screenshot da tela e salva.

        Args:
            item: Código do item
            quantidade: Quantidade
            referencia: Referência/código transação
            sufixo: Sufixo do arquivo (PRE ou POS)

        Returns:
            Caminho do arquivo salvo
        """
        # Nome do arquivo
        nome_arquivo = f"{item}_{quantidade}_{referencia}_{sufixo}_save.png"
        caminho_completo = os.path.join(self.pasta_hoje, nome_arquivo)

        # Capturar screenshot
        screenshot = ImageGrab.grab()

        # Salvar
        screenshot.save(caminho_completo)

        return caminho_completo

    def criar_evidencia(
        self,
        # Dados do item
        item_data: Dict,
        # Verificações
        internet_detalhes: Dict,
        validacao_ocr: Dict,
        validacao_visual: Optional[Dict] = None,
        # Screenshots
        screenshot_pre_path: str = None,
        screenshot_pos_path: str = None,
        # Salvamento
        salvamento: Dict = None,
        # Status final
        status_final: str = "sucesso",
        # Drive
        drive_info: Dict = None
    ) -> str:
        """
        Cria evidência JSON completa para um item.

        Args:
            item_data: Dict com dados do item (item, qtd, ref, subs, etc)
            internet_detalhes: Dict com resultado de verificação de internet
            validacao_ocr: Dict com resultado de validação OCR
            validacao_visual: Dict com resultado de validação visual (opcional)
            screenshot_pre_path: Caminho do screenshot PRÉ-save
            screenshot_pos_path: Caminho do screenshot PÓS-save
            salvamento: Dict com detalhes do salvamento
            status_final: Status final do processamento
            drive_info: Dict com informações de upload para Drive

        Returns:
            Caminho do arquivo JSON criado
        """
        timestamp_fim = datetime.now().isoformat()

        # Calcular duração
        timestamp_inicio = item_data.get("timestamp_inicio", timestamp_fim)
        try:
            inicio_dt = datetime.fromisoformat(timestamp_inicio)
            fim_dt = datetime.fromisoformat(timestamp_fim)
            duracao_segundos = (fim_dt - inicio_dt).total_seconds()
        except:
            duracao_segundos = 0.0

        # Calcular hashes de screenshots
        hash_pre = None
        hash_pos = None

        if screenshot_pre_path and os.path.exists(screenshot_pre_path):
            hash_pre = self._calcular_hash_arquivo(screenshot_pre_path)

        if screenshot_pos_path and os.path.exists(screenshot_pos_path):
            hash_pos = self._calcular_hash_arquivo(screenshot_pos_path)

        # Estrutura completa da evidência
        evidencia = {
            "metadata": {
                "versao_rpa": self.versao_rpa,
                "usuario_windows": self.usuario_windows,
                "nome_maquina": self.nome_maquina,
                "plataforma": platform.system(),
                "timestamp_inicio": timestamp_inicio,
                "timestamp_fim": timestamp_fim,
                "duracao_segundos": round(duracao_segundos, 2)
            },

            "planilha_origem": {
                "spreadsheet_id": self.spreadsheet_id,
                "aba": self.aba,
                "numero_linha": item_data.get("numero_linha"),
                "id_linha": item_data.get("id_linha")
            },

            "item_dados": {
                "item": item_data.get("item"),
                "quantidade": item_data.get("quantidade"),
                "referencia": item_data.get("referencia"),
                "sub_origem": item_data.get("sub_origem"),
                "end_origem": item_data.get("end_origem"),
                "sub_destino": item_data.get("sub_destino"),
                "end_destino": item_data.get("end_destino"),
                "tipo_transacao": item_data.get("tipo_transacao")
            },

            "verificacoes": {
                "internet": internet_detalhes if internet_detalhes else {},
                "validacao_ocr": validacao_ocr if validacao_ocr else {},
                "validacao_visual": validacao_visual if validacao_visual else {
                    "executada": False,
                    "motivo": "Não habilitada"
                }
            },

            "screenshots": {
                "pre_save": {
                    "caminho": os.path.basename(screenshot_pre_path) if screenshot_pre_path else None,
                    "timestamp": item_data.get("timestamp_screenshot_pre"),
                    "hash_sha256": hash_pre
                },
                "pos_save": {
                    "caminho": os.path.basename(screenshot_pos_path) if screenshot_pos_path else None,
                    "timestamp": item_data.get("timestamp_screenshot_pos"),
                    "hash_sha256": hash_pos
                }
            },

            "salvamento": salvamento if salvamento else {
                "executado": False
            },

            "status_final": status_final,

            "drive": drive_info if drive_info else {
                "uploaded": False,
                "url_json": None,
                "url_screenshot_pre": None,
                "url_screenshot_pos": None,
                "tentativas_upload": 0,
                "ultimo_erro": None
            },

            "cache_status": item_data.get("cache_status", {})
        }

        # Calcular hash da evidência
        evidencia["integridade"] = {
            "json_hash_sha256": self._calcular_hash_json(evidencia),
            "assinado_em": timestamp_fim
        }

        # Nome do arquivo JSON
        nome_arquivo = f"{item_data.get('item')}_{item_data.get('quantidade')}_{item_data.get('referencia')}.json"
        caminho_json = os.path.join(self.pasta_hoje, nome_arquivo)

        # Salvar JSON
        with open(caminho_json, 'w', encoding='utf-8') as f:
            json.dump(evidencia, f, indent=2, ensure_ascii=False)

        return caminho_json

    def criar_evidencia_erro(
        self,
        item_data: Dict,
        tipo_erro: str,
        detalhes_erro: Dict,
        screenshot_path: str = None
    ) -> str:
        """
        Cria evidência de erro (internet, validação visual, etc).

        Args:
            item_data: Dados do item (se disponível)
            tipo_erro: Tipo do erro (INTERNET, VALIDACAO_VISUAL, etc)
            detalhes_erro: Detalhes específicos do erro
            screenshot_path: Screenshot do erro (opcional)

        Returns:
            Caminho do arquivo JSON criado
        """
        timestamp = datetime.now().isoformat()

        # Hash do screenshot (se existir)
        hash_screenshot = None
        if screenshot_path and os.path.exists(screenshot_path):
            hash_screenshot = self._calcular_hash_arquivo(screenshot_path)

        evidencia_erro = {
            "metadata": {
                "versao_rpa": self.versao_rpa,
                "usuario_windows": self.usuario_windows,
                "nome_maquina": self.nome_maquina,
                "timestamp": timestamp,
                "tipo_evidencia": "ERRO"
            },

            "tipo_erro": tipo_erro,

            "item_dados": item_data if item_data else {"info": "Item não disponível"},

            "detalhes_erro": detalhes_erro,

            "screenshot_erro": {
                "caminho": os.path.basename(screenshot_path) if screenshot_path else None,
                "hash_sha256": hash_screenshot
            },

            "status_final": "erro"
        }

        # Hash da evidência
        evidencia_erro["integridade"] = {
            "json_hash_sha256": self._calcular_hash_json(evidencia_erro),
            "assinado_em": timestamp
        }

        # Nome do arquivo (usa timestamp para evitar conflitos)
        nome_arquivo = f"erro_{tipo_erro}_{timestamp.replace(':', '-').replace('.', '-')}.json"
        caminho_json = os.path.join(self.pasta_hoje, nome_arquivo)

        # Salvar JSON
        with open(caminho_json, 'w', encoding='utf-8') as f:
            json.dump(evidencia_erro, f, indent=2, ensure_ascii=False)

        return caminho_json

    def atualizar_evidencia_drive(
        self,
        evidencia_path: str,
        drive_urls: Dict
    ):
        """
        Atualiza evidência JSON com URLs do Google Drive.

        Args:
            evidencia_path: Caminho do arquivo JSON
            drive_urls: Dict com URLs do Drive (url_json, url_screenshot_pre, etc)
        """
        # Carregar evidência existente
        with open(evidencia_path, 'r', encoding='utf-8') as f:
            evidencia = json.load(f)

        # Atualizar seção Drive
        evidencia["drive"].update(drive_urls)
        evidencia["drive"]["uploaded"] = True
        evidencia["drive"]["upload_timestamp"] = datetime.now().isoformat()

        # Recalcular hash
        evidencia["integridade"]["json_hash_sha256"] = self._calcular_hash_json(evidencia)

        # Salvar atualizado
        with open(evidencia_path, 'w', encoding='utf-8') as f:
            json.dump(evidencia, f, indent=2, ensure_ascii=False)

    def limpar_arquivo_temporario(self, caminho_arquivo: str):
        """
        Remove arquivo temporário após upload bem-sucedido.

        Args:
            caminho_arquivo: Caminho do arquivo a deletar
        """
        try:
            if os.path.exists(caminho_arquivo):
                os.remove(caminho_arquivo)
        except Exception as e:
            # Não falhar se não conseguir deletar
            pass

    def limpar_pasta_temporaria(self):
        """
        Remove toda a pasta temporária de evidências.
        Chamar após todos os uploads estarem completos.
        """
        try:
            if os.path.exists(self.base_path):
                shutil.rmtree(self.base_path)
        except Exception as e:
            # Não falhar se não conseguir deletar
            pass


# Exemplo de uso
if __name__ == "__main__":
    print("Testando EvidenciasManager...\n")

    manager = EvidenciasManager()

    print(f"Pasta de evidências: {manager.pasta_hoje}")
    print(f"Usuário: {manager.usuario_windows}")
    print(f"Máquina: {manager.nome_maquina}")
    print(f"Versão RPA: {manager.versao_rpa}")
