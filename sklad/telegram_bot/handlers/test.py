# from loader import disp
# from aiogram.filters import Command
# from aiogram.types import Message
# from account.models import data
# from aiogram.fsm.context import FSMContext
# from states import Product
# from aiogram import Router, F
# from aiogram.types import Message, CallbackQuery
# from aiogram.fsm.context import FSMContext
# from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
# from datetime import date

# @disp.message(Command('test'))
# async def add_product(message: Message, state: FSMContext):
#     await state.set_state(Product.product_name)
#     await message.answer("Mahsulot qo'shing")

# @disp.message(Product.product_name)
# async def confirm_product(message: Message, state: FSMContext):
#     await state.update_data(product_name=message.text.title())
#     datas = await state.get_data()
#     product_name = datas['product_name']
#     data.add_product(product_name)
#     await message.answer("Ma'lumot qo'shildi")
#     await state.clear()

# @disp.message(Command("date"))
# async def choose_date(message: Message):
#     await message.answer(
#         "📅 Sanani tanlang:",
#         reply_markup=await SimpleCalendar().start_calendar()
#     )

# @disp.callback_query(SimpleCalendarCallback.filter())
# async def process_calendar(
#     callback: CallbackQuery,
#     callback_data: SimpleCalendarCallback
# ):
#     calendar = SimpleCalendar()
#     selected, picked_date = await calendar.process_selection(
#         callback,
#         callback_data
#     )

#     # 🔥 KUN BOSILGANDA
#     if callback_data.act == "DAY" and picked_date:
#         await callback.message.answer(
#             f"✅ Tanlangan sana: {picked_date.strftime('%Y-%m-%d')}"
#         )

#     # 🔥 TODAY BOSILGANDA
#     elif callback_data.act == "TODAY":
#         today = date.today()
#         await callback.message.answer(
#             f"✅ Tanlangan sana: {today.strftime('%Y-%m-%d')}"
#         )

#     await callback.answer()
