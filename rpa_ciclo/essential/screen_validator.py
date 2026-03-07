# -*- coding: utf-8 -*-
"""
Validador Visual Comparativo - Screen Validation
==================================================

Este módulo implementa validação visual comparativa usando OpenCV para detectar
se o Oracle modificou campos após Ctrl+S (bugs do Oracle ou comportamento inesperado).

Validação Comparativa:
- Captura screenshot PRÉ-save (antes de Ctrl+S)
- Captura screenshot PÓS-save (depois de Ctrl+S)
- Compara campos específicos usando OCR
- Detecta se algum campo foi modificado pelo Oracle

Autor: Claude Code
Data: 2026-01-06
"""

import cv2
import numpy as np
from PIL import Image, ImageGrab
import pytesseract
from typing import Tuple, Dict, List
import os


class ScreenValidator:
    """
    Validador visual comparativo para detectar mudanças em campos do Oracle.

    Compara screenshots PRÉ e PÓS salvamento para garantir que o Oracle
    não modificou nenhum campo inesperadamente.
    """

    def __init__(self, coords_campos: Dict):
        """
        Inicializa o validador visual.

        Args:
            coords_campos: Dict com coordenadas dos campos a validar
                          Exemplo: {"campo_item": (x, y, w, h), ...}
        """
        self.coords_campos = coords_campos

        # Configuração do Tesseract
        # Tenta usar Tesseract local (para executável) ou sistema
        tesseract_local = os.path.join(os.path.dirname(__file__), "tesseract", "tesseract.exe")
        if os.path.exists(tesseract_local):
            pytesseract.pytesseract.tesseract_cmd = tesseract_local
        elif os.path.exists(r"C:\Program Files\Tesseract-OCR\tesseract.exe"):
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    def capturar_screenshot(self) -> np.ndarray:
        """
        Captura screenshot da tela completa.

        Returns:
            Screenshot como array NumPy (BGR)
        """
        screenshot_pil = ImageGrab.grab()
        screenshot_np = np.array(screenshot_pil)
        # Convert RGB to BGR (OpenCV usa BGR)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        return screenshot_bgr

    def extrair_texto_campo(self, screenshot: np.ndarray, coords: Tuple) -> str:
        """
        Extrai texto de um campo específico usando OCR.

        Args:
            screenshot: Screenshot como array NumPy
            coords: Tupla (x, y, width, height) do campo

        Returns:
            Texto extraído do campo (limpo)
        """
        x, y, w, h = coords

        # Recortar região do campo
        campo_img = screenshot[y:y+h, x:x+w]

        # Pré-processamento para melhorar OCR
        # Converter para escala de cinza
        campo_gray = cv2.cvtColor(campo_img, cv2.COLOR_BGR2GRAY)

        # Binarização (threshold)
        _, campo_bin = cv2.threshold(campo_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # OCR
        config_tesseract = '--psm 7 --oem 3'  # PSM 7 = linha única
        texto = pytesseract.image_to_string(campo_bin, config=config_tesseract)

        # Limpar texto (remover espaços extras, quebras de linha)
        texto_limpo = texto.strip().replace('\n', '').replace('\r', '')

        return texto_limpo

    def comparar_screenshots(
        self,
        screenshot_pre: np.ndarray,
        screenshot_pos: np.ndarray,
        campos_para_comparar: List[str] = None
    ) -> Tuple[bool, List[Dict]]:
        """
        Compara dois screenshots campo a campo.

        Args:
            screenshot_pre: Screenshot antes de Ctrl+S
            screenshot_pos: Screenshot depois de Ctrl+S
            campos_para_comparar: Lista de campos para comparar (None = todos)

        Returns:
            Tupla (campos_iguais: bool, diferencas: List[Dict])
            - campos_iguais: True se todos os campos são iguais
            - diferencas: Lista de dicts com campos que mudaram
        """
        if campos_para_comparar is None:
            campos_para_comparar = list(self.coords_campos.keys())

        diferencas = []

        for nome_campo in campos_para_comparar:
            if nome_campo not in self.coords_campos:
                continue

            coords = self.coords_campos[nome_campo]

            # Extrair texto PRÉ e PÓS
            texto_pre = self.extrair_texto_campo(screenshot_pre, coords)
            texto_pos = self.extrair_texto_campo(screenshot_pos, coords)

            # Comparar
            if texto_pre != texto_pos:
                diferencas.append({
                    "campo": nome_campo,
                    "valor_pre": texto_pre,
                    "valor_pos": texto_pos,
                    "coordenadas": coords
                })

        campos_iguais = len(diferencas) == 0
        return campos_iguais, diferencas

    def gerar_diff_image(
        self,
        screenshot_pre: np.ndarray,
        screenshot_pos: np.ndarray,
        diferencas: List[Dict],
        output_path: str
    ):
        """
        Gera imagem visual mostrando diferenças entre PRÉ e PÓS.

        Args:
            screenshot_pre: Screenshot antes de Ctrl+S
            screenshot_pos: Screenshot depois de Ctrl+S
            diferencas: Lista de diferenças detectadas
            output_path: Caminho para salvar a imagem de diferenças
        """
        # Criar imagem lado a lado
        height = max(screenshot_pre.shape[0], screenshot_pos.shape[0])
        width_total = screenshot_pre.shape[1] + screenshot_pos.shape[1]

        diff_image = np.zeros((height, width_total, 3), dtype=np.uint8)
        diff_image[:screenshot_pre.shape[0], :screenshot_pre.shape[1]] = screenshot_pre
        diff_image[:screenshot_pos.shape[0], screenshot_pre.shape[1]:] = screenshot_pos

        # Marcar campos com diferenças
        for diff in diferencas:
            x, y, w, h = diff["coordenadas"]

            # Retângulo vermelho no PRÉ
            cv2.rectangle(diff_image, (x, y), (x+w, y+h), (0, 0, 255), 2)
            cv2.putText(
                diff_image,
                f"PRE: {diff['valor_pre'][:20]}",
                (x, y-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                1
            )

            # Retângulo vermelho no PÓS (offset pelo width da primeira imagem)
            x_pos = x + screenshot_pre.shape[1]
            cv2.rectangle(diff_image, (x_pos, y), (x_pos+w, y+h), (0, 0, 255), 2)
            cv2.putText(
                diff_image,
                f"POS: {diff['valor_pos'][:20]}",
                (x_pos, y-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                1
            )

        # Salvar imagem
        cv2.imwrite(output_path, diff_image)

    def validar_comparativo(
        self,
        screenshot_pre_path: str,
        screenshot_pos_path: str,
        campos: List[str] = None
    ) -> Tuple[bool, List[Dict]]:
        """
        Valida comparativamente dois screenshots salvos.

        Args:
            screenshot_pre_path: Caminho do screenshot PRÉ-save
            screenshot_pos_path: Caminho do screenshot PÓS-save
            campos: Campos para comparar (None = todos)

        Returns:
            Tupla (ok: bool, diferencas: List[Dict])
        """
        # Carregar screenshots
        screenshot_pre = cv2.imread(screenshot_pre_path)
        screenshot_pos = cv2.imread(screenshot_pos_path)

        if screenshot_pre is None or screenshot_pos is None:
            raise FileNotFoundError("Screenshots não encontrados")

        # Comparar
        campos_iguais, diferencas = self.comparar_screenshots(
            screenshot_pre,
            screenshot_pos,
            campos
        )

        return campos_iguais, diferencas


# Exemplo de uso
if __name__ == "__main__":
    print("Testando ScreenValidator...\n")

    # Coordenadas de exemplo (ajustar conforme o Oracle real)
    coords_exemplo = {
        "campo_item": (67, 155, 118, 22),
        "campo_quantidade": (639, 155, 89, 22),
        "campo_referencia": (737, 155, 100, 22)
    }

    validator = ScreenValidator(coords_exemplo)

    # Capturar screenshot atual
    screenshot_atual = validator.capturar_screenshot()
    print(f"Screenshot capturado: {screenshot_atual.shape}")

    # Extrair texto de um campo
    texto_item = validator.extrair_texto_campo(
        screenshot_atual,
        coords_exemplo["campo_item"]
    )
    print(f"Texto do campo 'item': {texto_item}")
