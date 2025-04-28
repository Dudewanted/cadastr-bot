import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import os
from datetime import datetime
from typing import Dict, List, Optional, Union

load_dotenv()

class GoogleSheetsManager:
    def __init__(self):
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(
            os.getenv('SERVICE_ACCOUNT_PATH'), self.scope)
        self.client = gspread.authorize(self.creds)
        self.sheet = self.client.open(os.getenv('SPREADSHEET_NAME', 'Кадастровые заявки'))
        self.worksheet = self.sheet.get_worksheet(0)
        
        # Кэш для хранения данных о последних заявках
        self._last_requests_cache = []
        self._last_update_time = datetime.min

    def _get_all_records(self, force_update: bool = False) -> List[Dict]:
        """Получает все записи с кэшированием на 1 минуту"""
        current_time = datetime.now()
        if force_update or (current_time - self._last_update_time).seconds > 60 or not self._last_requests_cache:
            self._last_requests_cache = self.worksheet.get_all_records()
            self._last_update_time = current_time
        return self._last_requests_cache

    def add_request(self, address: str, phone: str) -> bool:
        """
        Добавляет новую заявку в таблицу
        :param address: Адрес или геолокация
        :param phone: Номер телефона
        :return: True если успешно, False если ошибка
        """
        try:
            # Проверка на дубликаты по адресу и телефону
            existing = self.worksheet.findall(address)
            if existing:
                return False
                
            # Генерация ID (максимальный существующий + 1)
            all_records = self._get_all_records(force_update=True)
            new_id = max([int(r.get('ID', 0)) for r in all_records] + [0]) + 1
            
            self.worksheet.append_row([
                new_id,
                address,
                phone,
                datetime.now().strftime("%d.%m.%Y %H:%M"),
                "Новая"  # Статус по умолчанию
            ])
            
            # Обновляем кэш
            self._get_all_records(force_update=True)
            return True
            
        except Exception as e:
            print(f"[Google Sheets Error] add_request: {str(e)}")
            return False

    def get_pending_requests(self) -> List[Dict[str, Union[str, int]]]:
        """
        Получает все заявки со статусом 'Новая'
        :return: Список словарей с заявками
        """
        try:
            records = self._get_all_records()
            return [r for r in records if r.get('Статус', '') == 'Новая']
        except Exception as e:
            print(f"[Google Sheets Error] get_pending_requests: {str(e)}")
            return []

    def update_status(self, request_id: Union[str, int], new_status: str) -> bool:
        """
        Обновляет статус заявки
        :param request_id: ID заявки
        :param new_status: Новый статус
        :return: True если успешно, False если ошибка
        """
        try:
            # Находим строку с нужным ID
            cell = self.worksheet.find(str(request_id))
            if not cell:
                return False
                
            # Обновляем статус (5 столбец)
            self.worksheet.update_cell(cell.row, 5, new_status)
            
            # Обновляем кэш
            self._get_all_records(force_update=True)
            return True
            
        except Exception as e:
            print(f"[Google Sheets Error] update_status: {str(e)}")
            return False

    def get_request_by_id(self, request_id: Union[str, int]) -> Optional[Dict]:
        """
        Получает заявку по ID
        :param request_id: ID заявки
        :return: Словарь с данными заявки или None если не найдена
        """
        try:
            records = self._get_all_records()
            for r in records:
                if str(r.get('ID', '')) == str(request_id):
                    return r
            return None
        except Exception as e:
            print(f"[Google Sheets Error] get_request_by_id: {str(e)}")
            return None

# Создаем глобальный экземпляр для использования в других модулях
gsheets_manager = GoogleSheetsManager()

# Функции для обратной совместимости
def add_request(address: str, phone: str) -> bool:
    return gsheets_manager.add_request(address, phone)

def get_pending_requests() -> List[Dict]:
    return gsheets_manager.get_pending_requests()

def update_status(request_id: Union[str, int], new_status: str) -> bool:
    return gsheets_manager.update_status(request_id, new_status)

def get_request_by_id(request_id: Union[str, int]) -> Optional[Dict]:
    return gsheets_manager.get_request_by_id(request_id)