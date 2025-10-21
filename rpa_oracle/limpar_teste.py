import os

arquivos = ["cache_teste.json", "dados_processados.xlsx", "teste_log.txt"]

for arquivo in arquivos:
    if os.path.exists(arquivo):
        os.remove(arquivo)
        print(f"Removido: {arquivo}")
    else:
        print(f"Não existe: {arquivo}")

print("\nArquivos de teste limpos!")
