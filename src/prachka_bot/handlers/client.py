from aiogram import Router, types, F
from aiogram.filters import StateFilter
from prachka_bot.services.google_sheets import get_sheet, find_active_orders

router = Router()

@router.message(StateFilter(None), F.text)
async def check_order(message: types.Message):
    query = message.text.strip()

    if query.startswith('/'):
        return

    if not query.replace('-', '').replace(' ', '').isalnum():
        return

    try:
        sheet = get_sheet()
        active_orders = find_active_orders(sheet, query)
    except Exception:
        await message.answer(f"Ошибка чтения таблицы. Попробуйте позже или обратитесь за информацией в прачечную")
        return

    if not active_orders:
        await message.answer(
            "Заказ не найден или уже завершен. Проверьте фамилию или номер. Даже если заказа тут нет, он выполняется."
            "\nЕсли вы потерялись - нажмите /start")
        return

    order_texts = []
    for row in active_orders:
        text = (
            f"**Заказ №{row['ID']}**\n"
            f"📞 Заказчик: {row.get('Заказчик', '—')}\n"
            f"⏳ Дата завершения: {row.get('Дата завершения', '—')}\n"
            f"📋 Статус: **{row.get('Статус', '—')}**\n"
            f"📦 Примерный вес: {row.get('Вес', '—')} кг"
        )
        order_texts.append(text)

    final_message = "\n\n➖➖➖➖➖➖\n\n".join(order_texts)
    await message.answer(final_message, parse_mode="Markdown")
