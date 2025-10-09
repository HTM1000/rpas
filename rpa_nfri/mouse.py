import pyautogui
import time

print("🕒 Você tem 5 segundos para posicionar o mouse...")
time.sleep(5)

# Captura a posição do mouse
pos = pyautogui.position()
print(f"📍 Posição atual do mouse: {pos}")
