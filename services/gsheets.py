import logging
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from dotenv import load_dotenv
import os

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Конфигурация Google Sheets
SHEET_ID = os.getenv('SHEET_ID')
SHEET_NAME = os.getenv('SHEET_NAME')
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')

def authorize_gspread():
    """Авторизация в Google Sheets API"""
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            SERVICE_ACCOUNT_FILE, scope)
        return gspread.authorize(creds)
    except Exception as e:
        logger.error(f"Authorization error: {e}")
        raise

def get_worksheet():
    """Получение рабочего листа"""
    try:
        gc = authorize_gspread()
        sheet = gc.open_by_key(SHEET_ID)
        return sheet.worksheet(SHEET_NAME)
    except Exception as e:
        logger.error(f"Error getting worksheet: {e}")
        raise

def append_to_sheet(data: list):
    """Добавление данных в таблицу"""
    try:
        worksheet = get_worksheet()
        worksheet.append_row(data)
        logger.info(f"Data appended to sheet: {data}")
    except Exception as e:
        logger.error(f"Error appending to sheet: {e}")
        raise

def get_last_row():
    """Получение последней строки"""
    try:
        worksheet = get_worksheet()
        return len(worksheet.get_all_values()) + 1
    except Exception as e:
        logger.error(f"Error getting last row: {e}")
        raise

def update_status(request_id: str, new_status: str):
    """Обновление статуса заявки"""
    try:
        worksheet = get_worksheet()
        records = worksheet.get_all_records()
        row_num = next((i+2 for i, r in enumerate(records) if str(r['ID']) == request_id), None)
        
        if row_num:
            worksheet.update_cell(row_num, 5, new_status)
            logger.info(f"Updated status for request {request_id} to {new_status}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        raise