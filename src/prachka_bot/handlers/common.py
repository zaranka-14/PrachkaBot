from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from prachka_bot.services.google_sheets import is_admin

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "Здравствуйте! Это бот прачечной.\n\n"
        "Отправьте мне **вашу фамилию** или **номер телефона** "
        "в формате 8XXXXXXXXXX — и я скажу статус вашего белья."
    )

    if is_admin(message.from_user.id):
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Добавить заказ")],
                [KeyboardButton(text="️Изменить статус")]
            ],
            resize_keyboard=True,
            is_persistent=True
        )
        await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await message.answer(text, parse_mode="Markdown")


@router.message(Command("cancel"), F.text == "Отмена")
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Доброго времени суток! Отправьте /start для справки.")
        return
    await state.clear()
    await message.answer("Мы вернулись в начало. Чем я могу помочь?")
