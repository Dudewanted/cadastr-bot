"""
Модуль для работы с Google Sheets API.
Обеспечивает взаимодействие с таблицей заявок.
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Путь к файлу учетных данных
CREDENTIALS_FILE = "D:/programming/cadastr-bot/secure/client_secret.json"

# Название таблицы и листа
SPREADSHEET_NAME = "Кадастровые заявки"
WORKSHEET_NAME = "Sheet1"  # или None для первого листа

def get_worksheet():
    """
    Получает объект листа Google Sheets.
    
    Returns:
        gspread.Worksheet: Объект листа таблицы
    
    Raises:
        Exception: Если не удалось подключиться к таблице
    """
    try:
        # Авторизация в Google API
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            CREDENTIALS_FILE, scope
        )
        client = gspread.authorize(credentials)
        
        # Открытие таблицы
        spreadsheet = client.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME) if WORKSHEET_NAME else spreadsheet.sheet1
        
        logger.info("Успешное подключение к Google Sheets")
        return worksheet
        
    except Exception as e:
        logger.error(f"Ошибка подключения к Google Sheets: {e}")
        raise

def append_to_sheet(address: str, phone: str):
    """
    Добавляет новую запись в таблицу заявок.
    
    Args:
        address (str): Адрес или геолокация объекта
        phone (str): Контактный телефон клиента
    
    Returns:
        bool: True если запись успешно добавлена
    
    Raises:
        Exception: Если произошла ошибка при записи
    """
    try:
        worksheet = get_worksheet()
        
        # Получаем все записи для определения следующего ID
        records = worksheet.get_all_records()
        next_id = len(records) + 1
        
        # Подготавливаем данные для записи
        row_data = [
            next_id,                  # ID
            address,                   # Адрес/Геолокация
            phone,                     # Телефон
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Дата
            "Новая"                    # Статус
        ]
        
        # Добавляем новую строку
        worksheet.append_row(row_data)
        
        logger.info(f"Успешно добавлена запись: ID {next_id}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при добавлении записи: {e}")
        raise