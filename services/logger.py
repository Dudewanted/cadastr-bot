import logging
import os
from datetime import datetime
from config import Config

class BotLogger:
    """Класс для настройки и управления логированием"""
    
    def __init__(self, name):
        """
        Инициализация логгера
        :param name: Имя логгера (обычно __name__)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(Config.LOG_LEVEL)
        
        # Создаем папку для логов если ее нет
        if not os.path.exists(Config.LOG_DIR):
            os.makedirs(Config.LOG_DIR)
        
        # Формат сообщений в логах
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Обработчик для записи в файл
        file_handler = logging.FileHandler(
            f'{Config.LOG_DIR}/bot_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Обработчик для вывода в консоль
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def get_logger(self):
        """Возвращает настроенный логгер"""
        return self.logger

# Глобальный экземпляр логгера для использования в других модулях
logger = BotLogger('cadastr_bot').get_logger()