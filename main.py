"""
🏁 ОСНОВНОЙ МОДУЛЬ ЗАПУСКА БОТОВ

▌ Особенности:
✔ Проверка всех зависимостей перед запуском
✔ Детальное логирование инициализации
✔ Гибкая обработка ошибок
✔ Корректное завершение работы
✔ Поддержка кодировки UTF-8
"""

import os
import sys
import asyncio
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# ====================
# 🛠 НАСТРОЙКА СИСТЕМЫ
# ====================

def configure_environment():
    """Настраивает кодировку и окружение"""
    if sys.platform == "win32":
        # Для Windows явно устанавливаем UTF-8
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    
    # Проверяем наличие .env файла
    if not os.path.exists('.env'):
        raise FileNotFoundError("Отсутствует .env файл")

def setup_logging() -> logging.Logger:
    """Настраивает систему логирования"""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.FileHandler('app.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

# ====================
# 🔍 ПРОВЕРКА ЗАВИСИМОСТЕЙ
# ====================

def check_dependencies() -> None:
    """Проверяет наличие всех необходимых компонентов"""
    required_files = {
        'Google Sheets Credentials': 'secure/client_secret.json',
        'Environment File': '.env'
    }
    
    for name, path in required_files.items():
        if not os.path.exists(path):
            raise FileNotFoundError(f"{name} не найден: {path}")

# ====================
# ⚙️ КОНФИГУРАЦИЯ
# ====================

class BotConfig:
    """Управление конфигурацией ботов"""
    
    def __init__(self):
        load_dotenv()
        self.tokens = {
            'client': os.getenv("CLIENT_BOT_TOKEN"),
            'admin': os.getenv("ADMIN_BOT_TOKEN")
        }
        self._validate()
    
    def _validate(self) -> None:
        """Проверяет обязательные параметры"""
        for name, token in self.tokens.items():
            if not token:
                raise ValueError(f"Не задан {name.upper()}_BOT_TOKEN в .env")
    
    def get(self, bot_type: str) -> str:
        """Возвращает токен для указанного бота"""
        return self.tokens.get(bot_type, '')

# ====================
# 🤖 УПРАВЛЕНИЕ БОТАМИ
# ====================

async def run_bot_safely(bot_runner, token: str, name: str) -> None:
    """
    Безопасный запуск бота с обработкой ошибок
    
    Args:
        bot_runner: Функция запуска бота
        token: Токен бота
        name: Название бота для логов
    """
    try:
        logger.info(f"Запускаем {name}...")
        await bot_runner(token)
    except asyncio.CancelledError:
        logger.info(f"{name}: Корректное завершение работы")
    except Exception as e:
        logger.critical(f"{name}: Критическая ошибка - {str(e)}", exc_info=True)
        raise

async def run_all_bots(config: BotConfig) -> None:
    """Запускает всех ботов параллельно"""
    from bots import run_client_bot, run_admin_bot
    
    tasks = [
        asyncio.create_task(run_bot_safely(run_client_bot, config.get('client'), "Клиентский бот")),
        asyncio.create_task(run_bot_safely(run_admin_bot, config.get('admin'), "Админ-панель"))
    ]
    
    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        # Отменяем все задачи при ошибке
        for task in tasks:
            task.cancel()
        raise

# ====================
# 🏁 ТОЧКА ВХОДА
# ====================

def main() -> int:
    """Основная функция запуска"""
    try:
        # Инициализация
        configure_environment()
        global logger
        logger = setup_logging()
        
        logger.info("="*50)
        logger.info("ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ")
        logger.info("="*50)
        
        # Проверки
        check_dependencies()
        config = BotConfig()
        
        # Запуск
        asyncio.run(run_all_bots(config))
        return 0
        
    except Exception as e:
        logger.critical(f"ФАТАЛЬНАЯ ОШИБКА: {str(e)}", exc_info=True)
        return 1
    finally:
        logger.info("="*50)
        logger.info("ПРИЛОЖЕНИЕ ЗАВЕРШИЛО РАБОТУ")
        logger.info("="*50)

if __name__ == "__main__":
    sys.exit(main())