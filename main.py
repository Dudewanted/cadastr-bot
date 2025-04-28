"""
🏁 ОСНОВНОЙ МОДУЛЬ ЗАПУСКА БОТОВ
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Настройка кодировки
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Логирование
logging.basicConfig(
    format='🏁 [%(asctime)s] %(levelname)s - %(name)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def load_config():
    """Загружает конфигурацию с проверкой"""
    load_dotenv()
    
    config = {
        'client_token': os.getenv("CLIENT_BOT_TOKEN"),
        'admin_token': os.getenv("ADMIN_BOT_TOKEN"),
        'gsheets_creds': "secure/client_secret.json"
    }
    
    # Проверка обязательных параметров
    if not config['client_token']:
        logger.error("Не задан CLIENT_BOT_TOKEN в .env файле")
        sys.exit(1)
        
    if not config['admin_token']:
        logger.error("Не задан ADMIN_BOT_TOKEN в .env файле")
        sys.exit(1)
        
    if not os.path.exists(config['gsheets_creds']):
        logger.error(f"Файл учетных данных не найден: {config['gsheets_creds']}")
        sys.exit(1)
        
    return config

async def run_bot(bot_func, token, name):
    """Безопасный запуск бота"""
    try:
        logger.info("Запуск %s...", name)
        await bot_func(token)
    except Exception as e:
        logger.critical("Ошибка в %s: %s", name, e)
        raise

async def main_async():
    """Асинхронная точка входа"""
    config = load_config()
    
    # Запуск ботов параллельно
    await asyncio.gather(
        run_bot(run_client_bot, config['client_token'], "Клиентский бот"),
        run_bot(run_admin_bot, config['admin_token'], "Админ-панель")
    )

def main():
    """Точка входа"""
    try:
        logger.info("Инициализация приложения...")
        asyncio.run(main_async())
    except Exception as e:
        logger.critical("Фатальная ошибка: %s", e)
        sys.exit(1)
    finally:
        logger.info("Приложение завершено")

if __name__ == "__main__":
    main()