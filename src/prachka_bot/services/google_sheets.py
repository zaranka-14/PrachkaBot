import logging
import gspread
from google.oauth2.service_account import Credentials

from prachka_bot import config


logging.basicConfig(level=logging.INFO)


def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        config.CREDENTIALS_DICT, scopes=scopes
    )
    gc = gspread.authorize(creds)
    sh = gc.open(config.SPREADSHEET_NAME)
    return sh.worksheet(config.SHEET_NAME)


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS

def find_order(sheet, query: str):
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if str(row.get("ID", "")).strip() == query or \
           str(row.get("Телефон", "")).strip() == query:
            return i, row
    return None


def get_unfinished_orders(sheet):
    records = sheet.get_all_records()
    unfinished_orders = []

    for row in records:
        if str(row.get("Статус", "")).strip() != "Завершено":
            unfinished_orders.append(row)

    return unfinished_orders


def find_active_orders(sheet, query: str):
    records = sheet.get_all_records()
    active_orders = []

    for row in records:
        if str(row.get("ID", "")).strip() == query or \
                str(row.get("Телефон", "")).strip() == query:
            if str(row.get("Статус", "")).strip() != "Завершено":
                active_orders.append(row)

    return active_orders
