"""
Пакет bots - реализация Telegram-ботов для кадастровых услуг

Экспортирует основные функции для управления ботами:
- run_client_bot - запуск бота для клиентов
- run_admin_bot - запуск бота для администратора

Версия: 2.0 (адаптировано под python-telegram-bot v20.x)
"""

# Основные экспортируемые функции
from .client_bot import run_client_bot  # noqa: F401
from .admin_bot import run_admin_bot    # noqa: F401

# Дополнительные утилиты (при необходимости)
#from .utils import (                   # noqa: F401
    #setup_logging,
    #validate_config
#)

# Определение публичного API пакета
__all__ = [
    'run_client_bot',
    'run_admin_bot',
    'setup_logging',
    'validate_config'
]

# Мета-данные пакета
__version__ = '2.0.0'
__author__ = 'Ваше имя/компания'
__license__ = 'MIT'

# Настройка логгера пакета
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

def get_version():
    """Возвращает текущую версию пакета"""
    return __version__