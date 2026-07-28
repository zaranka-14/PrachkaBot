import os
import json

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("No BOT_TOKEN")

ADMIN_IDS = []
if admin_ids_str := os.getenv("ADMIN_IDS"):
    ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip()]

creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
if not creds_json:
    raise RuntimeError("No GOOGLE_CREDENTIALS_JSON")

CREDENTIALS_DICT = json.loads(creds_json)

SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "Prachka orders")
SHEET_NAME = os.getenv("SHEET_NAME", "Orders")

