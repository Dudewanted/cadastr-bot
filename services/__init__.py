"""
Инициализационный модуль пакета services

Экспортирует основные компоненты для работы с:
- Google Sheets API
- Другими сервисами (при добавлении)

Содержит:
- GoogleSheetsService - основной класс для работы с таблицами
- append_to_sheet - функция быстрой записи в таблицу
- get_worksheet - функция получения листа таблицы
"""

from .gsheets import (
    GoogleSheetsService,  # Основной сервисный класс
    append_to_sheet,      # Упрощенный интерфейс для добавления данных
    get_worksheet         # Упрощенный интерфейс для получения листа
)

# Определяем публичный API модуля
__all__ = [
    'GoogleSheetsService',
    'append_to_sheet', 
    'get_worksheet'
]

# Инициализация логгера
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

# Версия пакета
__version__ = '1.0.0'