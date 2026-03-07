# -*- coding: utf-8 -*-
"""
Monitor de Conexão com Internet - Circuit Breaker Pattern
==========================================================

Este módulo implementa verificação de conectividade com internet usando o pattern
Circuit Breaker para evitar pings excessivos e falsos positivos.

Pattern Circuit Breaker:
- FECHADO: Internet OK, pings funcionando normalmente
- ABERTO: Internet fora (3 falhas consecutivas), não faz mais pings
- MEIO_ABERTO: Testando reconexão após timeout

Autor: Claude Code
Data: 2026-01-06
"""

import socket
import time
import requests
from typing import Tuple, Dict


class InternetMonitor:
    """
    Monitor de internet com Circuit Breaker para prevenir pings excessivos.

    O circuit breaker evita que o RPA fique pingando infinitamente quando
    a internet está comprovadamente fora, reduzindo overhead e falsos positivos.
    """

    def __init__(self, url: str = "https://www.google.com", timeout: int = 5):
        """
        Inicializa o monitor de internet.

        Args:
            url: URL para fazer requisição HTTP (padrão: https://www.google.com)
            timeout: Timeout da requisição em segundos (padrão: 5)
        """
        self.url = url
        self.timeout = timeout

        # Circuit Breaker
        self.falhas_consecutivas = 0
        self.estado = "FECHADO"  # FECHADO, ABERTO, MEIO_ABERTO
        self.ultima_falha = None
        self.threshold_falhas = 3  # Número de falhas para abrir o circuit
        self.timeout_reabrir = 60  # Segundos para tentar reabrir circuit

    def verificar_internet(self) -> Tuple[bool, Dict]:
        """
        Verifica conectividade com internet usando Circuit Breaker.

        Returns:
            Tupla (ok: bool, detalhes: dict)
            - ok: True se internet está funcionando
            - detalhes: Dict com informações sobre a verificação
        """
        detalhes = {
            "internet_ok": False,
            "ping_ms": None,
            "erro": None,
            "circuit_estado": self.estado,
            "falhas_consecutivas": self.falhas_consecutivas
        }

        # Se circuit está ABERTO, não pinga (já sabemos que está fora)
        if self.estado == "ABERTO":
            # Verifica se passou o timeout para tentar reabrir
            if time.time() - self.ultima_falha > self.timeout_reabrir:
                self.estado = "MEIO_ABERTO"
                detalhes["circuit_estado"] = "MEIO_ABERTO"
            else:
                tempo_restante = int(self.timeout_reabrir - (time.time() - self.ultima_falha))
                detalhes["erro"] = f"Circuit breaker ABERTO - internet está fora (retry em {tempo_restante}s)"
                return False, detalhes

        # Tenta requisição HTTP real
        try:
            start = time.time()

            # Fazer requisição HTTP GET - igual quando busca dados do Sheets
            response = requests.get(self.url, timeout=self.timeout)

            ping_ms = (time.time() - start) * 1000

            # SUCESSO - verificar se conseguiu conectar (status 200-399)
            if response.status_code < 400:
                # SUCESSO - resetar circuit breaker
                self.falhas_consecutivas = 0
                self.estado = "FECHADO"
                detalhes["ping_ms"] = round(ping_ms, 2)
                detalhes["internet_ok"] = True
                detalhes["circuit_estado"] = "FECHADO"
                detalhes["status_code"] = response.status_code
                return True, detalhes
            else:
                detalhes["erro"] = f"HTTP {response.status_code} ao acessar {self.url}"
                return self._handle_falha(detalhes)

        except requests.exceptions.Timeout:
            detalhes["erro"] = f"Timeout ao conectar com {self.url}"
            return self._handle_falha(detalhes)

        except requests.exceptions.ConnectionError:
            detalhes["erro"] = f"Erro de conexão - sem acesso à internet"
            return self._handle_falha(detalhes)

        except requests.exceptions.RequestException as e:
            detalhes["erro"] = f"Erro inesperado: {str(e)}"
            return self._handle_falha(detalhes)

    def _handle_falha(self, detalhes: Dict) -> Tuple[bool, Dict]:
        """
        Incrementa falhas consecutivas e atualiza estado do circuit breaker.

        Args:
            detalhes: Dict com informações da verificação

        Returns:
            Tupla (False, detalhes atualizados)
        """
        self.falhas_consecutivas += 1

        if self.falhas_consecutivas >= self.threshold_falhas:
            self.estado = "ABERTO"
            self.ultima_falha = time.time()
            detalhes["erro"] = f"{detalhes['erro']} - Circuit breaker ABERTO após {self.threshold_falhas} falhas"

        detalhes["falhas_consecutivas"] = self.falhas_consecutivas
        detalhes["circuit_estado"] = self.estado
        return False, detalhes

    def resetar(self):
        """Reseta o circuit breaker para estado inicial (útil para testes)."""
        self.falhas_consecutivas = 0
        self.estado = "FECHADO"
        self.ultima_falha = None

    def get_estado(self) -> str:
        """Retorna o estado atual do circuit breaker."""
        return self.estado


# Exemplo de uso
if __name__ == "__main__":
    print("Testando InternetMonitor com Circuit Breaker...\n")

    monitor = InternetMonitor()

    for i in range(5):
        print(f"\n--- Tentativa {i+1} ---")
        ok, detalhes = monitor.verificar_internet()

        print(f"Internet OK: {ok}")
        print(f"Circuit Estado: {detalhes['circuit_estado']}")
        print(f"Falhas Consecutivas: {detalhes['falhas_consecutivas']}")

        if ok:
            print(f"Ping: {detalhes['ping_ms']}ms")
        else:
            print(f"Erro: {detalhes['erro']}")

        time.sleep(1)
