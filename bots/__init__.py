"""
🎛 ГЛАВНЫЙ МОДУЛЬ ПАКЕТА BOTS

▌ Основные компоненты:
├── 📞 client_bot - бот для клиентов
└── 🛠 admin_bot - бот для администратора

▌ Особенности:
✔ Поддержка Python 3.11+
✔ Безопасная работа с Unicode
✔ Четкое разделение ответственности
"""

import io
import sys
import logging
from typing import List

# Настройка кодировки для Windows
if sys.platform == "win32":
    sys.stdout = sys.__stdout__ = io.TextIOWrapper(
        sys.stdout.buffer, 
        encoding='utf-8', 
        errors='replace'
    )

# Логирование в файл с UTF-8
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s - %(name)s: %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bots.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Основные экспорты
from .client_bot import run_client_bot  # noqa: F401
from .admin_bot import run_admin_bot    # noqa: F401

__all__: List[str] = [
    'run_client_bot',
    'run_admin_bot'
]

__version__ = '2.3.1'
__author__ = 'GeodesicBot Team'

logger.info("Пакет bots успешно инициализирован")