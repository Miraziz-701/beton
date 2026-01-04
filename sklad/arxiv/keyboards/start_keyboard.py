from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

choise_job = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Haydovchi"),
            KeyboardButton(text="Mijoz")
        ]
    ],
    resize_keyboard=True,
    is_persistent=True
)

send_contact = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Telefon raqamni jonatish", request_contact=True)
        ]
    ], 
    resize_keyboard=True,
    is_persistent=True
)

check_info = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="✅"),
            KeyboardButton(text="❌")
        ]
    ],
    resize_keyboard=True,
    is_persistent=True
)

end_yolkira = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Ha"),
            KeyboardButton(text="Yoq")
        ]
    ],
    resize_keyboard=True,
    is_persistent=True
)
