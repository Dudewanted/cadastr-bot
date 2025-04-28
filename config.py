import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

class Config:
    """Класс конфигурации приложения, содержит все настройки"""
    
    # Токены Telegram ботов
    CLIENT_BOT_TOKEN = os.getenv('CLIENT_BOT_TOKEN')  # Токен бота для клиентов
    ADMIN_BOT_TOKEN = os.getenv('ADMIN_BOT_TOKEN')    # Токен бота для администратора
    
    # Настройки Google Sheets
    SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')      # ID таблицы Google Sheets
    SERVICE_ACCOUNT_FILE = '/secure/client_secret.json'  # Путь к файлу сервисного аккаунта
    SHEET_RANGE = 'Кадастровые заявки!A:E'            # Диапазон данных в таблице
    
    # Настройки логирования
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')        # Уровень логирования (DEBUG, INFO, WARNING, ERROR)
    LOG_DIR = 'logs'                                  # Папка для хранения логов
    
    # Настройки напоминаний
    REMINDER_INTERVAL_HOURS = int(os.getenv('REMINDER_INTERVAL_HOURS', 24))  # Интервал напоминаний в часах
    ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')        # Chat ID администратора в Telegram
    
    # Настройки кэширования
    CACHE_EXPIRY_MINUTES = int(os.getenv('CACHE_EXPIRY_MINUTES', 5))  # Время жизни кэша в минутах