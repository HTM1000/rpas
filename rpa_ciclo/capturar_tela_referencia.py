# -*- coding: utf-8 -*-
"""
Capturar nova imagem de referencia da tela
"""

import tkinter as tk
from PIL import ImageGrab, ImageTk, Image
import cv2
import numpy as np

print("=" * 60)
print("CAPTURAR IMAGEM DE REFERENCIA")
print("=" * 60)
print("\nInstrucoes:")
print("1. Abra o Oracle na tela de Transferencia de Subinventario")
print("2. Pressione ENTER aqui quando estiver pronto")
print("3. Selecione a regiao na tela que deseja usar como referencia")
print("4. DICA: Selecione apenas partes ESTATICAS (sem data, hora, rodape)")
print("")

input("Pressione ENTER quando o Oracle estiver pronto...")

# Capturar tela
print("\nCapturando tela...")
screenshot = ImageGrab.grab()
screenshot_np = np.array(screenshot)

print(f"Tela capturada: {screenshot.width}x{screenshot.height} pixels")

# Salvar screenshot completo
screenshot.save("captura_completa.png")
print("Salvo: captura_completa.png")

# Criar janela para seleção
print("\nAbrindo janela de selecao...")
print("Instrucoes na janela:")
print("- Clique e arraste para selecionar a regiao")
print("- Solte para confirmar")

class SeletorRegiao:
    def __init__(self, img):
        self.root = tk.Tk()
        self.root.title("Selecione a Regiao de Referencia")

        # Redimensionar se necessário
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        scale = 1.0
        if img.width > screen_width or img.height > screen_height:
            scale = min(screen_width / img.width, screen_height / img.height) * 0.9

        self.scale = scale
        new_width = int(img.width * scale)
        new_height = int(img.height * scale)

        self.img_display = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.img_original = img

        self.canvas = tk.Canvas(self.root, width=new_width, height=new_height)
        self.canvas.pack()

        self.tk_img = ImageTk.PhotoImage(self.img_display)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)

        # Variaveis de selecao
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.regiao = None

        # Bindings
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Instruções
        label = tk.Label(self.root,
                        text="Clique e arraste para selecionar a regiao\n" +
                             "Escolha uma area ESTATICA (sem data/hora/rodape)",
                        bg="yellow", pady=10)
        label.pack()

        self.root.mainloop()

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y

        if self.rect:
            self.canvas.delete(self.rect)

    def on_drag(self, event):
        if self.rect:
            self.canvas.delete(self.rect)

        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            outline="red", width=3
        )

    def on_release(self, event):
        end_x = event.x
        end_y = event.y

        # Converter para coordenadas da imagem original
        x1 = int(min(self.start_x, end_x) / self.scale)
        y1 = int(min(self.start_y, end_y) / self.scale)
        x2 = int(max(self.start_x, end_x) / self.scale)
        y2 = int(max(self.start_y, end_y) / self.scale)

        # Garantir que está dentro dos limites
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(self.img_original.width, x2)
        y2 = min(self.img_original.height, y2)

        self.regiao = (x1, y1, x2, y2)

        print(f"\nRegiao selecionada: X={x1} Y={y1} ate X={x2} Y={y2}")
        print(f"Tamanho: {x2-x1}x{y2-y1} pixels")

        # Extrair e salvar
        regiao_img = self.img_original.crop((x1, y1, x2, y2))

        # Salvar na pasta informacoes
        output_path = "informacoes/tela_transferencia_subinventory.png"
        regiao_img.save(output_path)

        print(f"\nSalvo: {output_path}")
        print("\nImagem de referencia atualizada com sucesso!")

        self.root.quit()
        self.root.destroy()

# Executar seletor
seletor = SeletorRegiao(screenshot)

print("\n" + "=" * 60)
print("CONCLUIDO!")
print("=" * 60)
print("\nProximos passos:")
print("1. Teste o RPA novamente")
print("2. A validacao de tela deve funcionar agora")
print("")
