# import requests
# from account.models import PriObyekts, NaqdObyekts
# from datetime import timedelta

# GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzcK7_TdtfpF_Huk474w8FP0JacM8SNpAThk5c527nmTl_jj4sQBG8hFgRoLQsy9ZFP/exec"



# def send_zakaz_to_google(zakaz):


#     number = zakaz.obyekt_id  # IntegerField

#     try:
#         if zakaz.tashkilot_nomi:
#             mijoz = zakaz.tashkilot_nomi.tashkilot_name
#             info = PriObyekts.objects.get(pk=number)
#             obyekt = info.obyekt_name
#             obyekt_address = info.location_name

#         else:
#             mijoz = zakaz.kim_tomonidan_jonatilgani.full_name
#             info = NaqdObyekts.objects.get(pk=number)
#             obyekt = info.obyekt_name
#             obyekt_address = info.location_name

#     except Exception as e:
#         print("OBYEKT TOPILMADI:", e)
#         return  # 👈 GOOGLEGA UMUMAN YUBORMAYMIZ

#     if zakaz.maxsulot_markasi:
#         marka_value = zakaz.maxsulot_markasi.markasi
    
#     else:
#         marka_value = zakaz.xomashyo.maxsulot_nomi

#     print(zakaz.qogozdagi_maxsulot_soni)
#     print(zakaz.mijoz_qoygan_narx)
#     print(zakaz.mijoz_jami_qoygan_narx)

#     payload = {
#         "agent": zakaz.kim_tomonidan_jonatilgani.full_name,
#         "sana": zakaz.date.strftime("%Y-%m-%d %H:%M"),
#         "mijoz": mijoz,
#         "marka": marka_value,
#         "obyekt": obyekt,
#         "mashina": zakaz.mashina.mashina_raqami,
#         "qogoz": zakaz.qogozdagi_maxsulot_soni,
#         "kuba": zakaz.mijoz_qoygan_narx,
#         "umumiy": zakaz.mijoz_jami_qoygan_narx,
#         "otkat": zakaz.xarajat_narxi,
#         "joy": obyekt_address
#     }

#     try:
#         resp = requests.post(
#             GOOGLE_SCRIPT_URL,
#             json=payload,
#             timeout=10
#         )
#         print("GOOGLE STATUS:", resp.status_code, resp.text)    
    
#     except Exception as e:
#         print("GOOGLEGA ULANMADI:", e)


# def delete_zakaz_from_google(zakaz):

#     sana = zakaz.date
#     start = sana - timedelta(minutes=1)
#     end = sana + timedelta(minutes=1)

#     payload = {
#         "action": "delete",
#         "start": start.strftime("%Y-%m-%d %H:%M:%S"),
#         "end": end.strftime("%Y-%m-%d %H:%M:%S")
#     }

#     try:
#         resp = requests.post(
#             GOOGLE_SCRIPT_URL,
#             json=payload,
#             timeout=10
#         )
#         print("GOOGLE DELETE:", resp.status_code, resp.text)

#     except Exception as e:
#         print("GOOGLE DELETE ERROR:", e)