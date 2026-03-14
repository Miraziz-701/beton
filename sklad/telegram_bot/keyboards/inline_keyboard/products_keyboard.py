from aiogram.utils.keyboard import InlineKeyboardBuilder
from account.models import data
from aiogram.types import InlineKeyboardButton


async def inline_xomashyos():
    keyboard = InlineKeyboardBuilder()
    products = await data.see_xomashyos()

    for product in products:
        keyboard.add(InlineKeyboardButton(
            text=product,
            callback_data=f"product:{product}"
        ))
    
    return keyboard.adjust(4).as_markup()


async def inline_products():
    keyboard = InlineKeyboardBuilder()
    products = await data.see_products()

    for product in products:
        keyboard.add(InlineKeyboardButton(
            text=product,
            callback_data=f"product:{product}"
        ))
    
    return keyboard.adjust(4).as_markup()

async def inline_naqd_obyekts(telegram_id):
    keyboard = InlineKeyboardBuilder()
    
    agent_id = await data.select_agent_id(telegram_id)
    
    obyekts = await data.see_naqd_obyekts(agent_id)

    for obyekt in obyekts:
        keyboard.add(InlineKeyboardButton(
            text=obyekt.obyekt_name,
            callback_data=f"naqd_obyekt:{obyekt.obyekt_name}"
        ))

    return keyboard.adjust(4).as_markup()

async def inline_pri_obyekts(telegram_id):
    keyboard = InlineKeyboardBuilder()
    
    agent_id = await data.select_agent_id(telegram_id)
    
    obyekts = await data.see_pri_obyekts(agent_id)

    for obyekt in obyekts:
        keyboard.add(InlineKeyboardButton(
            text=obyekt.obyekt_name,
            callback_data=f"pri_obyekt:{obyekt.obyekt_name}"
        ))

    return keyboard.adjust(4).as_markup()

