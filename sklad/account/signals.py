from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Asosiy
from account.utils.google_script import send_zakaz_to_google

@receiver(post_save, sender=Asosiy)
def zakaz_google_sync(sender, instance, created, **kwargs):
    if created and instance.kim_tomonidan_jonatilgani:
        send_zakaz_to_google(instance)
