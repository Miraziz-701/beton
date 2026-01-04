import os
import sys
from pathlib import Path

# 🔥 1. PROJECT ROOT NI TOPAMIZ
BASE_DIR = Path(__file__).resolve().parents[1]  # -> C:/Users/.../sklad/sklad
PROJECT_ROOT = BASE_DIR.parent                 # -> C:/Users/.../sklad

# 🔥 2. PYTHON PATH GA QO‘SHAMIZ
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(BASE_DIR))

# 🔥 3. DJANGO SETUP
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sklad.settings")
django.setup()

# 🔥 4. ENDI QOLGAN IMPORTLAR
import asyncio
import logging
import sys as _sys

from loader import disp, bot

import handlers.naqd_start
import handlers.test
import handlers.register
import handlers.add_mijoz
import handlers.pri_start


async def main():
    await disp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(stream=_sys.stdout, level=logging.INFO)
    asyncio.run(main())
