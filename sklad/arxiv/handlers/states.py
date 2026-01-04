from aiogram.fsm.state import State, StatesGroup

class Haydovchi(StatesGroup):
    telefon_raqami = State()
    mashina_raqami = State()
    check = State()

class YolkiraNarxi(StatesGroup):
    zakaz_id = State()
    narxi = State()
    tasdiq = State()

class Mijoz(StatesGroup):
    telefon_raqam = State()
    tasdiq = State()

class MijozNarxi(StatesGroup):
    order_id = State()
    narxi = State()
    checked = State()