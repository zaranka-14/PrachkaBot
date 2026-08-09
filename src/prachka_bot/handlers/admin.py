from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

from prachka_bot.services.google_sheets import is_admin, get_sheet, get_unfinished_orders
from prachka_bot.states import AddOrder

router = Router()

# ---------------------------------- ADD -----------------------------------------------------

@router.callback_query(F.text == "Добавить заказ")
async def admin_add(callback: types.CallbackQuery, state: FSMContext):

    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав администратора.", show_alert=True)
        return

    await callback.message.answer("Введите телефон или фамилию клиента:")
    await state.set_state(AddOrder.waiting_phone)
    await callback.answer()


@router.message(AddOrder.waiting_phone)
async def add_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    await state.update_data(phone=phone)
    await message.answer("Сколько примерно весит белье (кг)?")
    await state.set_state(AddOrder.waiting_weight)


@router.message(AddOrder.waiting_weight)
async def add_phone(message: types.Message, state: FSMContext):
    weight = message.text.strip()
    if not weight.isdigit():
        await message.answer("Неверный формат. Введите число (вес белья)")
        return
    await state.update_data(weight=weight)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Сегодня", callback_data="time_today"),
            InlineKeyboardButton(text="Завтра", callback_data="time_tomorrow"),
            InlineKeyboardButton(text="Послезавтра", callback_data="time_afterTomorrow"),
        ],
        [
            InlineKeyboardButton(text="Через 2 дня", callback_data="time_2days"),
        ],
        [
            InlineKeyboardButton(text="Через 3 дня", callback_data="time_3days"),
        ],
        [
            InlineKeyboardButton(text="Другое время (введите вручную)", callback_data="time_custom"),
        ]
    ])

    await message.answer("Когда заказ будет готов?", reply_markup=keyboard)
    await state.set_state(AddOrder.waiting_time)


@router.callback_query(AddOrder.waiting_time, F.data.startswith("time_"))
async def process_time_selection(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    time_choice = callback.data.split("_")[1]

    time_mapping = {
        "today": datetime.now().strftime("%d.%m.%Y"),
        "tomorrow": (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y"),
        "afterTomorrow": (datetime.now() + timedelta(days=2)).strftime("%d.%m.%Y"),
        "2days": (datetime.now() + timedelta(days=3)).strftime("%d.%m.%Y"),
        "3days": (datetime.now() + timedelta(days=4)).strftime("%d.%m.%Y"),
        "custom": None
    }

    if time_choice == "custom":
        await callback.message.answer("Введите дату готовности в формате ДД.ММ.ГГГГ (например 01.12.2026):")
        await callback.answer()
        return

    ready_time = time_mapping[time_choice]

    try:
        sheet = get_sheet()
        records = get_unfinished_orders(sheet)
        new_id = max([int(r["ID"]) for r in records], default=0) + 1
        sheet.append_row([new_id, data["phone"], "Принят", datetime.now().strftime("%d.%m.%Y"), ready_time, data["weight"]])
        await callback.message.answer(
            f"✅ Заказ №{new_id} добавлен."
            f"\nЗаказчик: {data['phone']}"
            f"\nСтатус: Принят"
            f"\nГотовность: {ready_time}"
            f"\nВес: {data['weight']}")

    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")

    await state.clear()
    await callback.answer()


@router.message(AddOrder.waiting_time)
async def add_custom_time(message: types.Message, state: FSMContext):
    data = await state.get_data()
    ready_time = message.text.strip()

    try:
        sheet = get_sheet()
        records = get_unfinished_orders(sheet)
        new_id = max([int(r["ID"]) for r in records], default=0) + 1
        sheet.append_row([new_id, data["phone"], "Принят", datetime.now().strftime("%d.%m.%Y"), ready_time, data["weight"]])
        await message.answer(f"✅ Заказ №{new_id} добавлен."
                             f"\nЗаказчик: {data['phone']}"
                             f"\nСтатус: Принят"
                             f"\nГотовность: {ready_time}"
                             f"\nВес: {data['weight']}")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

    await state.clear()

# ---------------------------------- CHANGE --------------------------------------------------

@router.callback_query(F.text == "Изменить статус")
async def admin_change(callback: types.CallbackQuery):

    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав администратора.", show_alert=True)
        return

    try:
        sheet = get_sheet()
        records = get_unfinished_orders(sheet)
    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")
        await callback.answer()
        return

    if not records:
        await callback.message.answer("Заказов пока нет.")
        await callback.answer()
        return

    keyboard_buttons = []
    for r in records:

        phone = str(r.get('Заказчик', ''))
        if len(phone) > 7:
            phone = phone[:4] + '...' + phone[-3:]

        btn_text = f"№{r['ID']} | {phone} | {r.get('Статус', '—')}"
        if len(btn_text) > 60:
            btn_text = btn_text[:57] + "..."

        keyboard_buttons.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"change_{r['ID']}")
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.answer(
        "Выберите заказ для изменения статуса:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("change_"))
async def process_order_selection(callback: types.CallbackQuery, state: FSMContext):
    order_id = callback.data.split("_")[1]

    await state.update_data(order_id=order_id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🟡 Частично готово", callback_data=f"status_{order_id}_partiallyReady"),
        ],
        [
            InlineKeyboardButton(text="🟢 Готово", callback_data=f"status_{order_id}_ready"),
            InlineKeyboardButton(text="✅ Завершено", callback_data=f"status_{order_id}_completed"),
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"),
        ]
    ])

    await callback.message.answer(
        f"Выберите новый статус для заказа №{order_id}:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("status_"))
async def process_status_change(callback: types.CallbackQuery):
    parts = callback.data.split("_", 2)
    if len(parts) != 3:
        await callback.message.answer("Ошибка: неверный формат данных.")
        await callback.answer()
        return

    order_id = parts[1]
    status_choice = parts[2]

    status_mapping = {
        "partiallyReady": "Частично готово",
        "ready": "Готово",
        "completed": "Завершено"
    }

    new_status = status_mapping[status_choice]

    try:
        sheet = get_sheet()
        records = get_unfinished_orders(sheet)

        updated = False
        for i, row in enumerate(records, start=2):
            if str(row.get("ID", "")).strip() == order_id:
                sheet.update_cell(i, 3, new_status)
                updated = True
                break

        if updated:
            await callback.message.answer(
                f"✅ Статус заказа №{order_id} изменён на «{new_status}».")
        else:
            await callback.message.answer(f"❌ Заказ №{order_id} не найден.")
    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")

    await callback.answer()
