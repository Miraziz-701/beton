from aiogram import Dispatcher, Bot
from django.conf import settings
from aiogram.client.default import DefaultBotProperties

disp = Dispatcher()
bot = Bot(token=settings.TOKEN, default=DefaultBotProperties(parse_mode='HTML'))