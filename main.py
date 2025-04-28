from bots.client_bot import ClientBot
from bots.admin_bot import AdminBot
import threading
from services.logger import logger

def run_client_bot():
    """Запускает бота для клиентов"""
    try:
        client_bot = ClientBot()
        client_bot.run()
    except Exception as e:
        logger.error(f"Ошибка в клиентском боте: {e}")

def run_admin_bot():
    """Запускает бота для администратора"""
    try:
        admin_bot = AdminBot()
        admin_bot.run()
    except Exception as e:
        logger.error(f"Ошибка в админском боте: {e}")

if __name__ == '__main__':
    logger.info("Запуск системы ботов")
    
    # Запускаем оба бота в разных потоках
    client_thread = threading.Thread(target=run_client_bot)
    admin_thread = threading.Thread(target=run_admin_bot)
    
    client_thread.start()
    admin_thread.start()
    
    # Ожидаем завершения потоков (хотя они должны работать бесконечно)
    client_thread.join()
    admin_thread.join()