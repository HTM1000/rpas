# Verificar quais abas existem na planilha
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY"

creds = Credentials.from_authorized_user_file("token.json", SCOPES)
service = build("sheets", "v4", credentials=creds)

# Obter informações da planilha
sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
sheets = sheet_metadata.get('sheets', [])

print("\nAbas disponíveis na planilha:")
for sheet in sheets:
    title = sheet['properties']['title']
    sheet_id = sheet['properties']['sheetId']
    print(f"  - '{title}' (ID: {sheet_id})")
