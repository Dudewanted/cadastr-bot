"""
🏁 ОСНОВНОЙ МОДУЛЬ ЗАПУСКА БОТОВ

▌ Функционал:
├── 🚀 Запуск клиентского бота
├── 🛠 Запуск админ-панели
└── 🔄 Асинхронное управление

▌ Особенности реализации:
✔ Поддержка кодировки UTF-8
✔ Централизованное управление конфигурацией
✔ Обработка ошибок запуска
✔ Логирование инициализации
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# ====================
# ⚙️ НАСТРОЙКА СИСТЕМЫ
# ====================

# Настройка кодировки для Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Инициализация логирования
logging.basicConfig(
    format='🏁 [%(asctime)s] %(levelname)s - %(name)s: %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# ====================
# 📦 ИМПОРТ БОТОВ
# ====================

from bots.client_bot import run_client_bot
from bots.admin_bot import run_admin_bot

# ====================
# 🔧 КОНФИГУРАЦИЯ
# ====================

class Config:
    """Контейнер для настроек приложения"""
    def __init__(self):
        self.CLIENT_BOT_TOKEN = os.getenv("CLIENT_BOT_TOKEN")
        self.ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
        self.GSHEETS_CREDENTIALS = "secure/client_secret.json"
        
        self.validate()
    
    def validate(self):
        """Проверяет обязательные настройки"""
        if not self.CLIENT_BOT_TOKEN:
            raise ValueError("Не задан CLIENT_BOT_TOKEN")
        if not self.ADMIN_BOT_TOKEN:
            raise ValueError("Не задан ADMIN_BOT_TOKEN")
        if not os.path.exists(self.GSHEETS_CREDENTIALS):
            raise FileNotFoundError(f"Файл учетных данных не найден: {self.GSHEETS_CREDENTIALS}")

# ====================
# 🚀 ФУНКЦИИ ЗАПУСКА
# ====================

async def run_bots(config: Config) -> None:
    """Запускает ботов в асинхронном режиме"""
    tasks = [
        asyncio.create_task(_run_bot_safely(run_client_bot, config.CLIENT_BOT_TOKEN, "Клиентский бот")),
        asyncio.create_task(_run_bot_safely(run_admin_bot, config.ADMIN_BOT_TOKEN, "Админ-панель"))
    ]
    await asyncio.gather(*tasks)

async def _run_bot_safely(bot_runner, token: str, bot_name: str) -> None:
    """Безопасный запуск бота с обработкой ошибок"""
    try:
        logger.info("Запускаем %s...", bot_name)
        await bot_runner(token)
    except Exception as e:
        logger.critical("Ошибка в работе %s: %s", bot_name, e, exc_info=True)
        raise

# ====================
# 🏁 ТОЧКА ВХОДА
# ====================

def main() -> None:
    """Основная функция запуска приложения"""
    try:
        logger.info("Инициализация приложения...")
        
        # Загрузка конфигурации
        config = Config()
        logger.info("Конфигурация успешно загружена")
        
        # Запуск ботов
        asyncio.run(run_bots(config))
        
    except Exception as e:
        logger.critical("Критическая ошибка: %s", e, exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Приложение завершило работу")

if __name__ == "__main__":
    main()