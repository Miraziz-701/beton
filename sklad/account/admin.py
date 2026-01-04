from django.contrib import admin
from account.models import (Jonativchi,  Mijoz, Obyekt, Asosiy, Kamera, Guruh, Mashina, KirimTuri, User, SkladProducts, Orders,
SkladYetkazuvchi, ChiqimTuri, ChiqimTotal, Ishchi, SkladRetsept, SementZavod, Sklad, Retsept, DetailXomashyo, BetonMarkasi, NaqdObyekts, PriObyekts)

# Register your models here.

admin.site.register(Jonativchi)
# admin.site.register(Maxsulot)
admin.site.register(Mijoz)
admin.site.register(Obyekt)
admin.site.register(Kamera)
admin.site.register(Guruh)  
admin.site.register(Mashina)  
admin.site.register(KirimTuri)  
admin.site.register(User)
admin.site.register(SkladProducts)  
admin.site.register(SkladYetkazuvchi)
admin.site.register(ChiqimTuri)
admin.site.register(ChiqimTotal)
admin.site.register(Ishchi)
admin.site.register(SkladRetsept)
admin.site.register(SementZavod)
admin.site.register(Sklad)
admin.site.register(Retsept)    
admin.site.register(DetailXomashyo)
admin.site.register(BetonMarkasi)
admin.site.register(NaqdObyekts)
admin.site.register(PriObyekts)
admin.site.register(Orders)


@admin.register(Asosiy)
class AsosiyAdmin(admin.ModelAdmin):
    list_display = ('tashkilot_nomi', 'kim_tomonidan_jonatilgani', 'maxsulot_markasi', 'obyekt_id', 'qogozdagi_maxsulot_soni', 'maxsulot_soni', 'kamera', 'mashina', 'date')