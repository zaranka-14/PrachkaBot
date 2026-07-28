from aiogram.fsm.state import StatesGroup, State


class AddOrder(StatesGroup):
    waiting_phone = State()
    waiting_time = State()
    waiting_weight = State()
