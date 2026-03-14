from loader import disp
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message, ReplyKeyboardRemove
from account.models import data
from keyboards.reply_keyboard.start_keyboard import order, check
from aiogram.fsm.context import FSMContext
from states import Agent
from aiogram import F


@disp.message(CommandStart(), StateFilter("*"))
async def check_agent(message: Message, state: FSMContext):
    if message.chat.type != "private":
        await message.answer("Buyurtma berish uchun botga yozing 👉 @asad_beton_bot")
        return
    
    await state.clear()
    
    if await data.check_agent(message.from_user.id):
        await message.answer("Buyurtma berish uchun pastdagi tugmani bosing", reply_markup=order)
    else:
        await message.answer("Ism familyangizni kiriting")
        await state.set_state(Agent.full_name)


@disp.message(Agent.full_name)
async def check_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.title())

    await message.answer(f"Ma'lumot to'g'rimi?\n\n\n{message.text.title()}", reply_markup=check)

    await state.set_state(Agent.check)



@disp.message(Agent.check, F.text == "✅")
async def end_register(message: Message, state: FSMContext):
    datas = await state.get_data()
    full_name = datas['full_name']

    await data.add_agent(full_name, message.from_user.id)

    await message.answer("Muvafaqiyatli ro'yxatdan o'tdingiz")

    await message.answer("Buyurtma berish uchun pastdagi tugmani bosing", reply_markup=order)

    await state.clear()

@disp.message(Agent.check, F.text == "❌")
async def start_register(message: Message, state: FSMContext):
    await message.answer("Ism familyangizni kiriting", reply_markup=ReplyKeyboardRemove())

    await state.set_state(Agent.full_name)
