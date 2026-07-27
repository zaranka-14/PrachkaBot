import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import gspread
from google.oauth2.service_account import Credentials

import config

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


class AddOrder(StatesGroup):
    waiting_phone = State()
    waiting_name = State()


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS

def find_order(sheet, query: str):
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if str(row.get("ID", "")).strip() == query or \
           str(row.get("Телефон", "")).strip() == query:
            return i, row
    return None

dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "Здравствуйте! Это бот прачечной.\n\n"
        "Отправьте мне **номер заказа** (из чека) или **номер телефона** "
        "в формате 8XXXXXXXXXX — и я скажу статус вашего белья."
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text.regexp(r"^(\d{10,}|[A-Za-z0-9\-]+)$"))
async def check_order(message: types.Message):
    query = message.text.strip()
    try:
        sheet = get_sheet()
        result = find_order(sheet, query)
    except Exception as e:
        await message.answer(f"Ошибка чтения таблицы: {e}. Попробуйте позже или обратитесь за информацией в прачечную")
        return

    if result is None:
        await message.answer("Заказ не найден. Проверьте номер. Даже если его тут нет, он выполняется.")
        return

    row_num, row = result
    text = (
        f"Заказ №{row['ID']}\n"
        f"Телефон: {row.get('Телефон', '—')}\n"
        f"Статус: **{row.get('Статус', '—')}**"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message()
async def fallback(message: types.Message):
    await message.answer("Отправьте номер заказа или телефона.")


@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    try:
        sheet = get_sheet()
        records = sheet.get_all_records()
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
        return

    if not records:
        await message.answer("Заказов пока нет.")
        return

    lines = ["*Список заказов:*\n"]
    for r in records[-15:]:
        lines.append(
            f"• №{r['ID']} | "
            f"{r.get('Телефон','')} | *{r.get('Статус','')}*"
        )
    lines.append("\nКоманды:\n/add — добавить заказ\n/status <ID> <статус> — изменить")
    await message.answer("\n".join(lines), parse_mode="Markdown")

@dp.message(Command("add"))
async def cmd_add(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Введите телефон клиента (10 цифр):")
    await state.set_state(AddOrder.waiting_phone)

@dp.message(AddOrder.waiting_phone)
async def add_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    await message.answer("Введите имя клиента:")
    await state.set_state(AddOrder.waiting_name)

@dp.message(AddOrder.waiting_name)
async def add_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = message.text.strip()
    try:
        sheet = get_sheet()
        records = sheet.get_all_records()
        new_id = max([int(r["ID"]) for r in records], default=0) + 1
        sheet.append_row([new_id, data["phone"], name, "Принят"])
        await message.answer(f"Заказ №{new_id} добавлен.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
    await state.clear()

@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) != 3:
        await message.answer("Использование: /status <ID> <новый статус>")
        return
    _, order_id, new_status = parts
    try:
        sheet = get_sheet()
        result = find_order(sheet, order_id)
        if result is None:
            await message.answer("Заказ не найден.")
            return
        row_num, _ = result
        sheet.update_cell(row_num, 4, new_status)
        await message.answer(f"Статус заказа №{order_id} изменён на «{new_status}».")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


async def main():
    bot = Bot(token=config.BOT_TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())