"""
🎛 ГЛАВНЫЙ МОДУЛЬ ПАКЕТА BOTS

▌ Назначение:
  Инициализация и экспорт основных компонентов ботов

▌ Экспортирует:
  ├── run_client_bot - запуск клиентского бота
  └── run_admin_bot - запуск админ-панели

▌ Особенности:
  ✔ Поддержка UTF-8 для логов
  ✔ Автоматическая настройка кодировки
  ✔ Единый стиль логирования
"""

import sys
import logging
from typing import List

# ====================
# 🛠 НАСТРОЙКА ЛОГИРОВАНИЯ
# ====================
def _configure_logging():
    """Настраивает систему логирования с UTF-8 кодировкой"""
    formatter = logging.Formatter(
        fmt='[%(asctime)s] %(name)s: %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    handlers = [
        logging.FileHandler('bots.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]

    for handler in handlers:
        handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=handlers
    )

_configure_logging()
logger = logging.getLogger(__name__)

# ====================
# 📦 ЭКСПОРТ КОМПОНЕНТОВ
# ====================
try:
    from .client_bot import run_client_bot
    from .admin_bot import run_admin_bot
    
    __all__: List[str] = [
        'run_client_bot',
        'run_admin_bot'
    ]
    
    __version__ = '2.5.0'
    __author__ = 'GeodesicBot Team'
    
    logger.info("Пакет bots успешно инициализирован (v%s)", __version__)
    
except ImportError as e:
    logger.critical("Ошибка импорта компонентов: %s", e)
    raise