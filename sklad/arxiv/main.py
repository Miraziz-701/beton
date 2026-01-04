# --- 0) STD imports ---
import os, sys, asyncio, logging
from pathlib import Path
from dotenv import load_dotenv

# --- 1) PYTHONPATH ni to'g'rilash (manage.py turgan ildizga) ---
BASE_DIR = Path(__file__).resolve().parents[1]   # .../sklad/  (main.py: .../sklad/telegram-bot/main.py)
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# --- 2) Env va Django sozlash ---
load_dotenv(BASE_DIR / ".env")                   # ixtiyoriy: .env ildizda bo'lsa
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sklad.settings")  # settings modul nomi
import django
django.setup()                                   # MUHIM: handler importidan OLDIN

# --- 3) Endi aiogram/handlerlarni import qiling ---
from aiogram import Bot
from handlers.start import disp                 # endi bu xavfsiz, chunki django.setup() chaqirildi

# --- 4) Botni ishga tushirish ---

load_dotenv()
BOT_TOKEN = os.getenv("TOKEN")

bot = Bot(token=BOT_TOKEN)

async def main():
    logging.basicConfig(level=logging.INFO)
    await disp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
