from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


order_type = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Naqd pul'),
            KeyboardButton(text="Pul ko'chirish")
        ]
    ],

    resize_keyboard=True,
    is_persistent=True
)

order = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='🛒 Buyurtma berish')
        ]
    ], 
    
    resize_keyboard=True,
    is_persistent=True
)

check = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='✅'),
            KeyboardButton(text='❌')
        ]
    ],

    resize_keyboard=True,
    is_persistent=True
)

check_obyekt = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='📍 Mavjud obyektlar'),
            KeyboardButton(text="➕ Obyekt qo'shish")
        ]
    ],

    resize_keyboard=True,
    is_persistent=True
)

check_obyekt_tash = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='🏢 Mavjud obyektlar'),
            KeyboardButton(text="📝 Obyekt qo'shish")
        ]
    ],

    resize_keyboard=True,
    is_persistent=True
)