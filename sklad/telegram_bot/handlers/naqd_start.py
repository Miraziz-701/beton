from loader import disp, bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from keyboards.reply_keyboard.start_keyboard import order, check, check_obyekt, order_type, product_type
from keyboards.inline_keyboard.products_keyboard import inline_products, inline_naqd_obyekts, inline_xomashyos
from aiogram import F
from aiogram.fsm.context import FSMContext
from states import Zakaz, Naqd
from account.utils.maps import extract_coords_google, extract_coords_google_q, extract_coords_yandex
from account.utils.geocode import get_address
from account.utils.orginfo import get_company_by_inn_orginfo
from account.models import data
from sklad.settings import CHAT_ID
from decimal import Decimal, InvalidOperation


@disp.message(F.text == '🛒 Buyurtma berish')
async def start_order(message: Message, state: FSMContext):
    await state.set_state(Zakaz.mijoz)
    await message.answer("To'lov turini tanlang", reply_markup=order_type)


# naqd

@disp.message(F.text == 'Naqd pul')
async def naqd_pul(message: Message):
    await message.answer("Bittasini tanlang", reply_markup=check_obyekt)

@disp.message(F.text == '📍 Mavjud obyektlar')
async def see_obyekts(message: Message):
    await message.answer("Mavjud obyektlar", reply_markup=ReplyKeyboardRemove())
    await message.answer("Tanlang", reply_markup=await inline_naqd_obyekts(message.from_user.id))

@disp.callback_query(F.data.startswith("naqd_obyekt:"), ~Command("start"))
async def check_obyekts(call: CallbackQuery, state: FSMContext):
    obyekt = call.data.split(":", 1)[1]
    await state.update_data(obyekt=obyekt)
    await state.update_data(address_need=True)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer("Birini tanlang", reply_markup=product_type)
    await state.set_state(Naqd.product_type)

@disp.message(Naqd.product_type, F.text == "Mahsulot")
async def product_start(message: Message, state: FSMContext):
    await state.update_data(product_type="Mahsulot")

    # OLDINGI REPLY KEYBOARDNI YOPISH
    await message.answer("✅ Tanlandi: Mahsulot", reply_markup=ReplyKeyboardRemove())

    # KEYINGI INLINE MENYU / RO'YXAT
    await message.answer("Mavjud mahsulotlar", reply_markup=await inline_products())
    await state.set_state(Naqd.product)

@disp.message(Naqd.product_type, F.text == "Xomashyo")
async def product_start(message: Message, state: FSMContext):
    await state.update_data(product_type="Xomashyo")
    await message.answer("✅ Tanlandi: Xomashyo" , reply_markup=ReplyKeyboardRemove())
    await message.answer("Mavjud xomashyolar", reply_markup=await inline_xomashyos())
    await state.set_state(Naqd.product)


@disp.message(F.text == "➕ Obyekt qo'shish")
async def add_obyekt(message: Message, state: FSMContext):
    await message.answer('Obyekt nomi', reply_markup=ReplyKeyboardRemove())
    await state.set_state(Naqd.obyekt)

@disp.message(Naqd.obyekt, ~Command("start"))
async def enter_product(message: Message, state: FSMContext):
    await state.update_data(obyekt=message.text.title())
    await state.update_data(address_need=False)
    await message.answer('Birini tanlang', reply_markup=product_type)
    await state.set_state(Naqd.product_type)

    
    # await message.answer('Mavjud mahsulotlar', reply_markup=await inline_products())
    # await state.set_state(Naqd.product)

@disp.callback_query(F.data.startswith("product:"), Naqd.product, ~Command("start"))
async def miqdori(call: CallbackQuery, state: FSMContext):
    product = call.data.split(":", 1)[1]
    await state.update_data(product=product)
    await state.set_state(Naqd.miqdori)
    await call.message.delete_reply_markup()
    await call.message.answer(f'{product}\n\nMiqdorini kiriting')
    

@disp.message(Naqd.miqdori, ~Command("start"))
async def check_miqdori(message: Message, state: FSMContext):
    try:
        miqdor = Decimal(message.text.replace(',', '.'))
        
        if miqdor <= 0:
            await message.answer("0 dan katta son kiriting")
            await state.set_state(Naqd.miqdori)
            
        await state.update_data(miqdori=float(miqdor))
        await state.set_state(Naqd.price)
        await message.answer("Kelishilgan narxni kiriting")
    
    except InvalidOperation:
        await message.answer("Miqdori raqamlardan iborat bo'ladi")
        await state.set_state(Naqd.miqdori)   


@disp.message(Naqd.price, ~Command("start"))
async def enter_price(message: Message, state: FSMContext):
    clean = message.text.replace(" ", "")
    
    datas = await state.get_data()
    
    product_type = datas['product_type']
    

    if clean.isdigit():
        if product_type == "Xomashyo":
            if len(clean) <= 2:
                await message.answer("To'liq narxni yozing")
            else:
                await state.update_data(price=int(clean))
                await state.set_state(Naqd.time)
                await message.answer("Yetkazib berish vaqtini yozing")
        else:
            if len(clean) <= 5:
                await message.answer("To'liq narxni yozing")
            else:
                await state.update_data(price=int(clean))
                await state.set_state(Naqd.time)
                await message.answer("Yetkazib berish vaqtini yozing")

    else: 
        await message.answer("Narx raqamlardan iborat bo'ladi")
        await state.set_state(Naqd.price)

@disp.message(Naqd.time, ~Command("start"))
async def enter_date(message: Message, state: FSMContext):
    await state.update_data(time=message.text.title())
    await message.answer("Qanday tartibda yetkazib beriladi?")
    await state.set_state(Naqd.description)

@disp.message(Naqd.description, ~Command("start"))
async def enter_tartib(message: Message, state: FSMContext):
    await state.update_data(description=message.text.title())
    await message.answer("Obyektning aloqa uchun telefon raqami\n\nMisol uchun raqam:\n<b>977010101</b>")
    await state.set_state(Naqd.phone_number)

@disp.message(Naqd.phone_number, ~Command("start"))
async def enter_phonenumber(message: Message, state: FSMContext):
    clean = message.text.replace(" ", "")


    if not clean.isdigit():
        await message.answer("Telefon raqam raqamlardan iborat bo'ladi")
        await state.set_state(Naqd.description)
    
    else:
        if len(clean) != 9:
            await message.answer("9 ta raqamdan iborat bo'lishi kerak\n\n977010101")
            await state.set_state(Naqd.description)
        
        else:
            await state.update_data(phone_number=clean)
            datas = await state.get_data()
            typ = datas['address_need']
            if typ is not True:
                await message.answer("Obyekt lokatsiyasini jo'nating")
                await state.set_state(Naqd.address_full)
            else:
                obyekt = datas['obyekt'] 

                location_name, location_full, location_lat, location_lon = await data.see_naqd_obyekt_info(obyekt)
                
                await state.update_data(address_full=location_full)
                await state.update_data(address=location_name)
                await state.update_data(address_lat=location_lat)
                await state.update_data(address_lon=location_lon)
                
                product = datas['product']
                miqdori = datas['miqdori']
                price = datas['price']
                time = datas['time']
                description = datas['description']
                phone_number = datas['phone_number']

                price_formatted = f"{int(price):,}".replace(",", " ")



                await message.answer_location(location_lat, location_lon)

                await message.answer(
                f"""
Ma'lumot to'g'rimi:


Obyekt nomi: {obyekt}
Maxsulot: {product}
Miqdori: {miqdori}
Kelishilgan narxi: {price_formatted}
Yetkazib berish vaqti: {time}
Qanday tartibda yetkazilib berishi: {description}
Aloqa uchun raqam: {phone_number}
Joylashuvi: {location_name}
""", reply_markup=check)
                
                await state.set_state(Naqd.status)

                

@disp.message(Naqd.address_full, ~Command("start"))
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
        product = data['product']
        miqdori = data['miqdori']
        price = data['price']
        time = data['time']
        description = data['description']
        phone_number = data['phone_number']
        address_full = data['address_full']
        address_lat = data['address_lat']
        address_lon = data['address_lon']
        address = data['address']

        price_formatted = f"{int(price):,}".replace(",", " ")

        await message.answer_location(address_lat, address_lon)        

        await message.answer(
            f"""
Ma'lumot to'g'rimi:


Obyekt nomi: {obyekt}
Maxsulot: {product}
Miqdori: {miqdori}
Kelishilgan narxi: {price_formatted}
Yetkazib berish vaqti: {time}
Qanday tartibda yetkazilib berishi: {description}
Aloqa uchun raqam: {phone_number}
Joylashuvi: {address}
""", reply_markup=check)

        await state.set_state(Naqd.status)

    
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
        product = data['product']
        miqdori = data['miqdori']
        price = data['price']
        time = data['time']
        description = data['description']
        phone_number = data['phone_number']
        address_full = data['address_full']
        address_lat = data['address_lat']
        address_lon = data['address_lon']
        address = data['address']

        price_formatted = f"{int(price):,}".replace(",", " ")

        await message.answer_location(address_lat, address_lon)

        await message.answer(
            f"""
Ma'lumot to'g'rimi:


Obyekt nomi: {obyekt}
Maxsulot: {product}
Miqdori: {miqdori}
Kelishilgan narxi: {price_formatted}
Yetkazib berish vaqti: {time}
Qanday tartibda yetkazilib berishi: {description}
Aloqa uchun raqam: {phone_number}
Joylashuvi: {address}
""", reply_markup=check)


        await state.set_state(Naqd.status)



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
        product = data['product']
        miqdori = data['miqdori']
        price = data['price']
        time = data['time']
        description = data['description']
        phone_number = data['phone_number']
        address_full = data['address_full']
        address_lat = data['address_lat']
        address_lon = data['address_lon']
        address = data['address']

        price_formatted = f"{int(price):,}".replace(",", " ")

        await message.answer_location(address_lat, address_lon)
        await message.answer(
            f"""
Ma'lumot to'g'rimi:


Obyekt nomi: {obyekt}
Maxsulot: {product}
Miqdori: {miqdori}
Kelishilgan narxi: {price_formatted}
Yetkazib berish vaqti: {time}
Qanday tartibda yetkazilib berishi: {description}
Aloqa uchun raqam: {phone_number}
Joylashuvi: {address}
""", reply_markup=check)

        await state.set_state(Naqd.status)

    else:
        await message.answer(
            "❗ Iltimos, lokatsiyani 📍 Telegram orqali yuboring "
            "yoki koordinatasi bor Google/Yandex Maps linkini tashlang."
        )
        await state.set_state(Naqd.address_full)

@disp.message(Naqd.status, ~Command("start"), F.text == "✅")
async def end_mijoz(message: Message, state: FSMContext):
    datas = await state.get_data()
    obyekt = datas['obyekt']
    address_need = datas['address_need']
    product_type = datas['product_type']
    product = datas['product']
    miqdori = datas['miqdori']
    price = datas['price']
    time = datas['time']
    description = datas['description']
    phone_number = datas['phone_number']
    address_full = datas['address_full']
    address_lat = datas['address_lat']
    address_lon = datas['address_lon']
    address = datas['address']

    if not address_need is True:
        await data.add_naqd_obyekt(obyekt, address, address_full, address_lat, address_lon) 

    if product_type == "Mahsulot":
        await data.add_order(await data.select_agent_id(message.from_user.id), "Naqd", await data.select_naqd_obyekt_id(obyekt), await data.see_product_id(product), "", miqdori, price, time, description, phone_number)
    else:
        await data.add_order(await data.select_agent_id(message.from_user.id), "Naqd", await data.select_naqd_obyekt_id(obyekt), "", await data.see_product_id(product), miqdori, price, time, description, phone_number)


    
    await bot.send_message(
        chat_id=CHAT_ID,
        text = f"""
Jo'natuvchi: {await data.select_agent(message.from_user.id)}
Obyekt nomi: {obyekt}
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

@disp.message(Naqd.status, ~Command("start"), F.text == "❌")
async def again_register(message: Message, state: FSMContext):
    await message.answer("Obyekt nomini qaytadan kiriting", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Naqd.obyekt)

# prichesliniya



# @disp.message(F.text == "Pul ko'chirish")
# async def pul_k(message: Message, state: FSMContext):
#     await message.answer("Obyekt nomini kiriting")
#     await state.set_state(PulKochirish.obyekt_nomi)


# @disp.message(PulKochirish.obyekt_nomi)
# async def t_n(message: Message, state: FSMContext):
#     await message.answer("Tashkilot nomini kiriting")
#     await state.set_state(PulKochirish.tashkilot_nomi)

# @disp.message(PulKochirish.tashkilot_nomi)
# async def t_n(message: Message, state: FSMContext):
#     await message.answer("INN kiriting")
#     await state.set_state(PulKochirish.inn)



# @disp.message(Zakaz.user)
# async def obyekt_name(message: Message, state: FSMContext):
#     await state.update_data(user=message.text.title())
#     await state.set_state(Zakaz.obyekt)
#     await message.answer('Korxona yoki tashkilot nomi yoki inn kiriting')

# @disp.message(Zakaz.obyekt)
# async def see_products(message: Message, state: FSMContext):
#     if not message.text.isdigit():
#         await state.update_data(obyekt=message.text.title())
#         await state.set_state(Zakaz.product)
#         await message.answer('Mavjud mahsulotlar', reply_markup=await inline_products())
#         return

    
#     inn = message.text.strip()

#     data = get_company_by_inn_orginfo(inn)

#     if not data:
#         await message.answer('Korxona topilmadi')
#         await state.set_state(Zakaz.obyekt)
#         return
    
#     await state.update_data(obyekt=data['company_name'])
#     await state.set_state(Zakaz.product)
#     await message.answer('Mavjud mahsulotlar', reply_markup=await inline_products())

# @disp.callback_query(F.data.startswith("product:"))
# async def miqdori(call: CallbackQuery, state: FSMContext):
#     product = call.data.split(":", 1)[1]
#     await state.update_data(product=product)
#     await state.set_state(Zakaz.quantity)
#     await call.message.delete_reply_markup()
#     await call.message.answer(f'{product}\n\nSonini kiriting')

# @disp.message(Zakaz.quantity)
# async def enter_count(message: Message, state: FSMContext):
#     await state.update_data(quantity=message.text)
#     await state.set_state(Zakaz.location)
#     await message.answer('Dostavka boradigan joyni lokatsiyani tashang')

# @disp.message(Zakaz.location)
# async def get_location(message: Message, state: FSMContext):

#     location_name = ""

#     if message.text.startswith("https://www.google.com/maps?q=") or message.text.startswith("https://maps.google.com/") or message.text.startswith("https://www.google.com/maps/place/"):
#         await state.update_data(location=message.text)
#         clear = (
#             extract_coords_google(message.text) or extract_coords_google_q(message.text)
#         )

#         lat, lon = clear

#         address = get_address(lat, lon)

#         location_name = address
    
#     elif message.text.startswith("https://yandex.com/maps/") or message.text.startswith("https://maps.yandex.ru/") or message.text.startswith("https://maps.yandex.ru/") or message.text.startswith("https://yandex.uz/maps/"):
#         await state.update_data(location=message.text)

#         clear = (
#             extract_coords_yandex(message.text)
#         )

#         lat, lon = clear

#         address = get_address(lat, lon)

#         location_name = address

#     elif message.location:
#         await state.update_data(location=message.text)

#         address = get_address(message.location.latitude, message.location.longitude)

#         location_name = address

#     else:
#         await message.answer(
#             "❗ Iltimos, lokatsiyani 📍 Telegram orqali yuboring "
#             "yoki koordinatasi bor Google/Yandex Maps linkini tashlang."
#         )
#         await state.set_state(Zakaz.location)

    
#     data = await state.get_data()
#     user = data['user']
#     obyekt = data['obyekt']
#     product_name = data['product']
#     miqdori = data['quantity']
#     location = data['location']
    

#     await message.answer(f"""
# {user} dan xabar topgansiz
# {obyekt} dan kelgansiz
# {product_name} 
# {miqdori} ta
# {location_name} ga olib borish kerak
# """)
    
#     await message.answer(location)

    # await state.set_state(Zakaz.check)
    # await message.answer()