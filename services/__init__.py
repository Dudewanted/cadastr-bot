"""
Пакет services содержит вспомогательные сервисы:
- gsheets.py - работа с Google Sheets API
- utils.py - валидация и утилиты
- logger.py - система логирования

При инициализации создается экземпляр логгера для всего пакета.
"""

import logging
from .logger import logger as package_logger

# Реэкспорт основных классов для удобного импорта
from .gsheets import GoogleSheetsService  # noqa
from .utils import Validator              # noqa
from .logger import BotLogger             # noqa

__all__ = ['GoogleSheetsService', 'Validator', 'BotLogger', 'package_logger']

# Инициализация логгера пакета
package_logger.info(f"Инициализирован пакет services")