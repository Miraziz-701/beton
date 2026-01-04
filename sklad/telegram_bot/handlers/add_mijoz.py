from loader import disp
from aiogram import F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from states import Client
from account.models import data
from account.utils.orginfo import get_company_by_inn_orginfo
from account.utils.maps import extract_coords_google, extract_coords_google_q, extract_coords_yandex
from account.utils.geocode import get_address
from keyboards.reply_keyboard.start_keyboard import check


@disp.message(F.text == "➕ Mijoz qo'shish")
async def add_mijoz(message: Message, state: FSMContext):
    await message.answer("Aloqa uchun ism", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Client.full_name)

@disp.message(Client.full_name)
async def add_obyekt(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.title())
    await message.answer("Aloqadagi shaxsning telefon raqami")
    await state.set_state(Client.aloqa_number)

@disp.message(Client.aloqa_number)
async def get_aloqa_number(message: Message, state: FSMContext):
    clean = "".join(message.text.split())


    if not clean.isdigit():
        await message.answer("Aloqadagi shaxsning telefon raqami")
        await state.set_state(Client.obyekt_name)

    else:
        if len(clean) != 9:
            await message.answer("Iloji boricha 994994949 shunday tartibda ya'ni 9 ta raqam bo'lishi kerak")
            await state.set_state(Client.obyekt_name)
        else:
            await state.update_data(aloqa_number=clean)
            await message.answer("Korxona yoki tashkilot manzilini ya'ni lokatsiyasini tashlang")
            await state.set_state(Client.address)

@disp.message(Client.obyekt_name)
async def check_obyekt(message: Message, state: FSMContext):
    if message.text.isdigit():
        inn = message.text.strip()

        data = get_company_by_inn_orginfo(inn)

        if not data:
            await message.answer("INN orqali ma'lumot topilmadi")
            await message.answer("Obyekt nomini kiriting")
            await state.set_state(Client.full_name)
            return
        
        await state.update_data(obyekt_name=data['company_name'])
        await message.answer(f"{data['company_name']} aloqa raqamini jo'nating\n\n\nShunday tartibda: <b>994994949</b>")
        await state.set_state(Client.aloqa_number)

    else:
        await state.update_data(obyekt_name=message.text.title())
        await message.answer("Tashkilot raqamini jo'nating")
        await state.set_state(Client.aloqa_number)


@disp.message(Client.address)
async def get_loaction(message: Message, state: FSMContext):

    if message.text and (message.text.startswith("https://www.google.com/maps?q=") or message.text.startswith("https://maps.google.com/") or message.text.startswith("https://www.google.com/maps/place/")):
        await state.update_data(address=message.text)
        clear = (
            extract_coords_google(message.text) or extract_coords_google_q(message.text)
        )

        lat, lon = clear

        await state.update_data(address_name=get_address(lat, lon))

        data = await state.get_data()
        full_name = data['full_name']
        obyekt_name = data['obyekt_name']
        aloqa_number = data['aloqa_number']
        address = data['address']
        address_name = data['address_name']

        await message.answer(
            f"""
Ma'lumot to'g'rimi:


Ism familya: {full_name}
Obyekt nomi: {obyekt_name}
Aloqa uchun raqam: {aloqa_number}
Joylashuvi: {address_name}

Lokatsiyasi 👇: {address}
""", reply_markup=check)

        await state.set_state(Client.check)

    
    elif message.text and (message.text.startswith("https://yandex.com/maps/") or message.text.startswith("https://maps.yandex.ru/") or message.text.startswith("https://maps.yandex.ru/") or message.text.startswith("https://yandex.uz/maps/")):
        await state.update_data(address=message.text)

        clear = (
            extract_coords_yandex(message.text)
        )

        lat, lon = clear

        await state.update_data(address_name=get_address(lat, lon))


        data = await state.get_data()
        full_name = data['full_name']
        obyekt_name = data['obyekt_name']
        aloqa_number = data['aloqa_number']
        address = data['address']
        address_name = data['address_name']

        await message.answer(
            f"""
Ma'lumot to'g'rimi:


Ism familya: {full_name}
Obyekt nomi: {obyekt_name}
Aloqa uchun raqam: {aloqa_number}
Joylashuvi: {address_name}

Lokatsiyasi 👇: {address}
""", reply_markup=check)


        await state.set_state(Client.check)



    elif message.location:
        lat = message.location.latitude
        lon = message.location.longitude

        map_link = f"https://maps.google.com/?q={lat},{lon}"

        await state.update_data(address=map_link)

        await state.update_data(address_name=get_address(message.location.latitude, message.location.longitude))
        

        data = await state.get_data()
        full_name = data['full_name']
        obyekt_name = data['obyekt_name']
        aloqa_number = data['aloqa_number']
        address = data['address']
        address_name = data['address_name']

        await message.answer(
            f"""
Ma'lumot to'g'rimi:


Ism familya: {full_name}
Obyekt nomi: {obyekt_name}
Aloqa uchun raqam: {aloqa_number}
Joylashuvi: {address_name}

Lokatsiyasi 👇: {address}
""", reply_markup=check)

        await state.set_state(Client.check)

    else:
        await message.answer(
            "❗ Iltimos, lokatsiyani 📍 Telegram orqali yuboring "
            "yoki koordinatasi bor Google/Yandex Maps linkini tashlang."
        )
        await state.set_state(Client.aloqa_number)

@disp.message(Client.check, F.text == "✅")
async def end_mijoz(message: Message, state: FSMContext):

    datas = await state.get_data()
    full_name = datas['full_name']
    obyekt_name = datas['obyekt_name']
    aloqa_number = datas['aloqa_number']
    address = datas['address']
    address_name = datas['address_name']

    await data.add_obyekt(obyekt_name, address_name, address, aloqa_number)
    await data.add_client(full_name, await data.select_obyekt_id(obyekt_name))


    await message.answer("Yangi mijoz qo'shildi")

    await state.clear()

@disp.message(Client.check, F.text == "❌")
async def again_register(message: Message, state: FSMContext):
    await message.answer("Mijozning ism familyasini kiriting")
    await state.set_state(Client.full_name)
