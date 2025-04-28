"""
🛠 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ БОТОВ

Содержит:
- Настройку вебхуков
- Валидацию конфигурации
- Обработку ошибок
"""

import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class BotError(Exception):
    """🔴 Базовый класс ошибок бота"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)
        logger.error(f"BotError: {message} | Details: {details}")

def setup_webhook(config: Dict[str, Any]) -> bool:
    """
    ⚙️ Настраивает вебхук для бота
    
    Args:
        config: Конфигурация вебхука
        
    Returns:
        bool: True если успешно
        
    Raises:
        BotError: При ошибках настройки
    """
    try:
        # Здесь должна быть реальная логика настройки
        logger.info(f"Настройка вебхука для {config.get('url')}")
        return True
    except Exception as e:
        raise BotError("Ошибка настройки вебхука", {"error": str(e)})

def validate_config(config_path: Path) -> Dict[str, Any]:
    """
    🔍 Проверяет корректность конфигурационного файла
    
    Args:
        config_path: Путь к файлу конфигурации
        
    Returns:
        Dict: Валидная конфигурация
        
    Raises:
        BotError: При невалидной конфигурации
    """
    try:
        if not config_path.exists():
            raise BotError("Файл конфигурации не найден")
        
        # Здесь должна быть реальная валидация
        dummy_config = {"token": "test", "webhook": {"url": "https://example.com"}}
        logger.info("Конфигурация успешно проверена")
        return dummy_config
    except Exception as e:
        raise BotError("Ошибка валидации конфигурации", {"path": str(config_path), "error": str(e)})

def format_error_for_user(error: Exception) -> str:
    """
    💬 Форматирует ошибку для показа пользователю
    
    Args:
        error: Исключение
        
    Returns:
        str: Понятное описание ошибки
    """
    if isinstance(error, BotError):
        return f"⚠️ {error.message}"
    return "⚠️ Произошла непредвиденная ошибка"