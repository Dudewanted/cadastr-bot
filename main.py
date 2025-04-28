"""
Главный модуль для запуска ботов
"""

import os
import asyncio
from dotenv import load_dotenv
from bots.client_bot import run_client_bot
from bots.admin_bot import run_admin_bot

# Загрузка переменных окружения
load_dotenv()

async def main():
    """Запуск ботов в асинхронном режиме"""
    client_task = asyncio.create_task(
        run_client_bot(os.getenv("CLIENT_BOT_TOKEN"))
    )
    admin_task = asyncio.create_task(
        run_admin_bot(os.getenv("ADMIN_BOT_TOKEN"))
    )
    
    await asyncio.gather(client_task, admin_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Боты остановлены")
    except Exception as e:
        print(f"Ошибка: {e}")