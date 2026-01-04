from loader import disp, bot
from sklad.settings import CHAT_ID
from account.models import data
from states import Pri
from aiogram import F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext
from account.utils.orginfo import get_company_by_inn_orginfo
from keyboards.inline_keyboard.products_keyboard import inline_products, inline_pri_obyekts
from account.utils.maps import extract_coords_google, extract_coords_google_q, extract_coords_yandex
from account.utils.geocode import get_address
from keyboards.reply_keyboard.start_keyboard import check, check_obyekt_tash
from decimal import Decimal, InvalidOperation



@disp.message(F.text == "Pul ko'chirish")
async def pri_pul(message: Message):
    await message.answer('Bittasini tanlang', reply_markup=check_obyekt_tash)

@disp.message(F.text == "🏢 Mavjud obyektlar")
async def pri_obyekts(message: Message):
    await message.answer("Mavjud obyektlar", reply_markup=ReplyKeyboardRemove())
    await message.answer("Tanlang", reply_markup=await inline_pri_obyekts())

@disp.callback_query(F.data.startswith("pri_obyekt:"))
async def check_obyekts(call: CallbackQuery, state: FSMContext):
    obyekt = call.data.split(":", 1)[1]
    await state.update_data(obyekt=obyekt)
    await state.update_data(address_need=True)
    await call.message.delete_reply_markup()
    await call.message.answer("Mavjud mahsulotlar", reply_markup=await inline_products())
    await state.set_state(Pri.product)

@disp.message(F.text == "📝 Obyekt qo'shish")
async def pri_obyekt(message: Message, state: FSMContext):
    await message.answer('Obyekt nomi', reply_markup=ReplyKeyboardRemove())
    await state.set_state(Pri.obyekt)


@disp.message(Pri.obyekt)
async def enter_product(message: Message, state: FSMContext):
    await state.update_data(obyekt=message.text.title())
    await state.update_data(address_need=False)
    await message.answer('Tashkilotning INN raqamini kiriting')
    await state.set_state(Pri.tashkilot)

@disp.message(Pri.tashkilot)
async def check_inn(message: Message, state: FSMContext):
    clean = "".join(message.text.split())

    if not clean.isdigit():
        await message.answer("Faqat tashkilotning <b>innisini</b> kiriting")
        await state.set_state(Pri.tashkilot)
    
    else:

        data = get_company_by_inn_orginfo(clean)

        if not data:
            await message.answer("INN orqali ma'lumot topilmadi")
            await message.answer("Boshqatan urinib ko'ring")
            await state.set_state(Pri.tashkilot)
            return
        
        await state.update_data(tashkilot=data['company_name'])
        await message.answer(f"{data['company_name']} uchun mahsulot tanlang", reply_markup=await inline_products())
        await state.set_state(Pri.product)

@disp.callback_query(F.data.startswith("product:"), Pri.product)
async def miqdori(call: CallbackQuery, state: FSMContext):
    product = call.data.split(":", 1)[1]
    await state.update_data(product=product)
    await state.set_state(Pri.miqdori)
    await call.message.delete_reply_markup()
    await call.message.answer(f'{product}\n\nSonini kiriting')

@disp.message(Pri.miqdori)
async def check_miqdori(message: Message, state: FSMContext):
    try:
        miqdor = Decimal(message.text.replace(',', '.'))
        if miqdor <= 0:
            await message.answer("0 dan katta son kiriting")
            await state.set_state(Pri.miqdori)
        await state.update_data(miqdori=float(miqdor))
        await state.set_state(Pri.price)
        await message.answer("Kelishilgan narxni kiriting")
    
    except InvalidOperation:
        await message.answer("Miqdori raqamlardan iborat bo'ladi")
        await state.set_state(Pri.price)

    


@disp.message(Pri.price)
async def enter_price(message: Message, state: FSMContext):
    clean = "".join(message.text.split())


    if clean.isdigit():
        if len(clean) <= 5:
            await message.answer("To'liq narxni yozing")
        else:    
            await state.update_data(price=message.text)
            await state.set_state(Pri.otkat)
            await message.answer("Kelishilgan bonusingizni kiriting")  
    else: 
        await message.answer("Narx raqamlardan iborat bo'ladi")
        await state.set_state(Pri.miqdori)

@disp.message(Pri.otkat)
async def enter_otkat(message: Message, state: FSMContext):
    clean = "".join(message.text.split())
    
    if clean.isdigit():
        await state.update_data(otkat=clean)
        await state.set_state(Pri.time)
        await message.answer("Yetkazib berilish vaqti")  
    
    else:
        await message.answer("Kelishilgan bonus raqamlardan iborat bo'ladi")
        await state.set_state(Pri.otkat)

@disp.message(Pri.time)
async def enter_date(message: Message, state: FSMContext):
    await state.update_data(time=message.text.title())
    await message.answer("Qanday tartibda yetkazib beriladi?")
    await state.set_state(Pri.description)

@disp.message(Pri.description)
async def enter_tartib(message: Message, state: FSMContext):
    await state.update_data(description=message.text.title())
    await message.answer("Obyektning aloqa uchun telefon raqami\n\nMisol uchun raqam:\n<b>977010101</b>")
    await state.set_state(Pri.phone_number)

@disp.message(Pri.phone_number)
async def enter_phonenumber(message: Message, state: FSMContext):
    clean = "".join(message.text.split())


    if not clean.isdigit():
        await message.answer("Telefon raqam raqamlardan iborat bo'ladi")
        await state.set_state(Pri.description)
    
    else:
        if len(clean) != 9:
            await message.answer("9 ta raqamdan iborat bo'lishi kerak\n\n977010101")
            await state.set_state(Pri.description)
        
        else:
            await state.update_data(phone_number=clean)
            datas = await state.get_data()
            address_need = datas['address_need']
            if address_need is not True:
                await message.answer("Obyekt lokatsiyasini jo'nating")
                await state.set_state(Pri.address_full)
            else:
                obyekt = datas['obyekt']

                tashkilot_name, location_name, location_full, location_lat, location_lon = await data.see_pri_obyekt_info(obyekt)
                
                await state.update_data(tashkilot=tashkilot_name)
                await state.update_data(address=location_name)
                await state.update_data(address_lat=location_lat)
                await state.update_data(address_lon=location_lon)
                await state.update_data(address_full=location_full)

                product = datas['product']
                miqdori = datas['miqdori']
                price = datas['price']
                otkat = datas['otkat']
                time = datas['time']
                description = datas['description']
                phone_number = datas['phone_number']

                price_formatted = f"{int(price):,}".replace(",", " ")
                otkat_formatted = f"{int(otkat):,}".replace(",", " ")

                await message.answer_location(location_lat, location_lon)

                await message.answer(
                    f"""
Ma'lumot to'g'rimi:


Obyekt nomi: {obyekt}
Tashkilot nomi: {tashkilot_name}
Maxsulot: {product}
Miqdori: {miqdori}
Kelishilgan narxi: {price_formatted}
Kelishilgan bonus narxi: {otkat_formatted}
Yetkazib berish vaqti: {time}
Qanday tartibda yetkazilib berishi: {description}
Aloqa uchun raqam: {phone_number}
Joylashuvi: {location_name}
""", reply_markup=check)

                await state.set_state(Pri.status)
                

@disp.message(Pri.address_full)
async def enter_address(message: Message, state: FSMContext):
    if message.text and (message.text.startswith("https://www.google.com/maps?q=") or message.text.startswith("https://maps.google.com/") or message.text.startswith("https://www.google.com/maps/place/")):
        await state.update_data(address_full=message.text)
        clear = (
            extract_coords_google(message.text) or extract_coords_google_q(message.text)
        )

        lat, lon = clear

        await state.update_data(address=get_address(lat, lon))
        await state.update_data(address_lat=lat)
        await state.update_data(address_lon=lon)

        data = await state.get_data()
        obyekt = data['obyekt']
        tashkilot = data['tashkilot']
        product = data['product']
        miqdori = data['miqdori']
        price = data['price']
        otkat = data['otkat']
        time = data['time']
        description = data['description']
        phone_number = data['phone_number']
        address_full = data['address_full']
        address_lat = data['address_lat']
        address_lon = data['address_lon']
        address = data['address']

        price_formatted = f"{int(price):,}".replace(",", " ")
        otkat_formatted = f"{int(otkat):,}".replace(",", " ")

        await message.answer_location(address_lat, address_lon)

        await message.answer(
            f"""
Ma'lumot to'g'rimi:


Obyekt nomi: {obyekt}
Tashkilot nomi: {tashkilot}
Maxsulot: {product}
Miqdori: {miqdori}
Kelishilgan narxi: {price_formatted}
Kelishilgan bonus narxi: {otkat_formatted}
Yetkazib berish vaqti: {time}
Qanday tartibda yetkazilib berishi: {description}
Aloqa uchun raqam: {phone_number}
Joylashuvi: {address}
""", reply_markup=check)

        await state.set_state(Pri.status)

    
    elif message.text and (message.text.startswith("https://yandex.com/maps/") or message.text.startswith("https://maps.yandex.ru/") or message.text.startswith("https://maps.yandex.ru/") or message.text.startswith("https://yandex.uz/maps/")):
        await state.update_data(address_full=message.text)

        clear = (
            extract_coords_yandex(message.text)
        )

        lat, lon = clear

        await state.update_data(address=get_address(lat, lon))
        await state.update_data(address_lat=lat)
        await state.update_data(address_lon=lon)

        data = await state.get_data()
        obyekt = data['obyekt']
        tashkilot = data['tashkilot']
        product = data['product']
        miqdori = data['miqdori']
        price = data['price']
        otkat = data['otkat']
        time = data['time']
        description = data['description']
        phone_number = data['phone_number']
        address_full = data['address_full']
        address_lat = data['address_lat']
        address_lon = data['address_lon']
        address = data['address']

        price_formatted = f"{int(price):,}".replace(",", " ")
        otkat_formatted = f"{int(otkat):,}".replace(",", " ")

        await message.answer_location(address_lat, address_lon)

        await message.answer(
            f"""
Ma'lumot to'g'rimi:


Obyekt nomi: {obyekt}
Tashkilot nomi: {tashkilot}
Maxsulot: {product}
Miqdori: {miqdori}
Kelishilgan narxi: {price_formatted}
Kelishilgan bonus narxi: {otkat_formatted}
Yetkazib berish vaqti: {time}
Qanday tartibda yetkazilib berishi: {description}
Aloqa uchun raqam: {phone_number}
Joylashuvi: {address}
""", reply_markup=check)


        await state.set_state(Pri.status)



    elif message.location:
        lat = message.location.latitude
        lon = message.location.longitude

        map_link = f"https://maps.google.com/?q={lat},{lon}"

        await state.update_data(address_full=map_link)

        await state.update_data(address=get_address(lat, lon))
        await state.update_data(address_lat=lat)
        await state.update_data(address_lon=lon)

        data = await state.get_data()
        obyekt = data['obyekt']
        tashkilot = data['tashkilot']
        product = data['product']
        miqdori = data['miqdori']
        price = data['price']
        otkat = data['otkat']
        time = data['time']
        description = data['description']
        phone_number = data['phone_number']
        address_full = data['address_full']
        address_lat = data['address_lat']
        address_lon = data['address_lon']
        address = data['address']

        price_formatted = f"{int(price):,}".replace(",", " ")
        otkat_formatted = f"{int(otkat):,}".replace(",", " ")

        await message.answer_location(address_lat, address_lon)

        await message.answer(
            f"""
Ma'lumot to'g'rimi:


Obyekt nomi: {obyekt}
Tashkilot nomi: {tashkilot}
Maxsulot: {product}
Miqdori: {miqdori}
Kelishilgan narxi: {price_formatted}
Kelishilgan bonus narxi: {otkat_formatted}
Yetkazib berish vaqti: {time}
Qanday tartibda yetkazilib berishi: {description}
Aloqa uchun raqam: {phone_number}
Joylashuvi: {address}
""", reply_markup=check)

        await state.set_state(Pri.status)

    else:
        await message.answer(
            "❗ Iltimos, lokatsiyani 📍 Telegram orqali yuboring "
            "yoki koordinatasi bor Google/Yandex Maps linkini tashlang."
        )
        await state.set_state(Pri.address_full)

@disp.message(Pri.status, F.text == "✅")
async def end_mijoz(message: Message, state: FSMContext):
    datas = await state.get_data()
    obyekt = datas['obyekt']
    address_need = datas['address_need']
    tashkilot = datas['tashkilot']
    product = datas['product']
    miqdori = datas['miqdori']
    price = datas['price']
    otkat = datas['otkat']
    time = datas['time']
    description = datas['description']
    phone_number = datas['phone_number']
    address_full = datas['address_full']
    address_lat = datas['address_lat']
    address_lon = datas['address_lon']
    address = datas['address']

    if address_need is not True:
        await data.add_pri_obyekt(obyekt, tashkilot, address, address_full, address_lat, address_lon)
    
    await data.add_order(await data.select_agent_id(message.from_user.id), 'Pri', await data.select_pri_obyekt_id(obyekt), await data.see_product_id(product), miqdori, price, time, description, phone_number, otkat)

    await bot.send_message(
        chat_id=CHAT_ID,
        text = f"""
Jo'natuvchi: {await data.select_agent(message.from_user.id)}
Obyekt nomi: {obyekt}
Tashkilot nomi: {tashkilot}
Maxsulot: {product}
Miqdori: {miqdori}
Yetkazib berish vaqti: {time}
Qanday tartibda yetkazilib berishi: {description}
Aloqa uchun raqam: {phone_number}
Joylashuvi: {address}

Lokatsiyasi 👇:
        """)
    
    await bot.send_location(
        chat_id=CHAT_ID,
        latitude=address_lat,
        longitude=address_lon
    )
    

    # datas = await state.get_data()
    # full_name = datas['full_name']
    # obyekt_name = datas['obyekt_name']
    # aloqa_number = datas['aloqa_number']
    # address = datas['address']
    # address_name = datas['address_name']

    # data.add_obyekt(obyekt_name, address_name, address, aloqa_number)
    # data.add_client(full_name, data.select_obyekt_id(obyekt_name))



    await message.answer("Zakaz qabul qilindi", reply_markup=ReplyKeyboardRemove())

    await state.clear()

@disp.message(Pri.status, F.text == "❌")
async def again_register(message: Message, state: FSMContext):
    await message.answer("Mijozning ism familyasini kiriting", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Pri.obyekt)