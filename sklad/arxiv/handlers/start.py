from aiogram import Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from keyboards.start_keyboard import choise_job, send_contact, check_info, end_yolkira
from aiogram.fsm.context import FSMContext
from handlers.states import Haydovchi, YolkiraNarxi, Mijoz, MijozNarxi
import re
from handlers.db import save_haydovchi, save_yolkira_narxi, save_mijoz, get_all_info, save_mijoz_narxi


disp = Dispatcher()
PATTERN1 = re.compile(r"^\d{2}[A-Z]\d{3}[A-Z]{2}$")   # 01A234BC
PATTERN2 = re.compile(r"^\d{2}\d{3}[A-Z]{3}$")        # 01234ABC


@disp.message(CommandStart())
async def start(message: Message):
    await message.answer("Iltimos bu ikkita roldan birini tanlang", reply_markup=choise_job)

@disp.message(F.text == "Haydovchi")
async def haydovchi_registaration_start(message: Message, state: FSMContext):
    await state.set_state(Haydovchi.telefon_raqami)
    await message.delete()
    await message.answer("Telefon raqamni jo'natish", reply_markup=send_contact)

@disp.message(Haydovchi.telefon_raqami)
async def haydovchi_registaration_continue(message: Message, state: FSMContext):
    await state.update_data(telefon_raqami = message.contact.phone_number)
    await state.set_state(Haydovchi.mashina_raqami)
    await message.delete()
    await message.answer("Mashina raqamini kiriting", reply_markup=ReplyKeyboardRemove())

@disp.message(Haydovchi.mashina_raqami)
async def haydovchi_registaration_end(message: Message, state: FSMContext):
    s = (message.text or "").replace(" ", "").upper()
    if PATTERN1.match(s):
        s_formatted = f"{s[0:2]} {s[2]} {s[3:6]} {s[6:8]}"
    elif PATTERN2.match(s):
        s_formatted = f"{s[0:2]} {s[2:5]} {s[5:8]}"
    else:
        await message.answer(
            "❌ Xato format!\nMisollar:\n• 01 O 001 OO\n• 01 001 OOO\n\nBoshqatan kiriting"
        )
        return
    await message.delete()
    await state.update_data(mashina_raqami=s_formatted)
    data = await state.get_data()
    phone_number = data["telefon_raqami"]
    await message.answer(f"Telefon raqam: {phone_number}\nMashina raqam: {s_formatted}\n\nTogrimi ?", reply_markup=check_info)
    await state.set_state(Haydovchi.check)

@disp.message(Haydovchi.check, F.text == '✅')
async def checked_registration(message: Message, state: FSMContext):
    await state.update_data(check = message.text)
    data = await state.get_data()
    phone_number = data["telefon_raqami"]
    car_number = data["mashina_raqami"]
    await message.delete()
    await save_haydovchi(phone_number, car_number, message.from_user.id)
    await message.answer("Ma'lumot saqlandi", reply_markup=ReplyKeyboardRemove())
    await state.clear()

@disp.message(Haydovchi.check, F.text == '❌')
async def again_registaration(message: Message, state: FSMContext):
    await message.delete()
    await state.clear()
    await message.answer("Boshqatan registiratsiya qilish uchun pastdagi tugmalardan birini bosing", reply_markup=choise_job)

@disp.callback_query(F.data.startswith('price:'))
async def start_yolkira_price(call: CallbackQuery, state: FSMContext):
    order_id = int(call.data.split(':', 1)[1])
    await state.update_data(zakaz_id=order_id)

    await call.message.edit_reply_markup(reply_markup=None)
    await state.set_state(YolkiraNarxi.narxi)
    await call.message.answer("Oborish narxini kiriting", reply_markup=ReplyKeyboardRemove())
    await call.answer()

@disp.message(YolkiraNarxi.narxi)
async def continue_yokira_price(message: Message, state: FSMContext):
    txt = (message.text or "").replace(" ", "")
    if not txt.isdigit():
        await message.answer("❗ Faqat raqam kiriting. Masalan: 120000")
        return
    if txt.isdigit() and len(str(txt)) <= 5:
        await message.answer("Toliq yozing: 100 ming -> 100000")
        return
    await state.update_data(narxi=txt)

    pretty = f"{int(txt):,}".replace(",", " ")
    await message.answer(f"Anigmi: {pretty} summa", reply_markup=end_yolkira)
    await state.set_state(YolkiraNarxi.tasdiq)

@disp.message(YolkiraNarxi.tasdiq, F.text == "Ha")
async def end_yokira_price(message: Message, state: FSMContext):
    data = await state.get_data()
    order = data["zakaz_id"]
    price = data["narxi"]
    await save_yolkira_narxi(order, price)
    await message.answer("Malumot saqlandi", reply_markup=ReplyKeyboardRemove())
    await state.clear()

@disp.message(YolkiraNarxi.tasdiq, F.text == "Yoq")
async def again_yolkira_price(message: Message, state: FSMContext):
    await state.set_state(YolkiraNarxi.narxi)
    await message.answer("Narxni boshqatan kiriting", reply_markup=ReplyKeyboardRemove())

@disp.message(F.text == "Mijoz")
async def start_mijoz_registaration(message:Message, state: FSMContext):
    await state.set_state(Mijoz.telefon_raqam)
    await message.delete()
    await message.answer("Telefon raqamni jo'natish", reply_markup=send_contact)

@disp.message(Mijoz.telefon_raqam)
async def continue_mijoz_registaration(message: Message, state: FSMContext):
    phone_number = message.contact.phone_number
    if not phone_number.startswith("+"):
        phone_number = "+" + phone_number
    await state.update_data(telefon_raqam = phone_number)
    await message.delete()
    await message.answer(f"Malumot togrimi ? {phone_number}", reply_markup=check_info)
    await state.set_state(Mijoz.tasdiq)

@disp.message(Mijoz.tasdiq, F.text == "❌")
async def again_mijoz_registaration(message: Message, state: FSMContext):
    await message.delete()
    await state.clear()
    await message.answer("Pastdagi tugmalardan birini tanlang", reply_markup=choise_job)

@disp.message(Mijoz.tasdiq, F.text == "✅")
async def end_mijoz_registaration(message: Message, state: FSMContext):
    await message.delete()
    data = await state.get_data()
    telefon_raqam = data["telefon_raqam"]
    await save_mijoz(telefon_raqam, message.from_user.id)
    javob = await save_mijoz(telefon_raqam, message.from_user.id)
    await message.answer(javob, reply_markup=ReplyKeyboardRemove())
    if "❌" in javob:
        await message.answer("Boshqatan urinib koring", reply_markup=choise_job)
        await state.clear()
    else:
        await state.clear()

@disp.callback_query(F.data.startswith('mijoz:price:')) 
async def start_mijoz_narxi(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")  
    pk = parts[2]
    await state.update_data(order_id=pk)
    data = await get_all_info(pk)
    await state.set_state(MijozNarxi.narxi)
    await call.message.delete_reply_markup()
    await call.message.answer(f"{data.maxsulot_markasi} markali {data.qogozdagi_maxsulot_soni} kuba betonni qanchadan olganizni kiriting")

@disp.message(MijozNarxi.narxi)
async def continue_mijoz_narxi(message: Message, state: FSMContext):
    price = (message.text or "").replace(" ", "")
    if not price.isdigit():
        await message.answer("❗ Faqat raqam kiriting. Masalan: 120 000")
        return
    if price.isdigit() and len(str(price)) <= 5:
        await message.answer("Toliq yozing: 100 ming -> 100 000")
        return
    if price.isdigit() and len(str(price)) == 5:
        await message.answer("Har bir kubani anig narxini yozing")
        return
    if price.isdigit() and len(str(price)) >= 8:
        await message.answer("Har bir kubani narxini yozing")
        return
    await state.update_data(narxi=price)
    data = await state.get_data()
    zakaz_id = data["order_id"]
    malumot = await get_all_info(zakaz_id)
    await state.set_state(MijozNarxi.checked)
    pretty = f"{int(price):,}".replace(",", " ")
    jami = int(malumot.qogozdagi_maxsulot_soni) * int(price) 
    jami_pretty = f"{int(jami):,}".replace(",", " ")
    await message.answer(f"Togrimi ? {malumot.maxsulot_markasi} markali {malumot.qogozdagi_maxsulot_soni} kubali {pretty} summadan oldizmi ?\nJami: {jami_pretty} boldimi?", reply_markup=end_yolkira)

@disp.message(MijozNarxi.checked, F.text == "Ha")
async def finish_mijoz_narxi(message: Message, state: FSMContext):
    data = await state.get_data()
    zakaz_id = data['order_id']
    price = data['narxi']
    javob = await save_mijoz_narxi(zakaz_id, price)
    await message.delete()
    if "❌" in javob:
        await message.answer(javob, reply_markup=ReplyKeyboardRemove())
        await state.clear()
    await message.answer("Malumot saqlandi", reply_markup=ReplyKeyboardRemove())
    await state.clear()

@disp.message(MijozNarxi.checked, F.text == "Yoq")
async def again_mijoz_narxi(message: Message, state: FSMContext):
    data = await state.get_data()
    zakaz_id = data["order_id"]
    malumot = await get_all_info(zakaz_id)
    await message.delete()
    await state.set_state(MijozNarxi.narxi)
    await message.answer(f"{malumot.maxsulot_markasi} markali {malumot.qogozdagi_maxsulot_soni} kuba betonni qanchadan olganizni kiriting", reply_markup=ReplyKeyboardRemove())