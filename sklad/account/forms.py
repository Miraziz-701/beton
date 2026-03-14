from django import forms
from django.utils import timezone
from django.db.models import Sum, Max
from django.contrib.auth.forms import AuthenticationForm
from account.models import (User, Asosiy, Mijoz,  Obyekt, Jonativchi, Kamera, BetonMarkasi, Guruh, Kirim,
KirimTuri, Sklad, SkladProducts, SkladYetkazuvchi, Retsept, ChiqimTuri, ChiqimTotal, Ishchi, KelmaganIshchilar, Agents)
from django.forms import modelformset_factory

class AdminLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Password'
    }))
    
    class Meta:
        model = User
        fields = ('username', 'password')


class AddProductForm(forms.ModelForm):
    kim_tomonidan_jonatilgani = forms.ModelChoiceField(
        queryset=Agents.objects.all().order_by("full_name"),
        empty_label="Tanlang...",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    tashkilot_nomi = forms.CharField(
        required=False,   
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'list': "tashkilot_list",
            'placeholder': 'Masalan: YTM-3'
        })
    )

    umumiy_maxsulot = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    izoh_qoshish = forms.BooleanField(
        required=False,
        label="Izoh qo‘shish",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_izoh_qoshish'})
    )

    izoh_matni = forms.CharField(
        required=False,
        label="Izoh matni",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Masalan',
            'id': 'id_izoh_matni'
        })
    )

    qogozdagi_maxsulot_soni = forms.FloatField(widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'placeholder': 'Soni'
    }))

    maxsulot_soni = forms.FloatField(widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'placeholder': 'Soni'
    }))

    obyekt_text = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'list': 'obyekt_list',
            'placeholder': 'Obyektni tanlang'
    }))


    kamera = forms.ModelChoiceField(
        queryset=Kamera.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'Tanlang...'
        })
    )

    mashina = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': '01 A 123 BB',
        'id': 'mashinaInput',
        'name': "mashina",
        'list': "mashinaSuggestions",  # 👈 faqat 'list', 'datalist' emas!
        'autocomplete': 'off'
    }))

    class Meta:
        model = Asosiy
        # exclude = ['mashina', 'mijoz', 'kim_tomonidan_jonatilgani', 'obyekt_nomi']
        fields = ('kim_tomonidan_jonatilgani', 'qogozdagi_maxsulot_soni', 'maxsulot_soni', 'kamera')
    


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Beton markalari
        beton_choices = [(f"beton_{m.id}", f"{m.markasi}") for m in BetonMarkasi.objects.all()]
        # Sklad mahsulotlari
        sklad_choices = [(f"xomashyo_{s.id}", f"{s.maxsulot_nomi}") for s in SkladProducts.objects.all()]

        self.fields['umumiy_maxsulot'].choices = [("", "Tanlang...")] + beton_choices + sklad_choices

    def clean(self):
        cleaned_data = super().clean()
        umumiy = cleaned_data.get("umumiy_maxsulot")
        izoh_qoshish = cleaned_data.get("izoh_qoshish")
        izoh_matni = cleaned_data.get("izoh_matni")

        if umumiy:
            if umumiy.startswith("beton_"):
                beton_id = umumiy.replace("beton_", "")
                cleaned_data["maxsulot_markasi"] = BetonMarkasi.objects.get(id=beton_id)
                cleaned_data["xomashyo"] = None
                cleaned_data["izoh_qoshish"] = False
                cleaned_data["izoh_matni"] = ""

            elif umumiy.startswith("xomashyo_"):
                xom_id = umumiy.replace("xomashyo_", "")
                cleaned_data["xomashyo"] = SkladProducts.objects.get(id=xom_id)
                cleaned_data["maxsulot_markasi"] = None

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        umumiy = self.cleaned_data.get("umumiy_maxsulot")
        izoh_qoshish = self.cleaned_data.get("izoh_qoshish")
        izoh_matni = self.cleaned_data.get("izoh_matni")

        if umumiy:
            if umumiy.startswith("beton_"):
                beton_id = umumiy.replace("beton_", "")
                instance.maxsulot_markasi = BetonMarkasi.objects.get(id=beton_id)
                instance.xomashyo = None
                instance.xomashyo_izohi = ""
            elif umumiy.startswith("xomashyo_"):
                xom_id = umumiy.replace("xomashyo_", "")
                instance.xomashyo = SkladProducts.objects.get(id=xom_id)
                instance.maxsulot_markasi = None

                if izoh_qoshish and izoh_matni.strip():
                    instance.xomashyo_izohi = izoh_matni.strip()
                else:
                    instance.xomashyo_izohi = ""

        if commit:
            instance.save()
        return instance

class AddTestProductForm(forms.ModelForm):
    kim_tomonidan_jonatilgani = forms.ModelChoiceField(
        queryset=Agents.objects.all().order_by("full_name"),
        empty_label="Tanlang...",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    tashkilot_nomi = forms.CharField(
        required=False,   
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'list': "tashkilot_list",
            'placeholder': 'Masalan: YTM-3'
        })
    )

    obyekt_id = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Obyektni tanlang',
        'list': 'obyekt_list'
    }))

    maxsulot_markasi = forms.ModelChoiceField(
        queryset=BetonMarkasi.objects.all().order_by("markasi"),
        empty_label="Tanlang...",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    qogozdagi_maxsulot_soni = forms.FloatField(widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'name': 'q_soni',
        'placeholder': 'Masalan: 1 ta'
    }))

    maxsulot_soni = forms.FloatField(widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'name': 'r_soni',
        'placeholder': 'Masalan: 1 ta'
    }))

    kamera = forms.ModelChoiceField(
        queryset=Kamera.objects.all().order_by("kamera_nomi"),
        empty_label="Tanlang...",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    mashina = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'name': 'mashina',
        'placeholder': '01 A 001 AA'
    }))

    class Meta:
        model = Asosiy
        fields = ('kim_tomonidan_jonatilgani', 'tashkilot_nomi', 'obyekt_id', 'maxsulot_markasi', 
                  'qogozdagi_maxsulot_soni', 'maxsulot_soni', 'kamera', 'mashina')


class AddMijozForm(forms.ModelForm):
    ism_familya = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'name': 'ism_familya',
        'placeholder': 'Ism Familya'
    }))

    telefon_raqami = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'name': 'telefon_raqami',
        'placeholder': '+998 ** *** ** **'
    }))

    class Meta:
        model = Mijoz
        fields = ('ism_familya', 'telefon_raqami')

class ChangeJonatuvchiForm(forms.ModelForm):
    ism_familya = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'name': 'ism_familya',
        'placeholder': 'Ism Familya'
    }))

    class Meta:
        model = Jonativchi
        fields = ('ism_familya',)

# class AddMaxsulotForm(forms.ModelForm):
#     nomi = forms.CharField(widget=forms.TextInput(attrs={
#         'class': 'form-control',
#         'name': 'maxsulot_nomi',
#         'placeholder': 'Nomi'
#     }))

#     soni = forms.IntegerField(widget=forms.NumberInput(attrs={
#         'class': 'form-control',
#         'name': 'maxsulot_soni',
#         'placeholder': 'Soni'
#     }))

#     class Meta:
#         model = Maxsulot
#         fields = ('nomi', 'soni')

class AddObyektForm(forms.ModelForm):
    obyekt_nomi = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'name': 'obyekt_nomi',
        'placeholder': 'Obyekt nomi'
    })) 

    class Meta:
        model = Obyekt
        fields = ('obyekt_nomi',)

class AddJonatuvchiForm(forms.ModelForm):
    ism_familya = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'name': 'ism_familya',
        'placeholder': 'Ism Familya'
    }))


    class Meta:
        model = Jonativchi
        fields = ('ism_familya',)

class AddKameraForm(forms.ModelForm):
    kamera_nomi = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'name': 'kamera_nomi',
        'placeholder': 'Kamera nomi'
    }))

    kamera_ip = forms.CharField(widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'name': 'kamera_ip',
            'placeholder': 'IP Address'
        }
    ))

    class Meta:
        model = Kamera
        fields = ('kamera_nomi', 'kamera_ip')

class AddBetonMarkaForm(forms.ModelForm):
    markasi = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'name': 'beton_markasi',
        'placeholder': 'Beton markasi'
    }))

    class Meta:
        model = BetonMarkasi
        fields = ('markasi',)

class AddXojayinForm(forms.ModelForm):
    xojayini = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'name': 'xojayini',
        'id': 'xojayini',
        'placeholder': 'Masalan: Asadbek'
    }))

    class Meta:
        model = Guruh
        fields = ('xojayini',)


class AddKirimForm(forms.ModelForm):
    turi = forms.ModelChoiceField(
        queryset=KirimTuri.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'name': 'turi',
            'required': True,
            'placeholder': 'Tanlang...'
        })
    )

    k_o_kelgani = forms.ModelChoiceField(
        queryset=Jonativchi.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'name': 'k_o_kelgani',
            'required': True,
            'placeholder': 'Tanlang...',
            'id': 'k_o_kelganiSelect'
        })
    )

    summa = forms.CharField(
        widget=forms.TextInput(attrs={
            'id': 'summa',
            'class': 'form-control',
            'placeholder': 'Masalan: 500 000',
            'required': True
        })
    )




    izoh = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'name': 'izoh',
            'rows': 2,
            'placeholder': 'Izoh kiriting...',
            'required': True
        })
    )
    
    checked = forms.ChoiceField(
        choices=Kirim.CHECK_CHOICE,
        widget=forms.RadioSelect()
    )

    sana = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }
        )
    )
    
    def clean_summa(self):
        value = self.cleaned_data['summa']
        value = value.replace(' ', '')  # probellarni olib tashlash
        if not value.isdigit():
            raise forms.ValidationError("Faqat raqam kiriting")
        return int(value)
    
    

    class Meta:
        model = Kirim
        fields = ('turi', 'k_o_kelgani', 'summa', 'izoh', 'checked', 'sana')


class AddSkladProductsForm(forms.ModelForm):
    maxsulot_nomi = forms.ModelChoiceField(
        queryset=SkladProducts.objects.all(),
        empty_label="Mahsulot nomi", 
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'nomi',
            'required': True
        })
    )

    maxsulot_miqdori = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'miqdor',
            'placeholder': 'Soni',
            'min': 0,
            'required': True
        })
    )

    maxsulot_narxi = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'narx',
            'placeholder': 'Narxi',
            'min': 0,
            'required': True
        })
    )

    tolov_turi = forms.ChoiceField(
        choices=Sklad.TOLOV_CHOICE,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
            'required': True
        })
    )

    yetkazuvchi = forms.ModelChoiceField(
        queryset=SkladYetkazuvchi.objects.all(),
        empty_label="Yetkazib beruvchi", 
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'yetkazuvchi',
            'required': True
        })
    )

    zavod = forms.ModelChoiceField(
        queryset=Kamera.objects.all(),
        empty_label="Zavod",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'zavod'
        })
    )

    izoh = forms.CharField(
        required=False, 
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'id': 'izoh',
            'rows': 3,
            'placeholder': 'Qo‘shimcha ma’lumot'
        })
    )

    sana = forms.DateTimeField(
        required=False,   # ← optional qildik
        initial=timezone.now,  
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local',
            'id': 'sana'
        })
    )

    def clean_maxsulot_narxi(self):
        value = self.cleaned_data.get("maxsulot_narxi")

        if value:
            value = value.replace(" ", "")
            return int(value)

        return value
    
    class Meta:
        model = Sklad
        fields = ('maxsulot_nomi', 'maxsulot_miqdori', 'maxsulot_narxi', 'tolov_turi', 'yetkazuvchi', 'zavod', 'izoh', 'sana')



class AddYetkazibBeruvchiForm(forms.ModelForm):
    class Meta:
        model = SkladYetkazuvchi
        fields = ["yetkazib_beruvchi"]   # modeldagi field bilan mos
        widgets = {
            "yetkazib_beruvchi": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Yangi yetkazib beruvchi nomi"
            })
        }

class AddRetseptForm(forms.ModelForm):
    retsept_nomi = forms.ModelChoiceField(
        queryset=BetonMarkasi.objects.all(),
        empty_label="Retsept turi",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'retsept',
        }),
        required=False   # ❗❗ majburiy emas qilamiz
    )

    maxsulot = forms.ModelChoiceField(
        queryset=SkladProducts.objects.all(),
        empty_label="Maxsulot",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'maxsulot',
            'required': True
        })
    )

    miqdor = forms.DecimalField(
        max_digits=7,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'class': 'form-control',
            'name': 'miqdor',
            'placeholder': 'Miqdori',
            'required': True
        })
    )

    class Meta:
        model = Retsept
        fields = ('retsept_nomi', 'maxsulot', 'miqdor')

RetseptFormSet = modelformset_factory(
    Retsept,
    form=AddRetseptForm,
    extra=1,        # faqat 1 ta bo‘sh forma chiqadi
    can_delete=True
)


class IshchiChoiceField(forms.ChoiceField):
    def to_python(self, value):
        if not value:
            return None
        # oldin get() edi, endi filter + order_by ishlatamiz
        return Ishchi.objects.filter(ism_familya=value).order_by('-qachon_tugashi').first()


class AddChiqimForm(forms.ModelForm):
    chiqim_turi = forms.ModelChoiceField(
        queryset=ChiqimTuri.objects.all().exclude(chiqim_nomi='Haydovchiga'),
        empty_label='Chiqim Turi',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'chiqimTuri',
            'required': True,
        })
    )

    yetkazuvchi = forms.ModelChoiceField(
        queryset=SkladYetkazuvchi.objects.all(),
        required=False,
        empty_label='Yetkazib beruvchi',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'yetkazibBeruvchi',
        })
    )

    ishchi = IshchiChoiceField(
        choices=[(i["ism_familya"], i["ism_familya"])
                 for i in Ishchi.objects.values("ism_familya").distinct()],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'ishchi',
        })
    )

    summa = forms.IntegerField(
        widget=forms.TextInput(attrs={
            'id': 'id_summa',
            'class': 'form-control',
            'placeholder': 'Summa',
            'required': True,
        })
    )

    tolov_turi = forms.ChoiceField(
        choices=ChiqimTotal.TURI,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )

    izoh = forms.CharField(
        required=False,   # ❗ bu yerda yozish kerak
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'id': 'izoh',
            'rows': 2,
            'placeholder': 'Qo‘shimcha ma’lumot',
        })
    )

    vaqti = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'id': 'sana',
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )

    class Meta:
        model = ChiqimTotal
        fields = ('chiqim_turi', 'ishchi', 'yetkazuvchi', 'summa', 'tolov_turi', 'izoh', 'vaqti')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ishchi'].choices = [
            (i["ism_familya"], i["ism_familya"])
            for i in Ishchi.objects.values("ism_familya").distinct()
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        new_choices = [("", "Yetkazib beruvchi")]  # empty_label qo‘lda qo‘shamiz

        for y in self.fields['yetkazuvchi'].queryset:
            # 1. Sklad bo‘yicha jami qarz
            umumiy_kirim = (
                Sklad.objects.filter(yetkazuvchi=y)
                .aggregate(total=Sum('jami_maxsulot_narxi'))['total']
                or 0
            )

            # 2. ChiqimTotal bo‘yicha shu yetkazuvchiga qilingan to‘lovlar
            jami_chiqim = (
                ChiqimTotal.objects.filter(yetkazuvchi=y)
                .aggregate(total=Sum('summa'))['total']
                or 0
            )

            # 3. Farq = qarz - to‘langan
            qarz = umumiy_kirim - jami_chiqim

            # Formatlash
            qarz_str = f"{qarz:,}".replace(",", " ")
            new_choices.append((y.id, f"{y.yetkazib_beruvchi} {qarz_str} so'm"))

        self.fields['yetkazuvchi'].choices = new_choices
    
    
    
    def clean_vaqti(self):
        vaqti = self.cleaned_data.get("vaqti")
        if not vaqti:
            return timezone.now()
        return vaqti
    
class AddIshchiForm(forms.ModelForm):
    ism_familya = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'id': 'ism_familya',
            'name': 'ism_familya',
            'class': 'form-control',
            'placeholder': 'Ism Familya'
        })
    )

    oyligi = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'id': 'oyligi',
            'name': 'oyligi',
            'class': 'form-control',
            'placeholder': 'Oyligi'
        })
    )

    qachondan_olishi = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'qachondan_olishi'
        })
    )

    class Meta:
        model = Ishchi
        fields = ('ism_familya', 'oyligi', 'qachondan_olishi')
    
    def clean_oyligi(self):
        value = self.cleaned_data['oyligi']
        # faqat raqamlarni qoldiramiz
        value = value.replace(" ", "").replace(",", "")
        try:
            return int(value)
        except ValueError:
            raise forms.ValidationError("Faqat raqam kiriting.")

class AddKelmaganIshchilarForm(forms.ModelForm):
    ishchi = forms.ModelChoiceField(
        queryset=Ishchi.objects.filter(
            id__in=Ishchi.objects.values("ism_familya")
            .annotate(last_id=Max("id"))
            .values_list("last_id", flat=True)
        ),
        required=True,
        empty_label="Ishchi",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'ishchi'})
    )

    izoh = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'id': 'izoh',
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Izoh'
        })
    )

    sana = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'id': 'sana',
            'class': 'form-control'
        })
    )

    class Meta:
        model = KelmaganIshchilar
        fields = ('ishchi', 'izoh', 'sana')