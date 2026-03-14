from aiogram.fsm.state import State, StatesGroup

class Agent(StatesGroup):
    full_name = State()
    check = State()

class Client(StatesGroup):
    full_name = State()
    aloqa_number = State()
    obyekt_name = State()
    address = State()
    address_name = State()
    check = State()

class Naqd(StatesGroup):
    obyekt = State()
    # check
    address_need = State()
    product_type = State()
    product = State()
    miqdori = State()
    price = State()
    time = State()
    description = State()
    phone_number = State()
    address_full = State()
    address_lat = State()
    address_lon = State()
    address = State()
    status = State()



class Pri(StatesGroup):
    obyekt = State()
    # main
    address_need = State()
    tashkilot = State()
    product_type = State()
    product = State()
    miqdori = State()
    price = State()
    otkat = State()
    time = State()
    description = State()
    phone_number = State()
    address_full = State()
    address_lat = State()
    address_lon = State()
    address = State()
    status = State()

class Zakaz(StatesGroup):
    mijoz = State()
    obyekt = State()
    product = State()
    quantity = State()
    location = State()
    check = State()

class User(StatesGroup):
    full_name = State()



# test
class Product(StatesGroup):
    product_name = State()