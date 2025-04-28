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
                "https://www.googleapis.com/auth/drive"
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                str(self.creds_path), scope
            )
            client = gspread.authorize(creds)
            spreadsheet = client.open(self.spreadsheet_name)
            self.worksheet = spreadsheet.sheet1
            logger.info("Успешная авторизация в Google Sheets")
        except Exception as e:
            logger.error(f"Ошибка авторизации: {e}")
            raise

    def append_request(self, address: str, phone: str) -> bool:
        """
        Добавление новой заявки
        
        Args:
            address (str): Адрес или координаты
            phone (str): Номер телефона
            
        Returns:
            bool: True если успешно
        """
        try:
            next_row = len(self.worksheet.get_all_values()) + 1
            row_data = [
                next_row,  # ID
                address,
                phone,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Новая"  # Статус
            ]
            self.worksheet.append_row(row_data)
            logger.info(f"Добавлена заявка ID {next_row}")
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления заявки: {e}")
            return False

    def update_status(self, request_id: int, status: str) -> bool:
        """
        Обновление статуса заявки
        
        Args:
            request_id (int): ID заявки
            status (str): Новый статус
            
        Returns:
            bool: True если успешно
        """
        try:
            cell = self.worksheet.find(str(request_id))
            self.worksheet.update_cell(cell.row, 5, status)
            logger.info(f"Обновлен статус заявки {request_id} на '{status}'")
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления статуса: {e}")
            return False

# Функции для обратной совместимости
def append_to_sheet(address: str, phone: str):
    """Упрощенный интерфейс для добавления заявки"""
    service = GoogleSheetsService(
        creds_path="D:/programming/cadastr-bot/secure/client_secret.json",
        spreadsheet_name="Кадастровые заявки"
    )
    return service.append_request(address, phone)

def get_worksheet():
    """Упрощенный интерфейс для получения листа"""
    service = GoogleSheetsService(
        creds_path="D:/programming/cadastr-bot/secure/client_secret.json",
        spreadsheet_name="Кадастровые заявки"
    )
    return service.worksheet