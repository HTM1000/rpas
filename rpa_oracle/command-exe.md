pyinstaller --onefile --windowed --icon=Logo.ico --add-data "CredenciaisOracle.json;." --add-data "qtd_negativa.png;." --add-data "ErroProduto.png;." --add-data "erroendereco.png;." --add-data "Tecumseh.png;." --add-data "Topo.png;." --add-data "Logo.png;." --hidden-import pyautogui --hidden-import mouseinfo --hidden-import PIL --hidden-import googleapiclient --hidden-import google.oauth2 --hidden-import google_auth_oauthlib --hidden-import cv2 --additional-hooks-dir=. RPA_Oracle.py


