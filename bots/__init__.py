"""
🎯 ПАКЕТ BOTS - ЯДРО ТЕЛЕГРАМ-БОТОВ ДЛЯ ГЕОДЕЗИЧЕСКИХ УСЛУГ

▌ Основные компоненты:
├── 📞 Клиентский бот (client_bot.py)
├── 🛠 Админ-панель (admin_bot.py)
└── 🛡 Утилиты (utils.py)

▌ Особенности:
✔ Поддержка python-telegram-bot v20+
✔ Интеграция с Google Sheets
✔ Логирование всех событий
✔ Гибкая система плагинов
"""

__version__ = '2.2.0'
__author__ = 'Geodesic Services'
__license__ = 'GPL-3.0'

import logging
from typing import Optional

# Инициализация системы логирования
logging.basicConfig(
    format='▌ %(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bots_runtime.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Основной интерфейс пакета
from .client_bot import run_client_bot  # noqa: F401
from .admin_bot import run_admin_bot    # noqa: F401
from .utils import (                   # noqa: F401
    setup_webhook,
    validate_config,
    BotError
)

# Автоматическая настройка при импорте
try:
    logger.info(f"🌀 Инициализация пакета bots v{__version__}")
    logger.debug("Проверка зависимостей...")
    
    import pytz
    from telegram import __version__ as tg_ver
    
    logger.info(f"✔ Telegram bot API v{tg_ver}")
    logger.info("Пакет успешно инициализирован\n" + "─" * 50)
    
except ImportError as e:
    logger.critical(f"❌ Ошибка зависимостей: {e}")
    raise

# Публичный API пакета
__all__ = [
    'run_client_bot',
    'run_admin_bot',
    'setup_webhook',
    'validate_config',
    'BotError'
]

def get_bot_version(bot_type: str) -> Optional[str]:
    """
    🏷 Получение версии конкретного бота
    
    Аргументы:
        bot_type: 'client' | 'admin'
        
    Возвращает:
        str: Версия бота или None если не найдено
    """
    versions = {
        'client': '2.2.0',
        'admin': '1.5.0'
    }
    return versions.get(bot_type.lower())

class BotConfig:
    """🔧 Конфигурация ботов (синглтон)"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_config()
        return cls._instance
    
    def _init_config(self):
        self.DEFAULT_TZ = 'Europe/Moscow'
        self.MAX_FILE_SIZE = 20  # MB
        self.REQUEST_TIMEOUT = 30  # seconds