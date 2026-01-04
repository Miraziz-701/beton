# import requests
# from bs4 import BeautifulSoup

# def get_company_by_inn_orginfo(inn: str) -> dict | None:
#     url = f"https://orginfo.uz/search/all/?q={inn}"

#     headers = {
#         "User-Agent": "Mozilla/5.0"
#     }

#     resp = requests.get(url, headers=headers, timeout=10)
#     if resp.status_code != 200:
#         return None

#     soup = BeautifulSoup(resp.text, "html.parser")

#     # 🔹 Natija kartasi
#     card = soup.select_one("div.card")
#     if not card:
#         return None

#     # 🔹 INN badge
#     badge = card.select_one("span.badge")
#     if not badge or inn not in badge.text:
#         return None

#     # 🔹 KORXONA NOMI — TO‘G‘RI JOY
#     title = card.select_one(".card-title")
#     if not title:
#         return None

#     company_name = title.text.strip()

#     # 🔹 Manzil
#     address_tag = card.select_one("div.text-muted")
#     address = address_tag.text.strip() if address_tag else None

#     return {
#         "inn": inn,
#         "company_name": company_name,
#         "address": address
#     }

# print(get_company_by_inn_orginfo(302340873))

import requests
from bs4 import BeautifulSoup

def get_company_by_inn_orginfo(inn: str) -> dict | None:
    url = f"https://orginfo.uz/search/all/?q={inn}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code != 200:
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    # 🔹 Aynan INN yozilgan span'ni topamiz
    inn_span = soup.find("span", string=lambda x: x and inn in x)
    if not inn_span:
        return None

    # 🔹 Yuqoriga chiqib card'ni olamiz
    card = inn_span.find_parent("div", class_="card")
    if not card:
        return None

    # 🔹 Korxona nomi
    title = card.select_one("h6.card-title")
    if not title:
        return None

    # 🔹 Manzil
    address_tag = card.select_one("p.text-body-tertiary")
    address = address_tag.text.strip() if address_tag else None

    return {
        "inn": inn,
        "company_name": title.text.strip(),
        "address": address
    }


