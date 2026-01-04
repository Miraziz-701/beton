import requests
from account.models import PriObyekts, NaqdObyekts

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbynFqkYpTwOsvGc8EbWa-LlNSwpImf8hsuGERmCdmaSqMa0KRAwV8IQRYRHb3-3Xajn/exec"



def send_zakaz_to_google(zakaz):


    number = zakaz.obyekt_id  # IntegerField

    try:
        if zakaz.tashkilot_nomi:
            mijoz = zakaz.tashkilot_nomi.tashkilot_name
            info = PriObyekts.objects.get(pk=number)
            obyekt = info.obyekt_name
            obyekt_address = info.location_name

        else:
            mijoz = zakaz.kim_tomonidan_jonatilgani.full_name
            info = NaqdObyekts.objects.get(pk=number)
            obyekt = info.obyekt_name
            obyekt_address = info.location_name

    except Exception as e:
        print("OBYEKT TOPILMADI:", e)
        return  # 👈 GOOGLEGA UMUMAN YUBORMAYMIZ



    payload = {
        "agent": zakaz.kim_tomonidan_jonatilgani.full_name,
        "sana": zakaz.date.strftime("%Y-%m-%d %H:%M"),
        "mijoz": mijoz,
        "marka": zakaz.maxsulot_markasi.markasi,
        "obyekt": obyekt,
        "mashina": zakaz.mashina.mashina_raqami,
        "qogoz": zakaz.qogozdagi_maxsulot_soni,
        "kuba": zakaz.mijoz_qoygan_narx,
        "umumiy": zakaz.mijoz_jami_qoygan_narx,
        "otkat": zakaz.xarajat_narxi,
        "joy": obyekt_address
    }

    try:
        resp = requests.post(
            GOOGLE_SCRIPT_URL,
            json=payload,
            timeout=5
        )
        print("GOOGLE STATUS:", resp.status_code, resp.text)    
    
    except Exception as e:
        print("GOOGLEGA ULANMADI:", e)
