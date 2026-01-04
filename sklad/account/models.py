from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from asgiref.sync import sync_to_async


# Create your models here.

class User(AbstractUser):
    pass

class Jonativchi(models.Model):
    ism_familya = models.CharField()

    def __str__(self):
        return self.ism_familya


class Mijoz(models.Model):
    ism_familya = models.CharField()
    telefon_raqami = models.CharField(null=True)
    telegram_id = models.IntegerField(default=0)

    def __str__(self):
        return self.ism_familya

class Obyekt(models.Model):
    obyekt_nomi = models.CharField()

    def __str__(self):
        return self.obyekt_nomi


class Agents(models.Model):
    full_name = models.CharField()
    telegram_id = models.IntegerField(unique=True)

    def __str__(self):
        return self.full_name

class NaqdObyekts(models.Model):
    obyekt_name = models.CharField()
    location_name = models.TextField()
    location_full = models.TextField()
    location_lat = models.CharField(null=True)
    location_lon = models.CharField(null=True)

    def __str__(self):
        return self.obyekt_name
    
class PriObyekts(models.Model):
    obyekt_name = models.CharField()    
    tashkilot_name = models.TextField()
    location_name = models.TextField()
    location_full = models.TextField()
    location_lat = models.CharField(null=True)
    location_lon = models.CharField(null=True)

    def __str__(self):
        return self.obyekt_name


# class Kamera(models.Model):
#     kamera_nomi = models.CharField()
    
#     def __str__(self):
#         return self.kamera_nomi

class BetonMarkasi(models.Model):
    markasi = models.CharField()

    def __str__(self):
        return self.markasi
    
class Orders(models.Model):
    agent = models.ForeignKey(to=Agents, on_delete=models.CASCADE)
    money_type = models.CharField()
    obyekt_id = models.IntegerField()
    product = models.ForeignKey(to=BetonMarkasi, on_delete=models.CASCADE)
    quantity = models.FloatField()
    price = models.IntegerField()
    otkat = models.FloatField(default=0)
    time = models.TextField()
    description = models.TextField()
    phone_number = models.CharField(max_length=9)
    date = models.DateField(auto_now_add=True)



class Kamera(models.Model):
    kamera_nomi = models.CharField()
    kamera_ip = models.TextField()

    def __str__(self):
        return self.kamera_nomi

class Mashina(models.Model):
    mashina_raqami = models.CharField()
    telefon_raqami = models.CharField()
    telegram_id = models.IntegerField(default=0)

    def __str__(self):
        return self.mashina_raqami

class Guruh(models.Model):
    xojayini = models.CharField()
    mashinalar = models.ForeignKey(to=Mashina, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.xojayini

class KirimTuri(models.Model):
    kirim_nomi = models.CharField()

    def __str__(self):
        return self.kirim_nomi


class SkladYetkazuvchi(models.Model):
    yetkazib_beruvchi = models.CharField()

    def __str__(self):
        return self.yetkazib_beruvchi
    

class SkladProducts(models.Model):
    maxsulot_nomi = models.CharField()
    soni = models.BigIntegerField(default=0)
    birlik = models.CharField(null=True)

    def __str__(self):
        return self.maxsulot_nomi


class Sklad(models.Model):

    TOLOV_CHOICE = [
        ('N', 'N'),
        ('P', 'P')    
    ]

    maxsulot_nomi = models.ForeignKey(to=SkladProducts, on_delete=models.CASCADE)
    maxsulot_miqdori = models.IntegerField()
    maxsulot_narxi = models.IntegerField()
    jami_maxsulot_narxi = models.BigIntegerField(default=0)
    tolov_turi = models.CharField(max_length=1, choices=TOLOV_CHOICE)
    yetkazuvchi = models.ForeignKey(to=SkladYetkazuvchi, on_delete=models.CASCADE)
    zavod = models.ForeignKey(to=Kamera, on_delete=models.CASCADE, null=True)
    izoh = models.TextField(null=True, blank=True)
    sana = models.DateTimeField()

    def __str__(self):
        return str(self.maxsulot_nomi)
    
class DetailXomashyo(models.Model):
    maxsulot = models.ForeignKey(to=BetonMarkasi, on_delete=models.CASCADE, null=True)
    xomashyo = models.ForeignKey(to=SkladProducts, on_delete=models.CASCADE)
    izoh = models.TextField(default="")
    miqdori = models.DecimalField(max_digits=7, decimal_places=2)
    narxi_donasi = models.FloatField()
    total_narx = models.FloatField()
    zavod = models.ForeignKey(to=Kamera, on_delete=models.CASCADE, null=True)
    vaqti = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.xomashyo)
    
class SkladRetsept(models.Model):
    maxsulot = models.ForeignKey(to=SkladProducts, on_delete=models.CASCADE)
    zavod = models.ForeignKey(to=Kamera, on_delete=models.CASCADE, null=True, blank=True)
    keltirilgan_miqdor = models.IntegerField()
    qancha_qolgani = models.IntegerField()
    narxi_donasi = models.IntegerField()
    olingan_sana = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.maxsulot)
    

class SementZavod(models.Model):
    sement_nomi = models.ForeignKey(to=SkladProducts, on_delete=models.CASCADE)
    sement_miqdori = models.BigIntegerField(default=0)
    zavod = models.ForeignKey(to=Kamera, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.sement_nomi)


class Retsept(models.Model):
    retsept_nomi = models.ForeignKey(to=BetonMarkasi, on_delete=models.CASCADE)
    maxsulot = models.ForeignKey(to=SkladProducts, on_delete=models.CASCADE)
    miqdor = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.retsept_nomi)

class Kirim(models.Model):

    CHECK_CHOICE = [
        ('N', 'N'),
        ('P', 'P')    
    ]

    turi = models.ForeignKey(to=KirimTuri, on_delete=models.CASCADE)
    k_o_kelgani = models.ForeignKey(to=Jonativchi, on_delete=models.CASCADE)
    summa = models.IntegerField()
    izoh = models.TextField(null=False)
    checked = models.CharField(max_length=1, choices=CHECK_CHOICE)
    sana = models.DateTimeField()

    def __str__(self):
        return self.turi

class ChiqimMashina(models.Model):
    TOLOV = [
        ('N', 'N'),
        ('P', 'P')
    ]

    mashina_raqami = models.ForeignKey(to=Mashina, on_delete=models.CASCADE)
    mijoz = models.ForeignKey(to=Mijoz, on_delete=models.CASCADE)
    obyekt_nomi = models.ForeignKey(to=Obyekt, on_delete=models.CASCADE)
    mashina_egasi = models.ForeignKey(to=Guruh, on_delete=models.CASCADE, null=True)
    berilgan_narx = models.IntegerField(default=0)
    zavod = models.ForeignKey(to=Kamera, on_delete=models.CASCADE)
    tolov_turi = models.CharField(max_length=1, choices=TOLOV)
    vaqt = models.DateTimeField(default=timezone.now)


class ChiqimTuri(models.Model):
    chiqim_nomi = models.CharField()

    def __str__(self):
        return self.chiqim_nomi



class Ishchi(models.Model):
    ism_familya = models.CharField()
    oyligi = models.IntegerField()
    qachondan_olishi = models.DateField(default=timezone.now)
    qachon_tugashi = models.DateField(null=True, blank=True)
    kelmagan_kuni = models.IntegerField(default=0)
    jami_beriladigan_summa = models.IntegerField(default=0)
    berilgan_puli = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        # Agar qachondan_olishi berilgan bo‘lsa → tugash sanasini hisoblab qo‘yamiz
        if self.qachondan_olishi:
            self.qachon_tugashi = self.qachondan_olishi + relativedelta(months=+1)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.ism_familya


class KelmaganIshchilar(models.Model):
    ishchi = models.ForeignKey(to=Ishchi, on_delete=models.CASCADE)
    izoh = models.CharField(null=True)
    sana = models.DateField(default=timezone.now)


class ChiqimTotal(models.Model):
    TURI = [
        ('N', 'N'),
        ('P', 'P')
    ]

    chiqim_turi = models.ForeignKey(to=ChiqimTuri, on_delete=models.CASCADE)
    ishchi = models.ForeignKey(to=Ishchi, on_delete=models.CASCADE, null=True)
    mijoz = models.ForeignKey(to=Mijoz, on_delete=models.CASCADE, null=True)
    maxsulot_markasi = models.ForeignKey(to=BetonMarkasi, on_delete=models.CASCADE, null=True)
    maxsulot_nomi = models.ForeignKey(to=SkladProducts, on_delete=models.CASCADE, null=True)
    miqdori = models.FloatField(null=True)
    k_kelgani = models.ForeignKey(to=Jonativchi, on_delete=models.CASCADE, null=True)
    yetkazuvchi = models.ForeignKey(to=SkladYetkazuvchi, on_delete=models.CASCADE, null=True)
    summa = models.BigIntegerField(default=0)
    mashina_raqami = models.ForeignKey(to=Mashina, on_delete=models.CASCADE, null=True)
    mashina_egasi = models.ForeignKey(to=Guruh, on_delete=models.CASCADE, null=True)
    tolov_turi = models.CharField(max_length=1, choices=TURI)
    izoh = models.CharField(null=True)
    zavod = models.ForeignKey(to=Kamera, on_delete=models.CASCADE, null=True)
    vaqti = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.chiqim_turi)




class Asosiy(models.Model):
    tashkilot_nomi = models.ForeignKey(to=PriObyekts, on_delete=models.CASCADE, null=True, blank=True)
    kim_tomonidan_jonatilgani = models.ForeignKey(to=Agents, on_delete=models.CASCADE)
    maxsulot_markasi = models.ForeignKey(to=BetonMarkasi, on_delete=models.CASCADE, null=True, blank=True)
    xomashyo = models.ForeignKey(to=SkladProducts, on_delete=models.CASCADE, null=True, blank=True)
    xomashyo_izohi = models.TextField(default="", blank=True)
    obyekt_id = models.IntegerField()
    qogozdagi_maxsulot_soni = models.FloatField()
    maxsulot_soni = models.FloatField()
    kamera = models.ForeignKey(to=Kamera, on_delete=models.CASCADE)
    mashina = models.ForeignKey(to=Mashina, on_delete=models.CASCADE)
    mijoz_qoygan_narx = models.IntegerField(default=0)
    mijoz_jami_qoygan_narx = models.BigIntegerField(default=0)
    maxsulot_tan_narx = models.BigIntegerField(default=0)
    mijoz_bergan_narx = models.BigIntegerField(default=0)
    haydovchi_qoygan_narx = models.IntegerField(default=0)
    haydovchiga_berilgan_narx = models.IntegerField(default=0)
    xarajat_narxi = models.IntegerField(default=0)
    xarajat_izohi = models.CharField(null=True, blank=True)
    qoshimcha_xarajat = models.BooleanField(default=False)
    mijoz_narx_qoyildi = models.BooleanField(default=False)
    haydovchi_narx_qoyildi = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    checked = models.BooleanField(default=False)
    tan_narxi_qoyildi = models.BooleanField(default=False)
    all_checked = models.BooleanField(default=False)

    @property
    def qolgan_summa(self):
        return self.mijoz_jami_qoygan_narx - self.mijoz_bergan_narx
    
    @property
    def foyda(self):
        return self.mijoz_jami_qoygan_narx - self.maxsulot_tan_narx
    
    @property
    def obyekt_nomi(self):
        if self.tashkilot_nomi:
            obyekt = PriObyekts.objects.filter(pk=self.obyekt_id).first()
        else:
            obyekt = NaqdObyekts.objects.filter(pk=self.obyekt_id).first()

        return obyekt.obyekt_name if obyekt else "-"


    def __str__(self):
        return self.date.strftime('%Y-%m-%d')
    
class data:

    @sync_to_async
    def check_agent(self, telegram_id: int):
        return Agents.objects.filter(telegram_id=telegram_id).first()
    
    @sync_to_async
    def add_naqd_obyekt(self, obyekt_name, location_name, location_full, location_lat, location_lon):
        return NaqdObyekts.objects.create(
            obyekt_name=obyekt_name,
            location_name=location_name,
            location_full=location_full,
            location_lat=location_lat,
            location_lon=location_lon
        )
    
    @sync_to_async
    def add_pri_obyekt(self, obyekt_name, tashkilot_name, location_name, location_full,  location_lat, location_lon):
        return PriObyekts.objects.create(
            obyekt_name=obyekt_name,
            tashkilot_name=tashkilot_name,
            location_name=location_name,
            location_full=location_full,
            location_lat=location_lat,
            location_lon=location_lon
        )
    
    @sync_to_async
    def select_naqd_obyekt_id(self, obyekt_name):
        return NaqdObyekts.objects.filter(obyekt_name=obyekt_name).values_list('id', flat=True).first()
    
    @sync_to_async
    def select_pri_obyekt_id(self, obyekt_name):
        return PriObyekts.objects.filter(obyekt_name=obyekt_name).values_list('id', flat=True).first()
    
    @sync_to_async
    def add_agent(self, full_name, telegram_id):
        return Agents.objects.create(full_name=full_name, telegram_id=telegram_id)

    @sync_to_async
    def see_product_id(self, product_name):
        return BetonMarkasi.objects.filter(markasi=product_name).values_list('id', flat=True).first()
    
    @sync_to_async
    def select_agent_id(self, telegram_id):
        return Agents.objects.filter(telegram_id=telegram_id).values_list('id', flat=True).first()
    
    @sync_to_async
    def add_order(self, agent_id, money_type, obyekt_id, product_id, quantity, price, time, description, phone_number, otkat=0):
        return Orders.objects.create(agent_id=agent_id, money_type=money_type, obyekt_id=obyekt_id, product_id=product_id, quantity=quantity, price=price, otkat=otkat, time=time, description=description, phone_number=phone_number)

    @sync_to_async
    def see_products(self):
        return list(
            BetonMarkasi.objects.values_list("markasi", flat=True)
        )
    
    @sync_to_async
    def see_naqd_obyekts(self):
        return list(NaqdObyekts.objects.values_list('obyekt_name', flat=True))
    
    @sync_to_async
    def see_pri_obyekts(self):
        return list(PriObyekts.objects.values_list('obyekt_name', flat=True))

    @sync_to_async
    def see_naqd_obyekt_info(self, obyekt_name): 
        return NaqdObyekts.objects.filter(obyekt_name=obyekt_name).values_list('location_name', 'location_full', 'location_lat', 'location_lon').first()

    @sync_to_async
    def see_pri_obyekt_info(self, obyekt_name): 
        return PriObyekts.objects.filter(obyekt_name=obyekt_name).values_list('tashkilot_name', 'location_name', 'location_full', 'location_lat', 'location_lon').first()

    @sync_to_async  
    def select_agent(self, telegram_id):
        return Agents.objects.filter(telegram_id=telegram_id).values_list('full_name', flat=True).first()
    