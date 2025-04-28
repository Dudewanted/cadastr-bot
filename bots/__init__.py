"""
Пакет bots содержит модули для телеграм-ботов:
- client_bot.py - бот для взаимодействия с клиентами
- admin_bot.py - бот для администратора

При инициализации пакета выполняется проверка зависимостей.
"""

import logging
from importlib.metadata import version, PackageNotFoundError

# Настройка логгера для пакета
_logger = logging.getLogger(__name__)

# Проверка необходимых зависимостей
REQUIRED_PACKAGES = [
    'python-dotenv',
    'pyTelegramBotAPI',
    'gspread',
    'oauth2client'
]

def check_dependencies():
    """Проверяет наличие и версии требуемых пакетов"""
    missing_packages = []
    for package in REQUIRED_PACKAGES:
        try:
            v = version(package)
            _logger.info(f"Пакет {package} найден (версия {v})")
        except PackageNotFoundError:
            missing_packages.append(package)
            _logger.error(f"Пакет {package} не найден")
    
    if missing_packages:
        raise ImportError(
            f"Отсутствуют необходимые пакеты: {', '.join(missing_packages)}. "
            "Установите их через pip install -r requirements.txt"
        )

# При импорте пакета автоматически проверяем зависимости
try:
    check_dependencies()
except ImportError as e:
    _logger.critical(str(e))
    raise

# Импорт основных классов для удобного доступа
from .client_bot import ClientBot  # noqa
from .admin_bot import AdminBot    # noqa

__all__ = ['ClientBot', 'AdminBot']