"""
Модуль для работы с Google Sheets API
Версия: 2.0
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """Сервис для работы с Google Sheets"""

    def __init__(self, creds_path: str, spreadsheet_name: str):
        """
        Инициализация сервиса

        Args:
            creds_path (str): Путь к файлу учетных данных
            spreadsheet_name (str): Название таблицы
        """
        self.creds_path = Path(creds_path)
        self.spreadsheet_name = spreadsheet_name
        self.worksheet = None
        self._authorize()

    def _authorize(self):
        """Авторизация в Google API"""
        try:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.file",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_name(str(self.creds_path), scope)
            client = gspread.authorize(creds)
            sheet = client.open(self.spreadsheet_name)
            self.worksheet = sheet.get_worksheet(0)
            logger.info("Авторизация прошла успешно")
        except Exception as e:
            logger.exception("Ошибка авторизации")

    def append_row(self, data: list):
        """Добавление строки в таблицу"""
        try:
            self.worksheet.append_row(data, value_input_option="USER_ENTERED")
            logger.info("Строка добавлена в таблицу")
        except Exception as e:
            logger.exception("Ошибка при добавлении строки")

    def update_status(self, row_id: str, status: str):
        """Обновление колонки 'Статус' (5-я колонка)"""
        try:
            row_index = int(row_id)
            self.worksheet.update_cell(row_index, 5, status)
            logger.info(f"Статус строки {row_id} обновлён на {status}")
        except Exception as e:
            logger.exception("Ошибка при обновлении статуса")


# 🎯 Экземпляр для использования
creds_file_path = "D:/programming/cadastr-bot/secure/cadastr-bots/client_secret.json"
spreadsheet_name = "Кадастровые заявки"

gs_service = GoogleSheetsService(creds_file_path, spreadsheet_name)

# ✏️ Утилиты
def append_to_sheet(data: list):
    gs_service.append_row(data)

def update_status(row_id: str, status: str):
    gs_service.update_status(row_id, status)
