from django.shortcuts import render, HttpResponseRedirect, redirect, get_object_or_404
from account.forms import (AdminLoginForm, AddProductForm, AddMijozForm, AddJonatuvchiForm,  AddKameraForm, 
AddObyektForm, AddBetonMarkaForm, AddXojayinForm, AddKirimForm, ChangeJonatuvchiForm, AddSkladProductsForm, 
AddYetkazibBeruvchiForm, AddRetseptForm, RetseptFormSet, AddChiqimForm, AddIshchiForm, AddKelmaganIshchilarForm, AddTestProductForm)
from django.contrib import auth, messages
from django.db.models.functions import Greatest
from dateutil.relativedelta import relativedelta
from django.urls import reverse
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from account.models import (Mijoz, Obyekt, Jonativchi, Kamera, Asosiy, BetonMarkasi, Mashina, Guruh, Kirim, KelmaganIshchilar, PriObyekts, NaqdObyekts, Agents,
KirimTuri, Retsept, SkladProducts, SementZavod, Sklad, SkladYetkazuvchi, ChiqimMashina, ChiqimTotal, ChiqimTuri, Ishchi, SkladRetsept, DetailXomashyo, Orders)
from django.http import JsonResponse
from django.db.models.functions import TruncDate
from collections import defaultdict
from django.utils.dateparse import parse_datetime
import pandas as pd
from django.core.files import File
from django.http import HttpResponse
from io import BytesIO
from django.utils.timezone import localtime
import cv2
from django.http import StreamingHttpResponse
from datetime import datetime 
from django.conf import settings
import os
import re
from django.db.models import Sum, F
from datetime import date, timedelta
from itertools import cycle
from aiogram import Bot
from django.conf import settings
import asyncio
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from django.db.models import Case, When, Value, IntegerField, Q
from django.utils import timezone
from django.apps import apps
from django.db.models.functions import Replace
from django.contrib.auth.decorators import user_passes_test
import json
from collections import OrderedDict
from django.db import transaction
from math import ceil


# Create your views here.
def login(request):
    if request.method == 'POST':
        form =  AdminLoginForm(data = request.POST)
        if form.is_valid():
            user_username = request.POST['username']
            user_password = request.POST['password']
            user = auth.authenticate(username = user_username, password = user_password)
            if user:
                auth.login(request, user)

                if user.is_superuser:
                    return HttpResponseRedirect(reverse('kassa_login'))

                return HttpResponseRedirect(reverse('home'))
    else:
        form = AdminLoginForm()
    context = {
        'form': form
    }
    return render(request, 'login.html', context)

@login_required
def home(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    selected_mashina = request.GET.get('mashina') or ''
    selected_marka = request.GET.get('marka')
    selected_mijoz = request.GET.get('mijoz')
    selected_jonatuvchi = request.GET.get('jonatuvchi')  
    selected_zavod = request.GET.get('zavod')  
    selected_obyekt = request.GET.get('obyekt') or ''
    selected_xojayini = request.GET.get('xojayini')

    queryset = Asosiy.objects.all()

    today = date.today()

    if from_date and to_date:
        queryset = queryset.filter(date__date__range=[from_date, to_date])
    elif from_date:
        queryset = queryset.filter(date__date=from_date)
    elif to_date:
        queryset = queryset.filter(date__date=to_date)
    
    if not any([from_date, to_date, selected_mijoz, selected_marka, selected_jonatuvchi, selected_zavod, selected_obyekt, selected_mashina, selected_xojayini]):
        queryset = queryset.filter(date__date=today)

    if selected_mashina:
        try:
            mashina_obj = Mashina.objects.get(mashina_raqami=selected_mashina)
            queryset = queryset.filter(mashina__id=mashina_obj.id)
        except Mashina.DoesNotExist:
            queryset = queryset.none() 

    if selected_marka:
        queryset = queryset.filter(maxsulot_markasi__id=selected_marka)
    
    if selected_mijoz:
        queryset = queryset.filter(mijoz_id=selected_mijoz)

    if selected_jonatuvchi:
        queryset = queryset.filter(kim_tomonidan_jonatilgani_id=selected_jonatuvchi)
    
    if selected_zavod:
        queryset = queryset.filter(kamera__id=selected_zavod)
    
    if selected_obyekt:
        try:
            queryset = queryset.filter(obyekt_nomi__obyekt_nomi=selected_obyekt)
        except Obyekt.DoesNotExist:
            queryset = queryset.none()

    mashinalar = Mashina.objects.all().order_by("mashina_raqami")
    
    if selected_xojayini:
        mashinalar_ids = Guruh.objects.filter(xojayini=selected_xojayini).values_list('mashinalar_id', flat=True)
        mashinalar = mashinalar.filter(id__in=mashinalar_ids)
        queryset = queryset.filter(mashina__id__in=mashinalar_ids)

    # Grouplash
    queryset = queryset.annotate(date_only=TruncDate('date')).order_by('-date')

    grouped = defaultdict(list)
    daily_totals = {}

    for item in queryset:
        grouped[item.date_only].append(item)
    
    for sana, items in grouped.items():
        umumiy = sum(i.maxsulot_soni for i in items)
        xomashyo = sum(i.maxsulot_soni for i in items if i.maxsulot_markasi is None)
        q_marka = sum(i.qogozdagi_maxsulot_soni for i in items if i.maxsulot_markasi is not None)
        r_marka = sum(i.maxsulot_soni for i in items if i.maxsulot_markasi is not None)

        daily_totals[sana] = {
            'umumiy': umumiy,
            'xomashyo': xomashyo,
            'q_marka': q_marka,
            'r_marka': r_marka
        }

    # Jami mahsulot hisoblash
    xomashyo_miqdor = queryset.filter(maxsulot_markasi__isnull=True).aggregate(
        total=Sum('maxsulot_soni')
    )['total'] or 0

    r_marka_miqdor = queryset.filter(maxsulot_markasi__isnull=False).aggregate(
        total=Sum('maxsulot_soni')
    )['total'] or 0

    q_marka_miqdor = queryset.filter(maxsulot_markasi__isnull=False).aggregate(
        total=Sum('qogozdagi_maxsulot_soni')
    )['total'] or 0

    umumiy_miqdor = queryset.aggregate(total=Sum('maxsulot_soni'))['total'] or 0

    # Marka ro‘yxati
    markalar = BetonMarkasi.objects.all()
    mijozlar = Mijoz.objects.all()
    jonatuvchilar = Jonativchi.objects.all()
    zavodlar = Kamera.objects.all()
    obyektlar = Obyekt.objects.all().order_by("obyekt_nomi")
    guruhlar = Guruh.objects.values_list('xojayini', flat=True).distinct()

    def pri_obyekt(self, tashkilot_nomi, obyekt_id):
        if tashkilot_nomi:
            PriObyekts.objects.get(pk=obyekt_id)
        else:
            NaqdObyekts.objects.get(pk=obyekt_id)

    return render(request, 'home.html', {
        'grouped_items': grouped.items(),
        'daily_totals': daily_totals,
        'selected_from': from_date,
        'selected_to': to_date,
        'selected_marka': selected_marka,
        'markalar': markalar,
        'mijozlar': mijozlar,
        'zavodlar': zavodlar,
        'guruhlar': guruhlar,
        'obyektlar': obyektlar,
        'mashinalar': mashinalar,
        'jonatuvchilar': jonatuvchilar,
        'umumiy_miqdor': umumiy_miqdor,
        'xomashyo_miqdor': xomashyo_miqdor,
        'real_marka_miqdor': r_marka_miqdor,
        'qogoz_marka_miqdor': q_marka_miqdor,
        'selected_mijoz': selected_mijoz,
        'selected_mashina': selected_mashina,
        'selected_jonatuvchi': selected_jonatuvchi,
        'selected_xojayini': selected_xojayini,
        'selected_zavod': selected_zavod,
        'selected_obyekt': selected_obyekt
    })
    

# --- FIFO: partiyalarni iste'mol qiladi; defitsit bo'lsa SkladRetseptga yangi batch yaratadi ---
def fifo_cost_and_consume(*, maxsulot, kerak_miqdor, zavod=None, when=None):
    """
    FIFO bo'yicha partiyalarni iste'mol qiladi va jami tan narxni qaytaradi.
    Yetmasa, oxirgi narx bo'yicha defitsit partiya yaratadi (qancha_qolgani=0).
    """
    if not kerak_miqdor or kerak_miqdor <= 0:
        return 0, []

    kerak_miqdor = Decimal(kerak_miqdor)
    when = when or timezone.now()

    qs = SkladRetsept.objects.filter(maxsulot=maxsulot)
    if zavod is not None:
        qs = qs.filter(zavod=zavod)
    qs = qs.order_by('olingan_sana', 'id')  # eng eski birinchi

    jami_tan_narx = 0
    consumed = []

    with transaction.atomic():
        batches = list(qs.select_for_update())
        kerak = kerak_miqdor

        for b in batches:
            if kerak <= 0:
                break
            
            available = Decimal(str(b.qancha_qolgani or 0))
            
            if available <= 0:
                continue

            take = min(kerak, available)
            
            take = Decimal(take)
            narx = Decimal(str(b.narxi_donasi)) 
            
            jami_tan_narx += take * narx
            
            take = Decimal(str(take))

            b.qancha_qolgani = available - take
            b.save(update_fields=['qancha_qolgani'])

            consumed.append({
                "batch_id": b.id,
                "maxsulot": str(maxsulot),   # 🔹 Mahsulot nomini qo‘shdik
                "olingan_sana": b.olingan_sana,
                "narxi_donasi": float(b.narxi_donasi),
                "olingan": take,
                "is_deficit": False,
            })
            kerak -= take

        if kerak > 0:
            # Oxirgi narxni topamiz
            price_qs = SkladRetsept.objects.filter(maxsulot=maxsulot)
            if zavod is not None:
                price_qs = price_qs.filter(zavod=zavod)
            price_qs = price_qs.order_by('-olingan_sana', '-id')
            
            last_price = 0
            
            for p in price_qs.values_list('narxi_donasi', flat=True):
                if p and float(p) > 0:   # 0 yoki None bo‘lsa tashlab ketadi
                    last_price = float(p)
                    break

            # Defitsit uchun partiya (darhol iste'mol qilingan)
            new_batch = SkladRetsept.objects.create(
                maxsulot=maxsulot,
                zavod=zavod,
                keltirilgan_miqdor=kerak,
                qancha_qolgani=0,
                narxi_donasi=last_price,
                olingan_sana=when,
            )
            
            last_price = Decimal(str(last_price))
            
            jami_tan_narx += kerak * last_price
            consumed.append({
                "batch_id": new_batch.id,
                "maxsulot": str(maxsulot),   # 🔹 Mahsulot nomini qo‘shdik
                "olingan_sana": new_batch.olingan_sana,
                "narxi_donasi": last_price,
                "olingan": kerak,
                "is_deficit": True,
            })

    return jami_tan_narx, consumed

# @login_required 
# @user_passes_test(lambda u: u.is_superuser, login_url='login') 
# def xaridordan_kirim_hisobot(request): 
#     if request.method == 'POST': 
#         try: 
#             data = json.loads(request.body) 
#             zakaz_id = data.get("zakaz_id")
#             pul = data.get("pul") 
#             pul_turi = data.get("turi") 
#             sana = data.get("sana") # frontdan keladi 
#             narx = data.get("narx") # yangi qo‘shilgan
            
#             zakaz = get_object_or_404(Asosiy, id=zakaz_id) 
            
#             # Sana tanlangan bo‘lsa yoki tanlanmasa 
#             if sana: 
#                 parsed = datetime.strptime(sana, "%Y-%m-%dT%H:%M") 
#                 if parsed == zakaz.date.replace(tzinfo=None): 
#                     sana = timezone.now() 
#                 elif timezone.is_naive(parsed): 
#                     sana = timezone.make_aware(parsed) 
            
#             else: 
#                 sana = timezone.now() 
                
#             # 1️⃣ Agar narx kiritilgan bo‘lsa — yangilash 
#             if narx: 
#                 mijoz_narx = float(narx) 
#                 zakaz.mijoz_qoygan_narx = mijoz_narx 
#                 zakaz.mijoz_jami_qoygan_narx = zakaz.qogozdagi_maxsulot_soni * mijoz_narx 
#                 zakaz.mijoz_narx_qoyildi = True 
#                 zakaz.save() 
                
#             # 2️⃣ Agar pul kiritilgan bo‘lsa — Kirim yozish 
#             if pul:
#                 k_turi = get_object_or_404(KirimTuri, kirim_nomi="Xaridordan kirim") 
#                 Kirim.objects.create( 
#                     turi=k_turi, 
#                     k_o_kelgani=zakaz.kim_tomonidan_jonatilgani, 
#                     summa=float(pul), 
#                     izoh=f"{zakaz.mijoz} {zakaz.mashina}", 
#                     checked=pul_turi, sana=sana 
#                 ) 
#                 zakaz.mijoz_bergan_narx += float(pul) 
#                 zakaz.save() 

#             return JsonResponse({"success": True}) 
            
#         except Exception as e: 
#             return JsonResponse({"success": False, "error": str(e)}) 
#     # Faqat narx qo‘yilmagan yoki to‘liq pul berilmaganlarni chiqarish 
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     selected_xaridor = request.GET.get('xaridor') or ''

    
#     zakazlar = Asosiy.objects.filter(
#         Q(haydovchi_narx_qoyildi=False) |                        
#         Q(mijoz_narx_qoyildi=False) |                            
#         ~Q(mijoz_jami_qoygan_narx=F('mijoz_bergan_narx'))
#     ).order_by("-date")

#     if from_date and to_date:
#         zakazlar = zakazlar.filter(date__date__range=[from_date, to_date])

#     elif from_date:
#         zakazlar = zakazlar.filter(date__date=from_date)
    
#     elif to_date:
#         zakazlar = zakazlar.filter(date__date=to_date)
    
#     if selected_xaridor:
#         try:
#             zakazlar = zakazlar.filter(mijoz__ism_familya=selected_xaridor)
#         except Mijoz.DoesNotExist:
#             zakazlar = zakazlar.none()


#     for zakaz in zakazlar: 
#         zakaz.qoldiq = zakaz.mijoz_jami_qoygan_narx - zakaz.mijoz_bergan_narx 

#         zakaz.umumiy_tan_narx = zakaz.maxsulot_tan_narx + zakaz.haydovchi_qoygan_narx  

#         zakaz.foyda = zakaz.mijoz_jami_qoygan_narx - zakaz.umumiy_tan_narx

#         start = zakaz.date - timedelta(minutes=1)
#         end   = zakaz.date + timedelta(minutes=1)

#         zakaz.detallar = DetailXomashyo.objects.filter(
#             maxsulot=zakaz.maxsulot_markasi,
#             vaqti__range=(start, end)
#         ).select_related("xomashyo")
    
#     umumiy_berilgan_summa = zakazlar.aggregate(total=Sum('mijoz_bergan_narx'))['total'] or 0
#     umumiy_summa = zakazlar.aggregate(total=Sum('mijoz_jami_qoygan_narx'))['total'] or 0
#     umumiy_qarzlar = sum(z.mijoz_jami_qoygan_narx - z.mijoz_bergan_narx for z in zakazlar)
#     umumiy_foyda = sum((z.mijoz_jami_qoygan_narx - (z.maxsulot_tan_narx + z.haydovchi_qoygan_narx)) for z in zakazlar)
#     xaridorlar = Mijoz.objects.all()

#     context = {
#         'zakazlar': zakazlar,
#         'umumiy_berilgan_summa': umumiy_berilgan_summa,
#         'umumiy_qarzlar': umumiy_qarzlar,
#         'umumiy_summa': umumiy_summa,
#         'umumiy_foyda': umumiy_foyda,
#         'xaridorlar': xaridorlar,
#         'selected_xaridor': selected_xaridor,
#         'selected_from': from_date,
#         'selected_to': to_date
#     }
                
#     return render(request, 'xaridordan_kirim.html', context)

@login_required
def xaridordan_kirim_hisobot(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    selected_xaridor = request.GET.get('xaridor')


    zakazlar = Asosiy.objects.all().order_by('-date')


    if from_date and to_date:
        zakazlar = zakazlar.filter(date__date__range=[from_date, to_date])

    elif from_date:
        zakazlar = zakazlar.filter(date__date=from_date)

    elif to_date:
        zakazlar = zakazlar.filter(date__date=to_date)
    
    if selected_xaridor:
        try:
            zakazlar = zakazlar.filter(mijoz__ism_familya=selected_xaridor)
        except Mijoz.DoesNotExist:
            zakazlar = zakazlar.none()


    jami_summa = zakazlar.aggregate(total=Sum('mijoz_jami_qoygan_narx'))['total'] or 0
    jami_berilgan_summa = zakazlar.aggregate(total=Sum('mijoz_bergan_narx'))['total'] or 0
    jami_qolgan_summa = zakazlar.aggregate(total=Sum(F('mijoz_jami_qoygan_narx') - F('mijoz_bergan_narx')))['total'] or 0
    jami_foyda_summa = zakazlar.aggregate(total=Sum(F('mijoz_jami_qoygan_narx') - F('maxsulot_tan_narx')))['total'] or 0
    xaridorlar = Mijoz.objects.all().order_by('ism_familya')


    context = {
        'zakazlar': zakazlar,
        'xaridorlar': xaridorlar,
        'selected_xaridor': selected_xaridor,
        'jammi_mijoz_summa': jami_summa,
        'jammi_berilgan_summa': jami_berilgan_summa,
        'jami_qolgan_summa': jami_qolgan_summa,
        'jami_foyda': jami_foyda_summa,
        'selected_from': from_date,
        'selected_to': to_date
    }

    return render(request, 'kirim_xaridor.html', context)

@login_required
def set_mijoz_narx(request, zakaz_id):
    mijoz_narx = request.GET.get('mijoz_narx', '0').replace(" ", "")

    zakaz = Asosiy.objects.get(id=zakaz_id)
    zakaz.mijoz_qoygan_narx = int(mijoz_narx)
    zakaz.mijoz_jami_qoygan_narx = zakaz.qogozdagi_maxsulot_soni * int(mijoz_narx)
    zakaz.mijoz_narx_qoyildi = True
    zakaz.save()

    qolgan_summa = zakaz.mijoz_jami_qoygan_narx - zakaz.mijoz_bergan_narx

    return JsonResponse({
        'success': True,
        'mijoz_qoygan_narx': zakaz.mijoz_qoygan_narx,
        'jami': zakaz.mijoz_jami_qoygan_narx,
        'qolgan': qolgan_summa
    })

@login_required
def add_otkat(request, zakaz_id):
    zakaz = Asosiy.objects.get(id=zakaz_id)

    if request.method == 'POST':
        otkat_narxi = request.POST.get('narx').replace(" ", "")
        otkat_izoh = request.POST.get('izoh') or ''
        
        zakaz.xarajat_narxi += int(otkat_narxi)
        zakaz.xarajat_izohi = otkat_izoh
        zakaz.maxsulot_tan_narx += int(otkat_narxi)
        zakaz.qoshimcha_xarajat = True
        zakaz.save()
        return redirect('xaridor_kirim')   
  
    context = {
        'zakaz': zakaz
    }


    return render(request, 'add_otkat.html', context)

@login_required
def enter_mijoz_summa(request, zakaz_id):

    zakaz = Asosiy.objects.get(id=zakaz_id)


    if request.method == 'POST':
        tolov_turi = request.POST.get('tolov_turi')
        summa = request.POST.get('summa').replace(" ", "")
        izoh = request.POST.get('izoh') or ''
        sana = request.POST.get('sana')

        kirim_turi = KirimTuri.objects.get(kirim_nomi = 'Xaridordan kirim')

        if not sana:
            sana = timezone.now()

        Kirim.objects.create(
            turi=kirim_turi,
            k_o_kelgani=zakaz.kim_tomonidan_jonatilgani,
            summa=summa,
            izoh=izoh,
            checked=tolov_turi,
            sana=sana
        )

        zakaz.mijoz_bergan_narx += int(summa)

        zakaz.save()

        return redirect('xaridor_kirim')


    context = {
        'zakaz': zakaz
    }




    return render(request, 'enter_money.html', context)


@login_required
def maxsulot_tan_narx(request, zakaz_id):
    zakaz = Asosiy.objects.get(id=zakaz_id)

    start = zakaz.date - timedelta(minutes=1)
    end = zakaz.date + timedelta(minutes=1)

    details = DetailXomashyo.objects.filter(vaqti__range=(start, end))

    data = []
    for detail in details:
        data.append({
            "nomi": str(detail.xomashyo),   
            "miqdor": float(detail.miqdori),
            "narx_donasi": float(detail.narxi_donasi),
            "jami_narxi": float(detail.total_narx),
            "vaqti": detail.vaqti.strftime("%d-%m-%Y %H:%M")
        })

    return JsonResponse({
        "details": data,
        "haydovchi_narx": zakaz.haydovchi_qoygan_narx,
        "otkat_narx": zakaz.xarajat_narxi,
        "otkat_izoh": zakaz.xarajat_izohi or ""
    })

    # context = {
    #     'zakaz': zakaz,
    #     'details': details
    # }




@login_required
def add_ortiqcha_xarajat(request, zakaz_id):
    zakaz = get_object_or_404(Asosiy, id=zakaz_id)

    if request.method == "POST":
        data = json.loads(request.body)
        
        xarajat_narxi_str = str(data.get("xarajat_narxi", "0")).replace(" ", "")
        xarajat_narxi = int(xarajat_narxi_str)   # faqat butun son saqlanadi

        xarajat_izohi = data.get("xarajat_izoh") or None

        zakaz.qoshimcha_xarajat = True
        zakaz.xarajat_narxi = xarajat_narxi
        zakaz.xarajat_izohi = xarajat_izohi
        zakaz.maxsulot_tan_narx += xarajat_narxi
        zakaz.save()

        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "POST kerak"})


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='login')
def haydovchi_chiqim(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    selected_obyekt = request.GET.get('obyekt') or ''
    selected_mashina = request.GET.get('mashina') or ''

    malumotlar = Asosiy.objects.annotate(
        qolgan_qarz=F('haydovchi_qoygan_narx') - F('haydovchiga_berilgan_narx')
    ).filter(
        Q(haydovchi_narx_qoyildi=False) | ~Q(haydovchi_qoygan_narx=F('haydovchiga_berilgan_narx'))
    ).order_by('-date')
    
    if from_date and to_date:
        malumotlar = malumotlar.filter(date__date__range=[from_date, to_date])
    
    elif from_date:
        malumotlar = malumotlar.filter(date__date=from_date)
    
    elif to_date:
        malumotlar = malumotlar.filter(date__date=to_date)

    if selected_obyekt:
        try:
            malumotlar = malumotlar.filter(obyekt_nomi__obyekt_nomi=selected_obyekt)
        except Obyekt.DoesNotExist:
            malumotlar = malumotlar.none()
    
    if selected_mashina:
        try:
            malumotlar = malumotlar.filter(mashina__mashina_raqami=selected_mashina)
        except Mashina.DoesNotExist:
            malumotlar = malumotlar.none() 


    obyektlar = Obyekt.objects.all().order_by('obyekt_nomi')
    mashinalar = Mashina.objects.all().order_by('mashina_raqami')
    guruhlar = Guruh.objects.all()
    umumiy_qarzlar = malumotlar.aggregate(total=Sum('qolgan_qarz'))['total'] or 0
    umumiy_berilgan = malumotlar.aggregate(total=Sum('haydovchiga_berilgan_narx'))['total'] or 0
    umumiy_summa = malumotlar.aggregate(total=Sum('haydovchi_qoygan_narx'))['total'] or 0

    context = {
        'datas': malumotlar,
        'guruhlar': guruhlar,
        'selected_from': from_date,
        'selected_to': to_date,
        'umumiy_qarzlar': umumiy_qarzlar,
        'umumiy_berilgan_summa': umumiy_berilgan,
        'jami_summa': umumiy_summa,
        'selected_obyekt': selected_obyekt,
        'selected_mashina': selected_mashina,
        'obyektlar': obyektlar,
        'mashinalar': mashinalar
    }

    return render(request, 'chiqim_list.html', context)


@login_required
def change_haydovchi_narx(request, pk):
    if request.method == "POST":
        try:
            haydovchi_narx = request.POST.get("narx")
            if not haydovchi_narx or not haydovchi_narx.isdigit():
                return JsonResponse({'status': 'error', 'message': 'Faqat raqam kiriting'})

            haydovchi_narx = int(haydovchi_narx)

            item = Asosiy.objects.get(id=pk)
            item.haydovchi_qoygan_narx = haydovchi_narx
            item.haydovchi_narx_qoyildi = True
            item.maxsulot_tan_narx += haydovchi_narx
            item.save()

            qarz = item.haydovchi_qoygan_narx - item.haydovchiga_berilgan_narx

            return JsonResponse({
                'status': 'ok',
                'new_value': item.haydovchi_qoygan_narx,
                'qarz': qarz
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'POST emas'})



@login_required
def add_haydovchi_narx(request, pk):
    if request.method == "POST":
        zavod_bergan_narx = request.POST.get('haydovchi_narx', '').strip()
        tolangan_vaqt = request.POST.get('vaqt')
        tolov_turi = request.POST.get('np')

        if tolangan_vaqt:
            tolangan_vaqt = parse_datetime(tolangan_vaqt)
        else:
            tolangan_vaqt = timezone.now()

        if not zavod_bergan_narx.isdigit():
            return JsonResponse({'status': 'error', 'message': 'Faqat raqam kiriting'})

        narx_int = int(zavod_bergan_narx)

        detail = Asosiy.objects.get(id=pk)

        # 🟢 Oldin o'zgaruvchida saqlaymiz
        berilgan_jami = detail.haydovchiga_berilgan_narx + narx_int
        qarz = detail.haydovchi_qoygan_narx - berilgan_jami

        # 🟢 Keyin bazaga saqlaymiz
        detail.haydovchiga_berilgan_narx = berilgan_jami
        detail.save()

        try:
            egasi = Guruh.objects.get(mashinalar=detail.mashina)
        except Guruh.DoesNotExist:
            egasi = None

        ChiqimMashina.objects.create(
            mashina_raqami=detail.mashina,
            mijoz=detail.mijoz,
            obyekt_nomi=detail.obyekt_nomi,
            mashina_egasi=egasi,
            berilgan_narx=narx_int,
            zavod=detail.kamera,
            tolov_turi=tolov_turi,
            vaqt=tolangan_vaqt
        )

        chiqim_nomi = ChiqimTuri.objects.get(chiqim_nomi="Haydovchiga")

        ChiqimTotal.objects.create(
            chiqim_turi=chiqim_nomi,
            mijoz=detail.mijoz,
            maxsulot_markasi = detail.maxsulot_markasi,
            miqdori=detail.qogozdagi_maxsulot_soni,
            k_kelgani=detail.kim_tomonidan_jonatilgani,
            summa=narx_int,
            mashina_raqami=detail.mashina,
            mashina_egasi=egasi,
            tolov_turi=tolov_turi,
            zavod=detail.kamera,
            vaqti=tolangan_vaqt
        )



        return JsonResponse({
            'status': 'ok',
            'new_value': detail.haydovchiga_berilgan_narx,
            'qarz': detail.haydovchi_qoygan_narx - detail.haydovchiga_berilgan_narx,
            'tolov_turi': tolov_turi       # <-- BUNI QO‘SHING
        })

    return JsonResponse({'status': 'error', 'message': 'POST bo‘lmagan so‘rov'})

@login_required
def add_chiqim(request):
    if request.method == 'POST':
        form = AddChiqimForm(data=request.POST)
        if form.is_valid():
            chiqim = form.save(commit=False)

            if chiqim.ishchi:
                # chiqim sanasini olish
                chiqim_sana = chiqim.vaqti.date()

                # shu sanaga to‘g‘ri keladigan ishchini topamiz
                ishchi = Ishchi.objects.filter(
                    ism_familya=chiqim.ishchi.ism_familya,
                    qachondan_olishi__lte=chiqim_sana
                ).order_by('-qachon_tugashi').first()

                if ishchi:
                    if chiqim_sana > ishchi.qachon_tugashi:
                        # agar shu oy uchun yozuv bo‘lmasa yangi ochiladi
                        oxirgi = Ishchi.objects.filter(
                            ism_familya=chiqim.ishchi.ism_familya
                        ).order_by('-qachon_tugashi').first()

                        Ishchi.objects.create(
                            ism_familya=oxirgi.ism_familya,
                            oyligi=oxirgi.oyligi,
                            qachondan_olishi=chiqim_sana.replace(day=1),
                            qachon_tugashi=(chiqim_sana.replace(day=1) + relativedelta(months=1)) - timedelta(days=1),
                            jami_beriladigan_summa = oxirgi.oyligi,
                            berilgan_puli=chiqim.summa
                        )
                    else:
                        # mavjud oyning ishchisiga pul qo‘shiladi
                        ishchi.berilgan_puli += chiqim.summa
                        ishchi.save()
                
                

            chiqim.save()
            return redirect('umumiy_chiqim')
        else:
            print(form.errors)
    else:
        form = AddChiqimForm()

    context = {
        'form': form
    }
    return render(request, 'add_chiqim.html', context)

@login_required
def ishchilar_davomati(request):
    kelmaganlar = KelmaganIshchilar.objects.all().order_by('-sana')

    context = {
        'kelmaganlar': kelmaganlar
    }

    return render(request, 'ishchilar_davomati.html', context)

@login_required
def add_ishchi(request):
    if request.method == 'POST':
        form = AddIshchiForm(data=request.POST)
        if form.is_valid():
            ishchi = form.save(commit=False)
            if not ishchi.qachondan_olishi:
                ishchi.qachondan_olishi = timezone.now().date()
            ishchi.jami_beriladigan_summa = ishchi.oyligi
            ishchi.save()
            return redirect('ishchilar_royxati')
        else:
            print(form.errors)
    else:
        form = AddIshchiForm()

    return render(request, 'add_ishchi.html', {'form': form})

@login_required
def ishchilar_royxati(request):
    ishchilar_detail = Ishchi.objects.all().order_by('-qachon_tugashi')

    for ishchi in ishchilar_detail:
        ishchi.qarz = ishchi.jami_beriladigan_summa - ishchi.berilgan_puli

    context = {
        'ishchilar': ishchilar_detail
    }

    return render(request, 'ishchilar_royxati.html', context)

@login_required
def add_kelmagan_ishchilar(request):
    if request.method == 'POST':
        form = AddKelmaganIshchilarForm(data=request.POST)
        if form.is_valid():
            kelmagan = form.save(commit=False)
            if not kelmagan.sana:   
                kelmagan.sana = timezone.now().date()
            kelmagan.save()

            ishchi_detail = Ishchi.objects.filter(
                    ism_familya=kelmagan.ishchi.ism_familya,
                    qachondan_olishi__lte=kelmagan.sana
                ).order_by('-qachon_tugashi').first()
            
            if kelmagan.sana > ishchi_detail.qachon_tugashi: 
                oxirgi = Ishchi.objects.filter(
                            ism_familya=kelmagan.ishchi.ism_familya
                        ).order_by('-qachon_tugashi').first()
                bir_kunlik_kemagan = oxirgi.oyligi / 30
                Ishchi.objects.create( 
                    ism_familya = oxirgi.ism_familya, 
                    oyligi = oxirgi.oyligi, 
                    qachondan_olishi = kelmagan.sana.replace(day=1),
                    qachon_tugashi = (kelmagan.sana.replace(day=1) + relativedelta(months=1)) - timedelta(days=1),
                    kelmagan_kuni = 1,
                    jami_beriladigan_summa = oxirgi.oyligi - bir_kunlik_kemagan
                )

            else:
                ishchi_detail.kelmagan_kuni += 1 
                bir_kunlik_kemagan = ishchi_detail.oyligi / 30
                ishchi_detail.jami_beriladigan_summa -= bir_kunlik_kemagan
                ishchi_detail.save()

            return redirect('ishchilar_davomati')
        else:
            print(form.errors)
    else:
        form = AddKelmaganIshchilarForm()


    context = {
        'form': form
    }


    return render(request, 'add_kelmagan_ishchilar.html', context)


@login_required
def umumiy_chiqim(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    selected_chiqim = request.GET.get('chiqim_turi')

    chiqimlar = ChiqimTotal.objects.all().order_by('-vaqti')
    yetkazuvchilar = SkladYetkazuvchi.objects.all()

    if from_date and to_date:
        chiqimlar = chiqimlar.filter(vaqti__date__range=[from_date, to_date])

    elif from_date:
        chiqimlar = chiqimlar.filter(vaqti__date=from_date)
    
    elif to_date:
        chiqimlar = chiqimlar.filter(vaqti__date=to_date)
    
    if selected_chiqim:
        chiqimlar = chiqimlar.filter(chiqim_turi__id=selected_chiqim)
    

    qarzlar = []
    for yetkazuvchi in yetkazuvchilar:
        jami_summa = (
            Sklad.objects.filter(yetkazuvchi=yetkazuvchi)
            .aggregate(total=Sum('jami_maxsulot_narxi'))['total'] or 0
        )
        jami_chiqim = (
            ChiqimTotal.objects.filter(yetkazuvchi=yetkazuvchi)
            .aggregate(total=Sum('summa'))['total'] or 0
        )
        qarz = jami_summa - jami_chiqim
        qarzlar.append((yetkazuvchi, qarz))

    chiqim_turlari = ChiqimTuri.objects.all()
    umumiy_miqdor = chiqimlar.aggregate(total=Sum('summa'))['total'] or 0


    context = {
        'umumiy_chiqimlar': chiqimlar,
        'qarzlar': qarzlar,
        'chiqim_turlari': chiqim_turlari,
        'selected_from': from_date,
        'selected_to': to_date,
        'selected_chiqim': selected_chiqim,
        'umumiy_miqdor': umumiy_miqdor
    }

    return render(request, 'umumiy_chiqim.html', context)


@login_required
def chiqim_hisobot(request):
    chiqimlar = ChiqimMashina.objects.all().order_by('-vaqt')

    context = {
        'chiqimlar': chiqimlar
    }

    return render(request, 'chiqim_hisobot.html', context) 




@login_required
def guruh_mashina_qoshish(request, xojayin_id):
    guruh = Guruh.objects.get(id=xojayin_id)

    if request.method == "POST":
        mashina_raqami = request.POST.get("mashina").strip().upper()

        mashina_obj, _ = Mashina.objects.get_or_create(mashina_raqami=mashina_raqami)

        # 1️⃣ Shu xojayinda shu mashina borligini tekshirish
        if Guruh.objects.filter(xojayini=guruh.xojayini, mashinalar=mashina_obj).exists():
            return redirect("guruh_list")

        # 2️⃣ Shu mashina boshqa xojayinda mavjudligini tekshirish
        if Guruh.objects.filter(mashinalar=mashina_obj).exclude(xojayini=guruh.xojayini).exists():
            return redirect("guruh_list")

        # Qo‘shish
        if guruh.mashinalar is None:
            guruh.mashinalar = mashina_obj
            guruh.save()
        else:
            Guruh.objects.create(xojayini=guruh.xojayini, mashinalar=mashina_obj)

        return redirect("guruh_list")
    

    mashinalar = Mashina.objects.all().order_by("mashina_raqami")
    context = {
        "guruh": guruh,
        "mashinalar": mashinalar
    }
    return render(request, "add_mashina.html", context)



@login_required
def guruhlar_list(request):
    rows = []
    owners = Guruh.objects.values_list('xojayini', flat=True).distinct()
    for name in owners:
        # ko‘rsatish uchun mashinalar
        mashinalar_qs = Guruh.objects.filter(xojayini=name, mashinalar__isnull=False).select_related('mashinalar')
        mashinalar = [g.mashinalar for g in mashinalar_qs]

        # link uchun ishlatadigan id: avval bo‘sh slot bo‘lsa o‘shani olamiz, bo‘lmasa birortasini
        slot = Guruh.objects.filter(xojayini=name, mashinalar__isnull=True).first()
        any_pk = slot.id if slot else Guruh.objects.filter(xojayini=name).values_list('id', flat=True).first()

        rows.append({'name': name, 'pk': any_pk, 'mashinalar': mashinalar})

    return render(request, 'guruhlar_list.html', {'rows': rows})



@login_required
def add_xojayin(request):
    if request.method == 'POST':
        form = AddXojayinForm(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect("guruh_list")
        else:
            print(form.errors)
    else:
        form = AddXojayinForm()
    
    context = {
        'form': form
    }
    return render(request, 'add_xojayin.html', context)

@login_required
def toggle_selected(request, pk):
    item = get_object_or_404(Asosiy, pk=pk)
    item.checked = True            # siz xohlagan holat
    item.all_checked = True
    item.save(update_fields=["checked", "all_checked"])
    return JsonResponse({"status": "ok", "checked": item.checked, "all_checked": item.all_checked})

# @login_required
# def toggle_selected(request, pk):
#     with transaction.atomic():
#         # 0) Zakazni lock qilamiz
#         item = Asosiy.objects.select_for_update().get(pk=pk)

#         # Toggle
#         item.checked = not item.checked
#         item.save(update_fields=["checked"])

#         # all_checked True bo‘lsa — qayta sarf/yozish yo‘q
#         if item.all_checked:
#             return JsonResponse({'status': 'skipped', 'selected': item.checked})
            
#         if item.xomashyo and not item.maxsulot_markasi:
#             sklad = SkladProducts.objects.select_for_update().get(pk=item.xomashyo.pk)

#             # sement bo‘lsa zavod bo‘yicha mavjud miqdor, bo‘lmasa umumiy soni
#             if "sement" in (item.xomashyo.maxsulot_nomi or "").lower():
#                 sz, _ = SementZavod.objects.get_or_create(
#                     sement_nomi=item.xomashyo,
#                     zavod=item.kamera,
#                     defaults={"sement_miqdori": 0}
#                 )
#                 mavjud = sz.sement_miqdori
#                 last_prices = (
#                     Sklad.objects.filter(maxsulot_nomi=item.xomashyo, zavod=item.kamera)
#                     .order_by("-sana", "-id")
#                     .values_list("maxsulot_narxi", flat=True)
#                 )
#             else:
#                 mavjud = sklad.soni
#                 last_prices = (
#                     Sklad.objects.filter(maxsulot_nomi=item.xomashyo)
#                     .order_by("-sana", "-id")
#                     .values_list("maxsulot_narxi", flat=True)
#                 )

#             # narxni topish
#             oxirgi_narx = 0
#             for price in last_prices:
#                 if price and price > 0:
#                     oxirgi_narx = price
#                     break

#             # ✅ Yetarli bo‘lsa kamaytirish
#             if mavjud >= item.maxsulot_soni:
#                 if "sement" in (item.xomashyo.maxsulot_nomi or "").lower():
#                     SementZavod.objects.filter(pk=sz.pk).update(
#                         sement_miqdori=F("sement_miqdori") - float(item.maxsulot_soni)
#                     )   
#                 else:
#                     SkladProducts.objects.filter(pk=sklad.pk).update(
#                         soni=F("soni") - float(item.maxsulot_soni)
#                     )

#                 DetailXomashyo.objects.create(
#                     maxsulot=None,
#                     xomashyo=item.xomashyo,
#                     izoh=item.xomashyo_izohi,
#                     miqdori=item.maxsulot_soni,
#                     narxi_donasi=oxirgi_narx,
#                     total_narx=item.maxsulot_soni * oxirgi_narx,
#                     zavod=item.kamera,
#                     vaqti=item.date
#                 )
#                 item.maxsulot_tan_narx = item.maxsulot_soni * oxirgi_narx

#             else:
#                 # ❌ Yetarli emas → defitsit
#                 kerak = item.maxsulot_soni - mavjud

#                 # mavjud qismni nolga tushirib yuboramiz
#                 if "sement" in (item.xomashyo.maxsulot_nomi or "").lower():
#                     SementZavod.objects.filter(pk=sz.pk).update(
#                         sement_miqdori = F("sement_miqdori") - float(item.maxsulot_soni)
#                     )

#                 else:
#                     SkladProducts.objects.filter(pk=sklad.pk).update(
#                         soni = F("soni") - float(item.maxsulot_soni)
#                     )

#                 DetailXomashyo.objects.create(
#                     maxsulot=None,
#                     xomashyo=item.xomashyo,
#                     izoh=item.xomashyo_izohi,
#                     miqdori=mavjud,
#                     narxi_donasi=oxirgi_narx,
#                     total_narx=mavjud * oxirgi_narx,
#                     zavod=item.kamera,  
#                     vaqti=item.date
#                 )

#                 # 🔥 Defitsit ham yoziladi
#                 DetailXomashyo.objects.create(
#                     maxsulot=None,
#                     xomashyo=item.xomashyo,
#                     izoh=item.xomashyo_izohi,
#                     miqdori=kerak,
#                     narxi_donasi=oxirgi_narx,
#                     total_narx=kerak * oxirgi_narx,
#                     zavod=item.kamera,
#                     vaqti=item.date
#                 )

#                 # Avto-kirim yozish
#                 # yetkazuvchi_obj, _ = SkladYetkazuvchi.objects.get_or_create(
#                 #     yetkazib_beruvchi=item.kamera.kamera_nomi
#                 # )
#                 # Sklad.objects.create(
#                 #     maxsulot_nomi=item.xomashyo,
#                 #     maxsulot_miqdori=kerak,
#                 #     maxsulot_narxi=oxirgi_narx,
#                 #     jami_maxsulot_narxi=kerak * oxirgi_narx,
#                 #     tolov_turi='N',
#                 #     yetkazuvchi=yetkazuvchi_obj,
#                 #     zavod=item.kamera,
#                 #     izoh=f"Avtomatik defitsit (Zakaz ID: {item.pk})",
#                 #     sana=timezone.now(),
#                 # )

#                 item.maxsulot_tan_narx = item.maxsulot_soni * oxirgi_narx

#             item.tan_narxi_qoyildi = True
#             item.all_checked = True
#             item.save(update_fields=["maxsulot_tan_narx", "tan_narxi_qoyildi", "all_checked"])

#             return JsonResponse({
#                 'status': 'ok',
#                 'selected': item.checked,
#                 'jami_tan_narx': item.maxsulot_tan_narx
#             })
        

#         # 1) Oxirgi retsept vaqtini topamiz (shu marka bo‘yicha)
#         oxirgi_vaqt = (
#             Retsept.objects
#             .filter(retsept_nomi=item.maxsulot_markasi)
#             .order_by('-date')
#             .values_list('date', flat=True)
#             .first()
#         )
#         if not oxirgi_vaqt:
#             return JsonResponse({'status': 'error', 'message': 'Retsept topilmadi'}, status=404)

#         start = oxirgi_vaqt - timedelta(minutes=1)
#         end   = oxirgi_vaqt + timedelta(minutes=1)

#         # 2) Shu retsept_nomi + vaqt oralig‘idagi barcha yozuvlar
#         toliq_guruh = list(
#             Retsept.objects
#             .filter(retsept_nomi=item.maxsulot_markasi, date__range=(start, end))
#             .select_related("maxsulot")
#         )
#         if not toliq_guruh:
#             return JsonResponse({'status': 'error', 'message': 'Retsept tarkibi topilmadi'}, status=404)

#         # 3) Retseptni mahsulot bo‘yicha JAMLAYMIZ (duplikatlar yo‘qolsin)
#         needs = {}     # key = (product_pk, is_sement) -> jami_kerak (int)
#         prod_map = {}  # product_pk -> SkladProducts instance
#         for r in toliq_guruh:
#             maxsulot_obj = r.maxsulot
#             is_sement = "sement" in (maxsulot_obj.maxsulot_nomi or "").lower()
#             kerak_miqdor = Decimal(r.miqdor) * Decimal(item.maxsulot_soni)
#             key = (maxsulot_obj.pk, is_sement)
#             needs[key] = needs.get(key, 0) + float(kerak_miqdor)
#             prod_map[maxsulot_obj.pk] = maxsulot_obj

#         # 4) FIFO bo‘yicha sarf (SkladRetsept dan kamayadi; defitsit bo‘lsa SkladRetseptga yangi batch)
#         jami_tan_narxi = 0
#         for (prod_pk, is_sement), jami_kerak in needs.items():
#             maxsulot_obj = prod_map[prod_pk]

#             if is_sement:
#                 total_cost, details = fifo_cost_and_consume(
#                     maxsulot=maxsulot_obj,
#                     kerak_miqdor=jami_kerak,
#                     zavod=item.kamera,    # sementlar zavod kesimida
#                     when=oxirgi_vaqt
#                 )
#             else:
#                 total_cost, details = fifo_cost_and_consume(
#                     maxsulot=maxsulot_obj,
#                     kerak_miqdor=jami_kerak,
#                     zavod=None,
#                     when=oxirgi_vaqt
#                 )
            
#             for d in details:
#                 DetailXomashyo.objects.create(
#                     maxsulot=item.maxsulot_markasi,   # qaysi beton markasi
#                     xomashyo=maxsulot_obj,            # qaysi xomashyo (sement/qum/shag‘al)
#                     izoh=item.xomashyo_izohi,
#                     miqdori=Decimal(str(d["olingan"])),
#                     narxi_donasi=Decimal(str(d["narxi_donasi"])),
#                     total_narx=Decimal(str(d["olingan"])) * Decimal(str(d["narxi_donasi"])),
#                     zavod=item.kamera,
#                     vaqti=item.date
#                 )

#             # === Omborlarni sinxronlashtirish ===
#             taken_from_stock = sum(d["olingan"] for d in details if not d["is_deficit"])
#             deficit_qty      = sum(d["olingan"] for d in details if d["is_deficit"])
#             deficit_price    = next((float(d["narxi_donasi"]) for d in details if d["is_deficit"]), None)

#             # 4.1) Har qanday mahsulot -> SkladProducts dan kamaytirish (faqat real olingan qism)
#             umumiy_olingan = float(taken_from_stock) + float(deficit_qty or 0)

#             if umumiy_olingan > 0:
#                 SkladProducts.objects.filter(pk=maxsulot_obj.pk).update(
#                     soni=F("soni") - umumiy_olingan
#                 )

#             # 4.2) Sement bo‘lsa -> SementZavod dan (shu zavod bo‘yicha) kamaytirish
#             if is_sement:
#                 # yo‘q bo‘lsa ham yaratiladi (0 dan)
#                 sz, _ = SementZavod.objects.get_or_create(
#                     sement_nomi=maxsulot_obj,
#                     zavod=item.kamera,
#                     defaults={"sement_miqdori": 0}
#                 )
#                 # taken_from_stock + deficit_qty ikkalasini ham hisobga olib ayiramiz
#                 umumiy_olingan = float(taken_from_stock) + float(deficit_qty or 0)

#                 SementZavod.objects.filter(pk=sz.pk).update(
#                     sement_miqdori=F("sement_miqdori") - umumiy_olingan
#                 )


#             # 4.3) Yetishmasa — Sklad ga avto-kirim (tolov_turi='N'; yetkazuvchi=zavod nomi)
#             if deficit_qty and deficit_qty > 0:
#                 yetkazuvchi_obj, _ = SkladYetkazuvchi.objects.get_or_create(
#                     yetkazib_beruvchi=item.kamera.kamera_nomi
#                 )
#                 narx_donasi = float(deficit_price or 0)
#                 jami = float(deficit_qty) * narx_donasi

#                 # Sklad.objects.create(
#                 #     maxsulot_nomi=maxsulot_obj,
#                 #     maxsulot_miqdori=float(deficit_qty),
#                 #     maxsulot_narxi=narx_donasi,
#                 #     jami_maxsulot_narxi=jami,
#                 #     tolov_turi='N',
#                 #     yetkazuvchi=yetkazuvchi_obj,
#                 #     zavod=item.kamera,
#                 #     izoh=f"Avtomatik defitsit (Zakaz ID: {item.pk})",
#                 #     sana=timezone.now(),
#                 # )
#                 # Eslatma: defitsit bo‘lgani uchun SkladProducts/SementZavod ni BU YERDA oshirmaymiz.
#                 # Agar bu kirimni real balansga qo‘shmoqchi bo‘lsangiz, shu yerda sonini +deficit_qty qiling.

#             # === /Omborlarni sinxronlashtirish ===

#             jami_tan_narxi += float(total_cost)

#         # 5) Tan narxni bir marta yozamiz va all_checked ni belgilaymiz
#         item.maxsulot_tan_narx = float(jami_tan_narxi)
#         item.tan_narxi_qoyildi = True
#         item.all_checked = True
#         item.save(update_fields=["maxsulot_tan_narx", "tan_narxi_qoyildi", "all_checked"])



#     return JsonResponse({'status': 'ok', 'selected': item.checked, 'jami_tan_narx': item.maxsulot_tan_narx})


@login_required
def suggest_mashina(request):
    query = request.GET.get('q', '').strip().upper()
    query_clean = query.replace(" ", "")

    mashinalar = Mashina.objects.annotate(
        raqam_clean=Replace('mashina_raqami', Value(" "), Value(""))
    ).filter(raqam_clean__icontains=query_clean)

    if query:
        mashinalar = mashinalar.annotate(
            priority=Case(
                When(raqam_clean__startswith=query_clean, then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            )
        ).order_by('priority', 'mashina_raqami')
    else:
        mashinalar = mashinalar.order_by('mashina_raqami')

    return JsonResponse(list(mashinalar.values_list('mashina_raqami', flat=True)[:20]), safe=False)

@login_required
def suggest_common(request, model_name, field_name):
    query = request.GET.get('q', '').strip()

    try:
        Model = apps.get_model('account', model_name)  # your_app_name ni almashtir
    except LookupError:
        return JsonResponse([], safe=False)

    objects = Model.objects.filter(Q(**{f"{field_name}__icontains": query}))

    if query:
        objects = objects.annotate(
            priority=Case(
                When(**{f"{field_name}__startswith": query}, then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            )
        ).order_by('priority', field_name)
    else:
        objects = objects.order_by(field_name)

    return JsonResponse(list(objects.values_list(field_name, flat=True)[:10]), safe=False)

@login_required
def add_product(request):
    if request.method == 'POST':
        form = AddProductForm(data=request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            mashina_raqami = form.cleaned_data['mashina']
            tashkilot_nomi = form.cleaned_data['tashkilot_nomi']
            obyekt_name = form.cleaned_data['obyekt_text']
            kim_tomonidan_jonatilgani = form.cleaned_data['kim_tomonidan_jonatilgani']
            umumiy_maxsulot = form.cleaned_data['umumiy_maxsulot']
            qogozdagi_maxsulot_soni = form.cleaned_data['qogozdagi_maxsulot_soni']
            mashina_obj, _ = Mashina.objects.get_or_create(mashina_raqami=mashina_raqami)
            product.mashina = mashina_obj
            umumiy = form.cleaned_data.get("umumiy_maxsulot")
            
            if tashkilot_nomi:
                obyekt = (
                    PriObyekts.objects
                    .filter(
                        obyekt_name__iexact=obyekt_name,
                        tashkilot_name__iexact=tashkilot_nomi
                    )
                    .first()
                )

                obyekt_id = obyekt.pk


                product_id = int(umumiy_maxsulot.split("_")[-1])

                agent = Agents.objects.get(full_name=kim_tomonidan_jonatilgani)

                order = Orders.objects.filter(agent=agent.pk, money_type="Pri", obyekt_id = obyekt_id, product = product_id).order_by("-date").first()
                product.obyekt_id = obyekt.pk
                product.tashkilot_nomi = obyekt
                product.xarajat_narxi = order.otkat
            
            else:
                obyekt = (
                    NaqdObyekts.objects.filter(obyekt_name__iexact=obyekt_name).first()
                )

                obyekt_id = obyekt.pk

                product_id = int(umumiy_maxsulot.split("_")[-1])

                agent = Agents.objects.get(full_name=kim_tomonidan_jonatilgani)

                order = Orders.objects.filter(agent=agent.pk, money_type="Naqd", obyekt_id = obyekt_id, product = product_id).order_by("-date").first()
                product.obyekt_id = obyekt.pk


            start = order.date
            end = order.date + timedelta(days=2)
            today = timezone.now().date()  

            if start <= today <= end:
                product.mijoz_qoygan_narx = order.price
                product.mijoz_jami_qoygan_narx = order.price * qogozdagi_maxsulot_soni
            
            else:
                print(f"Narx topilmadi {timezone.now()}")

            if umumiy:
                if umumiy.startswith("beton_"):
                    beton_id = umumiy.replace("beton_", "")
                    product.maxsulot_markasi = BetonMarkasi.objects.get(id=beton_id)
                    product.xomashyo = None
                elif umumiy.startswith("xomashyo_"):
                    xom_id = umumiy.replace("xomashyo_", "")
                    product.xomashyo = SkladProducts.objects.get(id=xom_id)
                    product.maxsulot_markasi = None

            product.save()



            with transaction.atomic():
                # 0) Zakazni lock qilamiz
                item = Asosiy.objects.select_for_update().get(pk=product.pk)

                # Toggle
                # item.checked = not item.checked
                # item.save(update_fields=["checked"])

                # all_checked True bo‘lsa — qayta sarf/yozish yo‘q
                if item.all_checked:
                    return JsonResponse({'status': 'skipped', 'selected': item.checked})
                    
                if item.xomashyo and not item.maxsulot_markasi:
                    sklad = SkladProducts.objects.select_for_update().get(pk=item.xomashyo.pk)

                    # sement bo‘lsa zavod bo‘yicha mavjud miqdor, bo‘lmasa umumiy soni
                    if "sement" in (item.xomashyo.maxsulot_nomi or "").lower():
                        sz, _ = SementZavod.objects.get_or_create(
                            sement_nomi=item.xomashyo,
                            zavod=item.kamera,
                            defaults={"sement_miqdori": 0}
                        )
                        mavjud = sz.sement_miqdori
                        last_prices = (
                            Sklad.objects.filter(maxsulot_nomi=item.xomashyo, zavod=item.kamera)
                            .order_by("-sana", "-id")
                            .values_list("maxsulot_narxi", flat=True)
                        )
                    else:
                        mavjud = sklad.soni
                        last_prices = (
                            Sklad.objects.filter(maxsulot_nomi=item.xomashyo)
                            .order_by("-sana", "-id")
                            .values_list("maxsulot_narxi", flat=True)
                        )

                    # narxni topish
                    oxirgi_narx = 0
                    for price in last_prices:
                        if price and price > 0:
                            oxirgi_narx = price
                            break

                    # ✅ Yetarli bo‘lsa kamaytirish
                    if mavjud >= item.maxsulot_soni:
                        if "sement" in (item.xomashyo.maxsulot_nomi or "").lower():
                            SementZavod.objects.filter(pk=sz.pk).update(
                                sement_miqdori=F("sement_miqdori") - float(item.maxsulot_soni)
                            )   
                        else:
                            SkladProducts.objects.filter(pk=sklad.pk).update(
                                soni=F("soni") - float(item.maxsulot_soni)
                            )

                        DetailXomashyo.objects.create(
                            maxsulot=None,
                            xomashyo=item.xomashyo,
                            izoh=item.xomashyo_izohi,
                            miqdori=item.maxsulot_soni,
                            narxi_donasi=oxirgi_narx,
                            total_narx=item.maxsulot_soni * oxirgi_narx,
                            zavod=item.kamera,
                            vaqti=item.date
                        )
                        item.maxsulot_tan_narx = item.maxsulot_soni * oxirgi_narx

                    else:
                        # ❌ Yetarli emas → defitsit
                        kerak = item.maxsulot_soni - mavjud

                        # mavjud qismni nolga tushirib yuboramiz
                        if "sement" in (item.xomashyo.maxsulot_nomi or "").lower():
                            SementZavod.objects.filter(pk=sz.pk).update(
                                sement_miqdori = F("sement_miqdori") - float(item.maxsulot_soni)
                            )

                        else:
                            SkladProducts.objects.filter(pk=sklad.pk).update(
                                soni = F("soni") - float(item.maxsulot_soni)
                            )

                        DetailXomashyo.objects.create(
                            maxsulot=None,
                            xomashyo=item.xomashyo,
                            izoh=item.xomashyo_izohi,
                            miqdori=mavjud,
                            narxi_donasi=oxirgi_narx,
                            total_narx=mavjud * oxirgi_narx,
                            zavod=item.kamera,  
                            vaqti=item.date
                        )

                        # 🔥 Defitsit ham yoziladi
                        DetailXomashyo.objects.create(
                            maxsulot=None,
                            xomashyo=item.xomashyo,
                            izoh=item.xomashyo_izohi,
                            miqdori=kerak,
                            narxi_donasi=oxirgi_narx,
                            total_narx=kerak * oxirgi_narx,
                            zavod=item.kamera,
                            vaqti=item.date
                        )

                        # Avto-kirim yozish
                        # yetkazuvchi_obj, _ = SkladYetkazuvchi.objects.get_or_create(
                        #     yetkazib_beruvchi=item.kamera.kamera_nomi
                        # )
                        # Sklad.objects.create(
                        #     maxsulot_nomi=item.xomashyo,
                        #     maxsulot_miqdori=kerak,
                        #     maxsulot_narxi=oxirgi_narx,
                        #     jami_maxsulot_narxi=kerak * oxirgi_narx,
                        #     tolov_turi='N',
                        #     yetkazuvchi=yetkazuvchi_obj,
                        #     zavod=item.kamera,
                        #     izoh=f"Avtomatik defitsit (Zakaz ID: {item.pk})",
                        #     sana=timezone.now(),
                        # )

                        item.maxsulot_tan_narx = item.maxsulot_soni * oxirgi_narx

                    item.tan_narxi_qoyildi = True
                    item.all_checked = True
                    item.save(update_fields=["maxsulot_tan_narx", "tan_narxi_qoyildi", "all_checked"])

                    return JsonResponse({
                        'status': 'ok',
                        'selected': item.checked,
                        'jami_tan_narx': item.maxsulot_tan_narx
                    })
                

                # 1) Oxirgi retsept vaqtini topamiz (shu marka bo‘yicha)
                oxirgi_vaqt = (
                    Retsept.objects
                    .filter(retsept_nomi=item.maxsulot_markasi)
                    .order_by('-date')
                    .values_list('date', flat=True)
                    .first()
                )
                if not oxirgi_vaqt:
                    return JsonResponse({'status': 'error', 'message': 'Retsept topilmadi'}, status=404)

                start = oxirgi_vaqt - timedelta(minutes=1)
                end   = oxirgi_vaqt + timedelta(minutes=1)

                # 2) Shu retsept_nomi + vaqt oralig‘idagi barcha yozuvlar
                toliq_guruh = list(
                    Retsept.objects
                    .filter(retsept_nomi=item.maxsulot_markasi, date__range=(start, end))
                    .select_related("maxsulot")
                )
                if not toliq_guruh:
                    return JsonResponse({'status': 'error', 'message': 'Retsept tarkibi topilmadi'}, status=404)

                # 3) Retseptni mahsulot bo‘yicha JAMLAYMIZ (duplikatlar yo‘qolsin)
                needs = {}     # key = (product_pk, is_sement) -> jami_kerak (int)
                prod_map = {}  # product_pk -> SkladProducts instance
                for r in toliq_guruh:
                    maxsulot_obj = r.maxsulot
                    is_sement = "sement" in (maxsulot_obj.maxsulot_nomi or "").lower()
                    kerak_miqdor = Decimal(r.miqdor) * Decimal(item.maxsulot_soni)
                    key = (maxsulot_obj.pk, is_sement)
                    needs[key] = needs.get(key, 0) + float(kerak_miqdor)
                    prod_map[maxsulot_obj.pk] = maxsulot_obj

                # 4) FIFO bo‘yicha sarf (SkladRetsept dan kamayadi; defitsit bo‘lsa SkladRetseptga yangi batch)
                jami_tan_narxi = 0
                for (prod_pk, is_sement), jami_kerak in needs.items():
                    maxsulot_obj = prod_map[prod_pk]

                    if is_sement:
                        total_cost, details = fifo_cost_and_consume(
                            maxsulot=maxsulot_obj,
                            kerak_miqdor=jami_kerak,
                            zavod=item.kamera,    # sementlar zavod kesimida
                            when=oxirgi_vaqt
                        )
                    else:
                        total_cost, details = fifo_cost_and_consume(
                            maxsulot=maxsulot_obj,
                            kerak_miqdor=jami_kerak,
                            zavod=None,
                            when=oxirgi_vaqt
                        )
                    
                    for d in details:
                        DetailXomashyo.objects.create(
                            maxsulot=item.maxsulot_markasi,   # qaysi beton markasi
                            xomashyo=maxsulot_obj,            # qaysi xomashyo (sement/qum/shag‘al)
                            izoh=item.xomashyo_izohi,
                            miqdori=Decimal(str(d["olingan"])),
                            narxi_donasi=Decimal(str(d["narxi_donasi"])),
                            total_narx=Decimal(str(d["olingan"])) * Decimal(str(d["narxi_donasi"])),
                            zavod=item.kamera,
                            vaqti=item.date
                        )

                    # === Omborlarni sinxronlashtirish ===
                    taken_from_stock = sum(d["olingan"] for d in details if not d["is_deficit"])
                    deficit_qty      = sum(d["olingan"] for d in details if d["is_deficit"])
                    deficit_price    = next((float(d["narxi_donasi"]) for d in details if d["is_deficit"]), None)

                    # 4.1) Har qanday mahsulot -> SkladProducts dan kamaytirish (faqat real olingan qism)
                    umumiy_olingan = float(taken_from_stock) + float(deficit_qty or 0)

                    if umumiy_olingan > 0:
                        SkladProducts.objects.filter(pk=maxsulot_obj.pk).update(
                            soni=F("soni") - umumiy_olingan
                        )

                    # 4.2) Sement bo‘lsa -> SementZavod dan (shu zavod bo‘yicha) kamaytirish
                    if is_sement:
                        # yo‘q bo‘lsa ham yaratiladi (0 dan)
                        sz, _ = SementZavod.objects.get_or_create(
                            sement_nomi=maxsulot_obj,
                            zavod=item.kamera,
                            defaults={"sement_miqdori": 0}
                        )
                        # taken_from_stock + deficit_qty ikkalasini ham hisobga olib ayiramiz
                        umumiy_olingan = float(taken_from_stock) + float(deficit_qty or 0)

                        SementZavod.objects.filter(pk=sz.pk).update(
                            sement_miqdori=F("sement_miqdori") - umumiy_olingan
                        )


                    # 4.3) Yetishmasa — Sklad ga avto-kirim (tolov_turi='N'; yetkazuvchi=zavod nomi)
                    if deficit_qty and deficit_qty > 0:
                        yetkazuvchi_obj, _ = SkladYetkazuvchi.objects.get_or_create(
                            yetkazib_beruvchi=item.kamera.kamera_nomi
                        )
                        narx_donasi = float(deficit_price or 0)
                        jami = float(deficit_qty) * narx_donasi

                        # Sklad.objects.create(
                        #     maxsulot_nomi=maxsulot_obj,
                        #     maxsulot_miqdori=float(deficit_qty),
                        #     maxsulot_narxi=narx_donasi,
                        #     jami_maxsulot_narxi=jami,
                        #     tolov_turi='N',
                        #     yetkazuvchi=yetkazuvchi_obj,
                        #     zavod=item.kamera,
                        #     izoh=f"Avtomatik defitsit (Zakaz ID: {item.pk})",
                        #     sana=timezone.now(),
                        # )
                        # Eslatma: defitsit bo‘lgani uchun SkladProducts/SementZavod ni BU YERDA oshirmaymiz.
                        # Agar bu kirimni real balansga qo‘shmoqchi bo‘lsangiz, shu yerda sonini +deficit_qty qiling.

                    # === /Omborlarni sinxronlashtirish ===

                    jami_tan_narxi += float(total_cost)

                # 5) Tan narxni bir marta yozamiz va all_checked ni belgilaymiz
                item.maxsulot_tan_narx = float(jami_tan_narxi)
                item.tan_narxi_qoyildi = True
                item.all_checked = True
                item.save(update_fields=["maxsulot_tan_narx", "tan_narxi_qoyildi", "all_checked"])



            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status':'ok','selected': item.checked,'jami_tan_narx': item.maxsulot_tan_narx, 'redirect_url': reverse('home')})   # ✅ shu
            
            return redirect('home')
    else:
        form = AddProductForm()
    

    mashinalar = Mashina.objects.all().order_by("mashina_raqami")  # ← shu qatorni qo‘shish muhim

    return render(request, 'add_product.html', {
        'form': form,
        'mashinalar': mashinalar  # ← kontekstga yuborish
    })

@login_required
def add_test_product(request):
    if request.method == 'POST':
        form = AddTestProductForm(data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('home'))
    else:
        form = AddTestProductForm()
    
    context = {
        'form': form
    }

    return render(request, 'add_test.html', context)

@login_required
def tashkilot_by_agent(request):
    agent_id = request.GET.get('agent_id')

    if not agent_id:
        return JsonResponse([], safe=False)

    # Orders → obyekt_id larni olamiz
    obyekt_ids = (
        Orders.objects
        .filter(agent_id=agent_id, money_type="Pri")
        .values_list('obyekt_id', flat=True)
        .distinct()
    )

    # Shu obyektlardan tashkilot nomlari
    tashkilotlar = (
        PriObyekts.objects
        .filter(id__in=obyekt_ids)
        .values_list('tashkilot_name', flat=True)
        .distinct()
    )

    return JsonResponse(list(tashkilotlar), safe=False)

@login_required
def obyekt_by_agent(request):
    agent_id = request.GET.get('agent_id')
    tashkilot_name = request.GET.get('tashkilot_name')  # faqat P da keladi

    if not agent_id:
        return JsonResponse([], safe=False)

    # 1️⃣ Agent bo‘yicha ordersdan obyekt_id larni olamiz
    obyekt_ids = (
        Orders.objects
        .filter(agent_id=agent_id)
        .values_list('obyekt_id', flat=True)
        .distinct()
    )

    # 2️⃣ Agar tashkilot_name BOR bo‘lsa → PRI
    if tashkilot_name:
        obyektlar = (
            PriObyekts.objects
            .filter(
                id__in=obyekt_ids,
                tashkilot_name=tashkilot_name
            )
            .values_list('obyekt_name', flat=True)
            .distinct()
        )

    # 3️⃣ Aks holda → NAQD
    else:
        obyektlar = (
            NaqdObyekts.objects
            .filter(id__in=obyekt_ids)
            .values_list('obyekt_name', flat=True)
            .distinct()
        )

    return JsonResponse(list(obyektlar), safe=False)


@login_required
def change_product(request, pk):
    instance = get_object_or_404(Asosiy, pk=pk)
    if request.method == 'POST':
        form =  AddProductForm(data = request.POST, instance = instance)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('home'))
    else:
        form = AddProductForm(instance=instance)
    
    context = {
        'form': form,
        'instance': instance
    }

    return render(request, 'change_product.html', context)

@login_required
def delete_product(request, pk):
    item = get_object_or_404(Asosiy, pk=pk)

    oxirgi_vaqt = item.date

    start_time = oxirgi_vaqt - timedelta(minutes=1)
    end_time   = oxirgi_vaqt + timedelta(minutes=1)



    toliq_guruh = DetailXomashyo.objects.filter(
        vaqti__range=(start_time, end_time)
    )

    for guruh in toliq_guruh:
        if guruh.xomashyo.maxsulot_nomi == "Sement":
            sement = SementZavod.objects.get(sement_nomi=guruh.xomashyo, zavod=guruh.zavod)
            
            sement.sement_miqdori += float(guruh.miqdori)
            
            sement.save()
        
        

        mahsulot = SkladProducts.objects.get(pk=guruh.xomashyo.pk)

        mahsulot.soni += float(guruh.miqdori)

        mahsulot.save()


    toliq_guruh.delete() 


    


    item.delete()
    # return HttpResponseRedirect(reverse('home'))
    return JsonResponse({"status": "ok"})


@login_required
def product_setting(request):
    mijozlar = Mijoz.objects.all()
    # maxsulotlar = Maxsulot.objects.all()
    obyektlar = Obyekt.objects.all()
    jonatuvchilar = Jonativchi.objects.all()
    kameralar = Kamera.objects.all()
    markalar = BetonMarkasi.objects.all()

    context = {
        'clients': mijozlar,
        # 'products': maxsulotlar,
        'places': obyektlar,
        'from_users': jonatuvchilar,
        'cameras': kameralar,
        'markas': markalar
    }
    return render(request, 'product_settings.html', context)

FORM_MAP = {
    1: (AddMijozForm, 'add_mijoz.html'),
    # 2: (AddMaxsulotForm, 'add_maxsulot.html'),
    3: (AddObyektForm, 'add_obyekt.html'),
    4: (AddJonatuvchiForm, 'add_jonatuvchi.html'),
    5: (AddKameraForm, 'add_kamera.html'),
    6: (AddBetonMarkaForm, 'add_marka.html'),
}

@login_required
def add_all(request, add_id):
    form_class, template = FORM_MAP.get(add_id, (None, None))
    if not form_class:
        return redirect('setting')
    if request.method == 'POST':
        form = form_class(data=request.POST)
        if form.is_valid():
            form.save()
            next_url = request.POST.get('next')
            return redirect(next_url or reverse('setting'))
    else:
        form = form_class()

    context = {
        'form': form,
        'add_id': add_id
    }
    return render(request, template, context)

@login_required
def change_k_o_kelgani(request, jonatuvchi_id):
    jonatuvchi = get_object_or_404(Jonativchi, id=jonatuvchi_id)

    if request.method == 'POST':
        form = ChangeJonatuvchiForm(request.POST, instance=jonatuvchi)
        if form.is_valid():
            form.save()
            # Orqaga qaytish uchun GET next ni ishlatamiz
            next_url = request.GET.urlencode()
            return redirect(f'/kirim/add?{next_url}')
    else:
        form = ChangeJonatuvchiForm(instance=jonatuvchi)

    return render(request, 'change_k_o_kelgani.html', {'form': form})


@login_required
def pechat_qilish(request, pk):
    item = get_object_or_404(Asosiy, pk=pk)
    context = {
        'item': item
    }
    return render(request, 'pechat_qilish.html', context)

@login_required
def export_excel(request):
    data = Asosiy.objects.all().values(
        'id', 'mijoz__ism_familya', 'kim_tomonidan_jonatilgani__ism_familya',
        'obyekt_nomi__obyekt_nomi', 'maxsulot_markasi__markasi',
        'qogozdagi_maxsulot_soni', 'maxsulot_soni',
        'mashina__mashina_raqami', 'kamera__kamera_nomi', 'date'
    )
    df = pd.DataFrame(data)

    # Sana formatini to'g'rilash (tzinfo olib tashlanadi)
    if 'date' in df.columns:
        df['date'] = df['date'].apply(lambda x: localtime(x).replace(tzinfo=None) if pd.notnull(x) else x)

    # Ustun nomlarini o'zgartirish
    df.rename(columns={
        'Бетон': 'Maxsulot nomi',
        'mijoz__ism_familya': 'Mijoz',
        'kim_tomonidan_jonatilgani__ism_familya': 'Kim orqali kelgani',
        'obyekt_nomi__obyekt_nomi': 'Obyekt',
        'maxsulot_markasi__markasi': 'Markasi',
        'qogozdagi_maxsulot_soni': 'Qog\'ozdagi miqdori',
        'maxsulot_soni': 'Real miqdori',
        'mashina__mashina_raqami': 'Mashina',
        'kamera__kamera_nomi': 'Kamera',
        'date': 'Sana'
    }, inplace=True)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='yyyy-mm-dd HH:mm') as writer:
        df.to_excel(writer, sheet_name='Hisobot', index=False)
        workbook = writer.book
        worksheet = writer.sheets['Hisobot']

        # Ranglar ketma-ketligi
        fill_colors = cycle(['#FFFF99', '#CCFFCC', '#FFCCCC', '#CCE5FF', '#D9D2E9', '#FFF2CC'])
        color_map = {}
        row_colors = [] 

        bg_color_map = {}

        # Har bir sanaga rang ajratish
        for date_val in df['Sana']:
            date_key = date_val.date() if pd.notnull(date_val) else None
            if date_key not in color_map:
                color = next(fill_colors)
                color_map[date_key] = workbook.add_format({'bg_color': color})
                bg_color_map[date_key] = color
            row_colors.append(color_map[date_key])

        # Sana uchun alohida format (rang + datetime)
        date_format_map = {}
        for date_key, color in bg_color_map.items():
            date_format_map[date_key] = workbook.add_format({
                'bg_color': color,
                'num_format': 'yyyy-mm-dd hh:mm'
            })

        # Ma'lumotlarni format bilan yozish
        for row_num, (row_data, fmt) in enumerate(zip(df.values.tolist(), row_colors), start=1):
            for col_num, value in enumerate(row_data):
                col_name = df.columns[col_num]
                if col_name == 'Sana' and pd.notnull(value):
                    date_fmt = date_format_map.get(value.date())
                    worksheet.write_datetime(row_num, col_num, value, date_fmt)
                else:
                    worksheet.write(row_num, col_num, value, fmt)

        # Ustun kengliklarini sozlash
        for idx, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(idx, idx, column_width)

    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=hisobot.xlsx'
    return response

@login_required
def get_kamera_ip(request, kamera_id):
    kamera = get_object_or_404(Kamera, id=kamera_id)
    return JsonResponse({'ip': kamera.kamera_ip})


@login_required
def gen_frames(request, kamera_id):
    kamera = get_object_or_404(Kamera, id=kamera_id)
    cap = cv2.VideoCapture(kamera.kamera_ip)

    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@login_required
def video_feed(request, kamera_id):
    return StreamingHttpResponse(
        gen_frames(request, kamera_id),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )

@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='login')
def kassa_login(request):
    return render(request, 'kassa_login.html')

@login_required
def check_home(request):
    all_records = Asosiy.objects.all().order_by('-date')

    context = {
        'datas': all_records
    }

    return render(request, 'check_home.html', context)


@login_required
def kirim_hisobot(request):

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    selected_jonatuvchi = request.GET.get('jonatuvchi') or ''

    queryset = Kirim.objects.all()

    if from_date and to_date:
        queryset = queryset.filter(sana__date__range=[from_date, to_date])
    
    elif from_date:
        queryset = queryset.filter(sana__date=from_date)
    
    elif to_date:
        queryset = queryset.filter(sana__date=to_date)
    
    if selected_jonatuvchi:
        try:
            queryset = queryset.filter(k_o_kelgani__ism_familya = selected_jonatuvchi)
        except Jonativchi.DoesNotExist:
            queryset = queryset.none()
    

    


    n_summa = queryset.filter(
        checked = 'N'
    ).aggregate(jami=Sum('summa'))['jami'] or 0

    p_summa = queryset.filter(
        checked = 'P'
    ).aggregate(jami=Sum('summa'))['jami'] or 0

    kirimlar = queryset.order_by('-sana')
    jonatuvchilar = Jonativchi.objects.all()

    umumiy_summa = queryset.aggregate(total=Sum('summa'))['total'] or 0


    context = {
        'n_summa': n_summa,
        'p_summa': p_summa,
        'kirimlar': kirimlar,
        'selected_from': from_date,
        'selected_to': to_date,
        'selected_jonatuvchi': selected_jonatuvchi,
        'jonatuvchilar': jonatuvchilar,
        'umumiy_summa': umumiy_summa
    }
    return render(request, 'kirim_hisobot.html', context)

@login_required
def add_kirim(request):
    if request.method == 'POST':
        form = AddKirimForm(request.POST)
        if form.is_valid():
            kirim = form.save(commit=False)
            if not kirim.sana:
                kirim.sana = timezone.now()
            kirim.save()
            return redirect('kirim_hisobot')
        else:
            print(form.errors)
    else:
        # Agar query string orqali qiymatlar kelsa — initial qilib beramiz
        initial_data = request.GET.dict()
        form = AddKirimForm(initial=initial_data)

    return render(request, 'add_kirim.html', {'form': form})

@login_required
def sklad_products_list(request):
    barcha_maxsulotlar = SkladProducts.objects.exclude(maxsulot_nomi="Sement")
    barcha_sementlar = SementZavod.objects.all()

    umumiy_sement = barcha_sementlar.aggregate(total=Sum("sement_miqdori"))["total"] or 0


    context = {
        "maxsulotlar": barcha_maxsulotlar,
        "sementlar": barcha_sementlar,
        "total_sement": umumiy_sement
    }
    return render(request, "sklad_list.html", context)


@login_required
def add_sklad_products(request):
    if request.method == 'POST':
        form = AddSkladProductsForm(data=request.POST)
        if form.is_valid():
            sklad = form.save(commit=False)

            if not sklad.izoh or sklad.izoh.strip() == "":
                sklad.izoh = None  

            if not sklad.sana:
                sklad.sana = timezone.now()
            
            sklad.jami_maxsulot_narxi = sklad.maxsulot_narxi * sklad.maxsulot_miqdori

            sklad.save()


            # 🔹 SkladProducts yangilash
            product = sklad.maxsulot_nomi
            product.soni += sklad.maxsulot_miqdori
            product.save()

            

            # 🔹 SementZavod yangilash
            if "sement" in product.maxsulot_nomi.lower():
                obj, created = SementZavod.objects.get_or_create(
                    sement_nomi=product,
                    zavod=sklad.zavod,
                    defaults={"sement_miqdori": sklad.maxsulot_miqdori}
                )
                if not created:
                    obj.sement_miqdori += sklad.maxsulot_miqdori
                    obj.save()
                
                SkladRetsept.objects.create(
                    maxsulot = sklad.maxsulot_nomi,
                    zavod = sklad.zavod,
                    keltirilgan_miqdor = sklad.maxsulot_miqdori,
                    qancha_qolgani = sklad.maxsulot_miqdori,
                    narxi_donasi = sklad.maxsulot_narxi,
                    olingan_sana = sklad.sana
                )
            
            else:
                SkladRetsept.objects.create(
                    maxsulot = sklad.maxsulot_nomi,
                    keltirilgan_miqdor = sklad.maxsulot_miqdori,
                    qancha_qolgani = sklad.maxsulot_miqdori,
                    narxi_donasi = sklad.maxsulot_narxi,
                    olingan_sana = sklad.sana
                )

            return redirect('sklad_products')
        else:
            print(form.errors)
    else:
        form = AddSkladProductsForm()

    return render(request, 'add_sklad_product.html', {'form': form})




# def add_yetkazib_beruvchi(request):
#     if request.method == "POST":
#         form = AddYetkazibBeruvchiForm(data=request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('add_sklad_products')
#         else: 
#             print(form.errors)
#     else:
#         form = AddYetkazibBeruvchiForm()
    
#     context = {
#         'form': form
#     }

#     return render(request, 'add_yetkazib_beruvchi.html', context)

@login_required
def add_yetkazib_beruvchi(request):
    if request.method == "POST":
        form = AddYetkazibBeruvchiForm(request.POST)
        if form.is_valid():
            yetkazuvchi = form.save()
            return JsonResponse({
                "id": yetkazuvchi.id,
                "nomi": yetkazuvchi.yetkazib_beruvchi
            })
        else:
            return JsonResponse({"errors": form.errors}, status=400)
    return JsonResponse({"error": "Faqat POST so‘rovlarga ruxsat beriladi"}, status=405)

@login_required
def add_retsept(request):
    if request.method == "POST":
        formset = RetseptFormSet(request.POST, queryset=Retsept.objects.none())
        if formset.is_valid():
            first_retsept = formset.forms[0].cleaned_data.get("retsept_nomi")
            if not first_retsept:
                formset.errors[0]["retsept_nomi"] = ["Retsept turi majburiy"]
            else:
                instances = formset.save(commit=False)

                for i, instance in enumerate(instances):
                    if not instance.retsept_nomi_id:  # ForeignKey id bo‘sh bo‘lsa
                        instance.retsept_nomi = first_retsept

                # endi hammasini birdaniga saqlaymiz
                for instance in instances:
                    instance.save()
                return redirect("retsept_list")
        else:
            print(formset.errors)
    else:
        formset = RetseptFormSet(queryset=Retsept.objects.none())

    return render(request, "add_retsept.html", {"formset": formset})


@login_required
def sklad_hisobot(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    selected_yetkazuvchi = request.GET.get('yetkazuvchi') or ''
    selected_xomashyo = request.GET.get('xomashyo')
    selected_zavod = request.GET.get('zavod')

    sklad = Sklad.objects.all()
    chiqim = DetailXomashyo.objects.all()


    today = date.today()

    if from_date and to_date:
        sklad = sklad.filter(sana__date__range=[from_date, to_date])
        chiqim = chiqim.filter(vaqti__date__range=[from_date, to_date])

    elif from_date:
        sklad = sklad.filter(sana__date=from_date)
        chiqim = chiqim.filter(vaqti__date=from_date)
    
    elif to_date:
        sklad = sklad.filter(sana__date=to_date)
        chiqim = chiqim.filter(vaqti__date=to_date)

    if selected_yetkazuvchi:
        try:
            sklad = sklad.filter(yetkazuvchi__yetkazib_beruvchi=selected_yetkazuvchi)
        except Jonativchi.DoesNotExist:
            sklad = sklad.none()
    
    if selected_xomashyo:
        sklad = sklad.filter(maxsulot_nomi__maxsulot_nomi=selected_xomashyo)
        chiqim = chiqim.filter(xomashyo__maxsulot_nomi=selected_xomashyo)
    
    if selected_zavod:
        sklad = sklad.filter(zavod__kamera_nomi=selected_zavod)
        chiqim = chiqim.filter(zavod__kamera_nomi=selected_zavod)
    
    if not any([from_date, to_date, selected_yetkazuvchi, selected_xomashyo, selected_zavod]):
        sklad = sklad.filter(sana__date=today)
        chiqim = chiqim.filter(vaqti__date=today)

        
    
    n_summa = sklad.filter(
        tolov_turi = 'N'
    ).aggregate(jami=Sum('maxsulot_narxi'))['jami'] or 0

    p_summa = sklad.filter(
        tolov_turi = 'P'
    ).aggregate(jami=Sum('maxsulot_narxi'))['jami'] or 0

    all_records = []

    for s in sklad:
        all_records.append({
            "maxsulot_nomi": s.maxsulot_nomi,
            "maxsulot_miqdori": s.maxsulot_miqdori,
            "yetkazuvchi": s.yetkazuvchi.yetkazib_beruvchi,
            "maxsulot_narxi": s.maxsulot_narxi,
            "jami_maxsulot_narxi": s.jami_maxsulot_narxi,
            "tolov_turi": s.tolov_turi,
            "izoh": s.izoh,
            "zavod": s.zavod,
            "sana": s.sana
        })

    for ch in chiqim:
        all_records.append({
            "maxsulot_nomi": ch.xomashyo,
            "maxsulot_miqdori": -ch.miqdori,
            "yetkazuvchi": "-",
            "maxsulot_narxi": -ch.narxi_donasi,
            "jami_maxsulot_narxi": -ch.total_narx,
            "tolov_turi": "-",
            "izoh": ch.izoh,
            "zavod": ch.zavod,
            "sana": ch.vaqti
        })

    all_records = sorted(all_records, key=lambda x: x["sana"], reverse=True)

    yetkazuvchilar = SkladYetkazuvchi.objects.exclude(
        yetkazib_beruvchi__in=["1-Zavod", "2-Zavod"]
    )
    xomashyolar = SkladProducts.objects.all()
    zavodlar = Kamera.objects.all()

    sklad_summa = sklad.aggregate(total=Sum('jami_maxsulot_narxi'))['total'] or 0
    
    chiqim_summa = chiqim.aggregate(total=Sum('total_narx'))['total'] or 0

    sklad_miqdor = sklad.aggregate(total=Sum('maxsulot_miqdori'))['total'] or 0
    chiqim_miqdor = chiqim.aggregate(total=Sum('miqdori'))['total'] or 0

    jammi_summa = sklad_summa - chiqim_summa
    jami_miqdor =  sklad_miqdor - chiqim_miqdor
    
    context = {
        'hisobotlar': all_records,
        'selected_from': from_date,
        'selected_to': to_date, 
        'selected_yetkazuvchi': selected_yetkazuvchi,
        'selected_xomashyo': selected_xomashyo,
        'selected_zavod': selected_zavod,
        'yetkazuvchilar': yetkazuvchilar,
        'xomashyolar': xomashyolar,
        'zavodlar': zavodlar,
        'n_summa': n_summa,
        'p_summa': p_summa,
        'jammi_summa': jammi_summa,
        'umumiy_miqdor': jami_miqdor
    }

    return render(request, 'sklad_hisobot.html', context)
    
@login_required
def retsept_list(request):
    barcha_retseptlar = (
        Retsept.objects
        .select_related("retsept_nomi", "maxsulot")
        .order_by("date")
    )

    korilgan_guruhlar = set()
    grouped = {}

    for r in barcha_retseptlar:
        # Guruhlash asoslari
        boshlanish = r.date - timedelta(minutes=1)
        tugash = r.date + timedelta(minutes=1)
        guruh_uniq_key = (r.retsept_nomi.id, r.date.strftime('%Y-%m-%d %H:%M'))

        if guruh_uniq_key in korilgan_guruhlar:
            continue

        guruh = (
            Retsept.objects
            .select_related("retsept_nomi", "maxsulot")
            .filter(
                retsept_nomi=r.retsept_nomi,
                date__range=(boshlanish, tugash)
            )
        )

        # 🔹 FIFO bo‘yicha tan narx hisoblash
        jami_tan_narxi = 0

        for item in guruh:
            needed_miqdor = item.miqdor
            partiyalar = (
                SkladRetsept.objects
                .filter(maxsulot=item.maxsulot)
                .order_by("olingan_sana")
            )

            for partiya in partiyalar:
                if needed_miqdor <= 0:
                    break

                if partiya.qancha_qolgani >= needed_miqdor:
                    jami_tan_narxi += needed_miqdor * partiya.narxi_donasi
                    needed_miqdor = 0
                else:
                    jami_tan_narxi += partiya.qancha_qolgani * partiya.narxi_donasi
                    needed_miqdor -= partiya.qancha_qolgani

            if needed_miqdor > 0:
                jami_tan_narxi = None
                break  # omborda yetarli emas, chiqib ketamiz

        grouped[(r.retsept_nomi, r.date)] = {
            "nom": r.retsept_nomi,
            "vaqt": r.date,
            "items": guruh,
            "tan_narxi": jami_tan_narxi
        }

        korilgan_guruhlar.add(guruh_uniq_key)

    sorted_grouped = OrderedDict(
        sorted(grouped.items(), key=lambda x: x[0][1], reverse=True)
    )

    return render(request, "retsept_list.html", {"retseptlar": sorted_grouped})




# def capture_plate(request):
#     if request.method == "POST":
#         ip = request.POST.get("ip")
#         if not ip:
#             return JsonResponse({"error": "Kamera IP topilmadi"}, status=400)
        
#         cap = cv2.VideoCapture(ip)
#         ret, frame = cap.read()
#         cap.release()

#         if not ret:
#             return JsonResponse({"error": "Kadr olinmadi"}, status=500)

#         reader = easyocr.Reader(['en', 'ru'])
#         results = reader.readtext(frame)
        
#         if results:
#             plate = results[0][1]
#             return JsonResponse({"plate": plate})
#         else:
#             return JsonResponse({"error": "Raqam topilmadi"}, status=404)

#     return JsonResponse({"error": "Noto‘g‘ri so‘rov"}, status=405)