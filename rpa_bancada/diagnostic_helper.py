# -*- coding: utf-8 -*-
"""
Módulo de Diagnóstico para RPA Oracle
Ajuda a entender exatamente o que está sendo copiado e como processar
"""

import time
import json
import os
from pathlib import Path
from datetime import datetime
import hashlib
import pyperclip
import pandas as pd
from io import StringIO

# Diretório para logs de diagnóstico
DEBUG_DIR = Path("debug_logs")
DEBUG_DIR.mkdir(exist_ok=True)

class OracleDiagnostic:
    """Classe para diagnóstico e análise do clipboard Oracle"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback or print
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = DEBUG_DIR / self.session_id
        self.session_dir.mkdir(exist_ok=True)
        
    def log(self, msg):
        """Log com callback"""
        self.log_callback(f"[DIAG] {msg}")
        
    def save_raw_clipboard(self, text, prefix="clipboard"):
        """Salva o conteúdo bruto do clipboard para análise"""
        filename = self.session_dir / f"{prefix}_{datetime.now().strftime('%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)
        self.log(f"📝 Clipboard salvo em: {filename}")
        return filename
        
    def analyze_clipboard_content(self, text):
        """Analisa o conteúdo do clipboard e retorna diagnóstico"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "size_chars": len(text),
            "size_kb": len(text.encode('utf-8')) / 1024,
            "lines": text.count('\n'),
            "tabs": text.count('\t'),
            "empty_lines": len([l for l in text.split('\n') if not l.strip()]),
            "hash": hashlib.md5(text.encode()).hexdigest()[:8],
            "starts_with": text[:100] if text else "",
            "ends_with": text[-100:] if text else "",
            "has_headers": False,
            "detected_separator": None,
            "potential_columns": []
        }
        
        # Detectar separador
        if '\t' in text[:1000]:
            analysis["detected_separator"] = "TAB"
        elif '|' in text[:1000]:
            analysis["detected_separator"] = "PIPE"
        elif ';' in text[:1000]:
            analysis["detected_separator"] = "SEMICOLON"
        elif ',' in text[:1000]:
            analysis["detected_separator"] = "COMMA"
            
        # Tentar detectar cabeçalhos
        first_lines = text.split('\n')[:5]
        if first_lines:
            first_line = first_lines[0]
            if '\t' in first_line:
                potential_headers = first_line.split('\t')
                analysis["potential_columns"] = [h.strip() for h in potential_headers if h.strip()]
                analysis["has_headers"] = any('Org' in h or 'Item' in h or 'Sub' in h for h in potential_headers)
                
        # Salvar análise
        analysis_file = self.session_dir / f"analysis_{datetime.now().strftime('%H%M%S')}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
            
        self.log(f"📊 Análise salva: {analysis_file}")
        return analysis
        
    def monitor_clipboard_changes(self, max_duration=20*60, check_interval=2):
        """
        Monitora mudanças no clipboard por até max_duration segundos
        Detecta quando o Oracle termina de copiar verificando estabilidade
        """
        self.log(f"👀 Iniciando monitoramento do clipboard (máx {max_duration//60} minutos)")
        
        start_time = time.time()
        last_hash = ""
        last_size = 0
        stable_count = 0
        stable_threshold = 3  # Considera estável após 3 verificações sem mudança
        
        history = []
        
        while time.time() - start_time < max_duration:
            current_text = pyperclip.paste() or ""
            current_hash = hashlib.md5(current_text.encode()).hexdigest()
            current_size = len(current_text)
            
            # Registrar mudança
            if current_hash != last_hash:
                elapsed = time.time() - start_time
                self.log(f"📋 Mudança detectada: {current_size:,} chars (após {elapsed:.1f}s)")
                
                # Salvar snapshot se houver conteúdo significativo
                if current_size > 100:
                    self.save_raw_clipboard(current_text, f"snapshot_{int(elapsed)}")
                    
                history.append({
                    "time": elapsed,
                    "size": current_size,
                    "hash": current_hash[:8]
                })
                
                stable_count = 0
                last_hash = current_hash
                last_size = current_size
                
            else:
                stable_count += 1
                
                # Se estável e tem conteúdo significativo, considerar completo
                if stable_count >= stable_threshold and current_size > 100:
                    elapsed = time.time() - start_time
                    self.log(f"✅ Clipboard estável com {current_size:,} chars após {elapsed:.1f}s")
                    
                    # Salvar versão final
                    self.save_raw_clipboard(current_text, "final")
                    
                    # Salvar histórico
                    history_file = self.session_dir / "clipboard_history.json"
                    with open(history_file, 'w') as f:
                        json.dump(history, f, indent=2)
                        
                    return current_text, True
                    
            # Feedback a cada 30 segundos
            if int(time.time() - start_time) % 30 == 0:
                elapsed = time.time() - start_time
                self.log(f"⏳ Monitorando... {elapsed:.0f}s - Tamanho atual: {current_size:,} chars")
                
            time.sleep(check_interval)
            
        # Timeout atingido
        self.log(f"⏱️ Timeout de {max_duration//60} minutos atingido")
        final_text = pyperclip.paste() or ""
        if final_text:
            self.save_raw_clipboard(final_text, "timeout")
            
        return final_text, False
        
    def try_multiple_parsing_strategies(self, text):
        """
        Tenta múltiplas estratégias de parsing para garantir sucesso
        """
        results = []
        
        # Estratégia 1: TSV padrão
        try:
            df = pd.read_csv(StringIO(text), sep='\t', engine='python', on_bad_lines='skip')
            if not df.empty and df.shape[1] > 1:
                results.append(("TSV_STANDARD", df))
                self.log(f"✅ Estratégia TSV padrão: {df.shape}")
        except Exception as e:
            self.log(f"❌ TSV padrão falhou: {e}")
            
        # Estratégia 2: TSV com encoding diferente
        try:
            df = pd.read_csv(StringIO(text), sep='\t', encoding='latin1', engine='python', on_bad_lines='skip')
            if not df.empty and df.shape[1] > 1:
                results.append(("TSV_LATIN1", df))
                self.log(f"✅ Estratégia TSV Latin1: {df.shape}")
        except Exception as e:
            self.log(f"❌ TSV Latin1 falhou: {e}")
            
        # Estratégia 3: Detectar separador automaticamente
        for sep in ['\t', '|', ';', ',']:
            try:
                df = pd.read_csv(StringIO(text), sep=sep, engine='python', on_bad_lines='skip')
                if not df.empty and df.shape[1] > 3:  # Precisa ter pelo menos 4 colunas
                    results.append((f"SEP_{sep.replace('\t', 'TAB')}", df))
                    self.log(f"✅ Estratégia separador '{sep}': {df.shape}")
            except Exception:
                pass
                
        # Estratégia 4: Ignorar primeiras linhas problemáticas
        lines = text.split('\n')
        for skip in [1, 2, 3]:
            if len(lines) > skip:
                try:
                    text_skipped = '\n'.join(lines[skip:])
                    df = pd.read_csv(StringIO(text_skipped), sep='\t', engine='python', on_bad_lines='skip')
                    if not df.empty and df.shape[1] > 1:
                        results.append((f"SKIP_{skip}_LINES", df))
                        self.log(f"✅ Estratégia skip {skip} linhas: {df.shape}")
                except Exception:
                    pass
                    
        # Estratégia 5: Tentar com diferentes engines pandas
        try:
            df = pd.read_csv(StringIO(text), sep='\t', engine='c', low_memory=False, on_bad_lines='skip')
            if not df.empty and df.shape[1] > 1:
                results.append(("ENGINE_C", df))
                self.log(f"✅ Estratégia Engine C: {df.shape}")
        except Exception:
            pass
            
        # Salvar resultados de todas as estratégias
        strategies_file = self.session_dir / "parsing_strategies.txt"
        with open(strategies_file, 'w', encoding='utf-8') as f:
            f.write("RESULTADOS DAS ESTRATÉGIAS DE PARSING\n")
            f.write("="*50 + "\n\n")
            for strategy, df in results:
                f.write(f"Estratégia: {strategy}\n")
                f.write(f"Shape: {df.shape}\n")
                f.write(f"Colunas: {list(df.columns)}\n")
                f.write(f"Primeiras linhas:\n{df.head()}\n")
                f.write("-"*50 + "\n\n")
                
        return results
        
    def validate_dataframe(self, df):
        """
        Valida se o DataFrame tem as colunas esperadas do Oracle
        """
        expected_patterns = [
            'org', 'sub', 'endere', 'item', 'descri', 'rev', 'udm', 'estoque'
        ]
        
        columns_lower = [str(col).lower() for col in df.columns]
        matches = 0
        
        for pattern in expected_patterns:
            if any(pattern in col for col in columns_lower):
                matches += 1
                
        validity_score = matches / len(expected_patterns)
        
        validation = {
            "columns": list(df.columns),
            "shape": df.shape,
            "validity_score": validity_score,
            "is_valid": validity_score >= 0.5,
            "matched_patterns": matches,
            "expected_patterns": len(expected_patterns)
        }
        
        self.log(f"📈 Validação: Score {validity_score:.2%} - {'✅ VÁLIDO' if validation['is_valid'] else '❌ INVÁLIDO'}")
        
        return validation
        
    def create_diagnostic_report(self):
        """
        Cria relatório completo de diagnóstico
        """
        report_file = self.session_dir / "diagnostic_report.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write(f"RELATÓRIO DE DIAGNÓSTICO RPA ORACLE\n")
            f.write(f"Sessão: {self.session_id}\n")
            f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60 + "\n\n")
            
            # Listar todos os arquivos criados
            f.write("ARQUIVOS GERADOS:\n")
            for file in sorted(self.session_dir.glob("*")):
                f.write(f"  - {file.name} ({file.stat().st_size:,} bytes)\n")
                
            f.write("\n" + "="*60 + "\n")
            f.write("INSTRUÇÕES PARA ANÁLISE:\n")
            f.write("1. Verifique o arquivo 'final.txt' ou 'timeout.txt' para ver o conteúdo completo\n")
            f.write("2. Consulte 'analysis_*.json' para estatísticas do clipboard\n")
            f.write("3. Veja 'parsing_strategies.txt' para resultados de diferentes métodos de parsing\n")
            f.write("4. Use 'clipboard_history.json' para entender a evolução temporal\n")
            
        self.log(f"📑 Relatório de diagnóstico criado: {report_file}")
        return report_file