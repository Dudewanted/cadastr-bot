import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from services.logger import logger
from config import Config

class GoogleSheetsService:
    """Класс для работы с Google Sheets API"""
    
    def __init__(self):
        """Инициализация подключения к Google Sheets"""
        try:
            # Настройка области видимости и авторизация
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                Config.SERVICE_ACCOUNT_FILE, scope)
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_key(Config.SPREADSHEET_ID).sheet1
            
            # Настройка кэширования
            self._cache = {}
            self._cache_expiry = timedelta(minutes=Config.CACHE_EXPIRY_MINUTES)
            
            logger.info("Успешное подключение к Google Sheets")
        except Exception as e:
            logger.error(f"Ошибка подключения к Google Sheets: {e}")
            raise

    def _is_cache_valid(self, key: str) -> bool:
        """
        Проверяет актуальность данных в кэше
        :param key: Ключ кэша
        :return: True если данные актуальны, иначе False
        """
        if key not in self._cache:
            return False
        cached_time, _ = self._cache[key]
        return datetime.now() - cached_time < self._cache_expiry
    
    def add_request(self, address: str, phone: str) -> bool:
        """
        Добавляет новую заявку в таблицу
        :param address: Адрес или геолокация объекта
        :param phone: Номер телефона клиента
        :return: True если успешно, иначе False
        """
        try:
            # Инвалидируем кэш при добавлении новой записи
            if 'all_requests' in self._cache:
                del self._cache['all_requests']
            
            # Получаем следующую свободную строку
            next_row = len(self.sheet.get_all_values()) + 1
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Заполняем данные в таблице
            self.sheet.update_cell(next_row, 1, next_row - 1)  # ID
            self.sheet.update_cell(next_row, 2, address)       # Адрес
            self.sheet.update_cell(next_row, 3, phone)         # Телефон
            self.sheet.update_cell(next_row, 4, current_date)  # Дата
            self.sheet.update_cell(next_row, 5, 'Новая')      # Статус
            
            logger.info(f"Добавлена новая заявка: {address}, {phone}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении заявки: {e}")
            return False
    
    def update_status(self, row_id: int, status: str) -> bool:
        """
        Обновляет статус заявки
        :param row_id: ID строки (начинается с 1)
        :param status: Новый статус
        :return: True если успешно, иначе False
        """
        try:
            self.sheet.update_cell(row_id + 1, 5, status)
            logger.info(f"Обновлен статус заявки {row_id} на '{status}'")
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления статуса: {e}")
            return False
    
    def get_new_requests(self, force_refresh=False) -> list:
        """
        Получает новые заявки (со статусом 'Новая')
        :param force_refresh: Если True, игнорирует кэш
        :return: Список новых заявок
        """
        cache_key = 'new_requests'
        
        # Проверяем кэш если не требуется принудительное обновление
        if not force_refresh and self._is_cache_valid(cache_key):
            _, data = self._cache[cache_key]
            logger.debug("Использованы кэшированные данные заявок")
            return data
            
        try:
            records = self.sheet.get_all_records()
            new_requests = [dict(row, id=idx+1) for idx, row in enumerate(records) 
                          if row.get('Статус') == 'Новая']
            
            # Обновляем кэш
            self._cache[cache_key] = (datetime.now(), new_requests)
            logger.info(f"Получено {len(new_requests)} новых заявок")
            return new_requests
        except Exception as e:
            logger.error(f"Ошибка получения заявок: {e}")
            return []