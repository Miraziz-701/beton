from asgiref.sync import sync_to_async
from account.models import Mashina, Asosiy, Mijoz

@sync_to_async
def save_haydovchi(telefon: str, mashina_raqami: str, telegram_id: int):
    Mashina.objects.create(telefon_raqami=telefon, mashina_raqami=mashina_raqami, telegram_id=telegram_id)

@sync_to_async
def save_yolkira_narxi(order_id: int, price: int):
    yolkira = Asosiy.objects.get(id=order_id)
    yolkira.haydovchi_qoygan_narx = price
    yolkira.save()

@sync_to_async
def save_mijoz(telefon: str, telegram_id: int):
    try:
        # Telefon raqam bo‘yicha mijozni qidirish
        mijoz = Mijoz.objects.get(telefon_raqami=telefon)
        
        # Agar topilgan bo‘lsa telegram_id ni yangilash
        mijoz.telegram_id = telegram_id
        mijoz.save()
        
        return f"✅ Malumot saqlandi"
    
    except Mijoz.DoesNotExist:
        # Agar bunday telefon raqamli mijoz yo‘q bo‘lsa
        return "❌ Siz Asad Beton ning mijozi emassiz."

@sync_to_async
def get_all_info(order_id: int):
    return Asosiy.objects.select_related("maxsulot_markasi",).filter(id=order_id).first()

@sync_to_async
def save_mijoz_narxi(zakaz_id: int, mijoz_narxi: int):
    zakaz = Asosiy.objects.get(id=zakaz_id)

    if zakaz.narx_qoyildi:
        pretty_dona = f"{int(zakaz.mijoz_qoygan_narx):,}".replace(",", " ")
        pretty_jami = f"{int(zakaz.mijoz_jami_qoygan_narx):,}".replace(",", " ")

        return f"❌ Siz kech qoldingiz sizning {zakaz.maxsulot_markasi} markali {zakaz.qogozdagi_maxsulot_soni} kuba betonningiz {pretty_dona} sumdan qoyilgan \nJami: {pretty_jami} sum boldi"

    mijoz_narx = float(mijoz_narxi)
    jami = zakaz.qogozdagi_maxsulot_soni * mijoz_narx
    zakaz.mijoz_qoygan_narx = mijoz_narxi
    zakaz.mijoz_jami_qoygan_narx = jami
    zakaz.save()