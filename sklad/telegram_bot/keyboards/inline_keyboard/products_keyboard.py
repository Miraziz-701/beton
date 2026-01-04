from aiogram.utils.keyboard import InlineKeyboardBuilder
from account.models import data
from aiogram.types import InlineKeyboardButton


async def inline_products():
    keyboard = InlineKeyboardBuilder()
    products = await data.see_products()

    for product in products:
        keyboard.add(InlineKeyboardButton(
            text=product,
            callback_data=f"product:{product}"
        ))
    
    return keyboard.adjust(4).as_markup()

async def inline_naqd_obyekts():
    keyboard = InlineKeyboardBuilder()
    obyekts = await data.see_naqd_obyekts()

    for obyekt in obyekts:
        keyboard.add(InlineKeyboardButton(
            text=obyekt,
            callback_data=f"naqd_obyekt:{obyekt}"
        ))

    return keyboard.adjust(4).as_markup()

async def inline_pri_obyekts():
    keyboard = InlineKeyboardBuilder()
    obyekts = await data.see_pri_obyekts()

    for obyekt in obyekts:
        keyboard.add(InlineKeyboardButton(
            text=obyekt,
            callback_data=f"pri_obyekt:{obyekt}"
        ))

    return keyboard.adjust(4).as_markup()

