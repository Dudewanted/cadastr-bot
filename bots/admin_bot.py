import threading
import time
from datetime import datetime, timedelta
from telebot import TeleBot, types
from config import Config
from services.gsheets import GoogleSheetsService
from services.logger import logger

class AdminBot:
    """Класс бота для администратора"""
    
    def __init__(self):
        """Инициализация бота"""
        self.bot = TeleBot(Config.ADMIN_BOT_TOKEN)
        self.gsheets = GoogleSheetsService()
        self.last_update = None
        
        # Настройка системы напоминаний
        self.reminder_interval = timedelta(hours=Config.REMINDER_INTERVAL_HOURS)
        self.reminder_thread = threading.Thread(target=self._run_reminders, daemon=True)
        self.reminder_thread.start()
        
        # Регистрация обработчиков
        self._register_handlers()
        logger.info("Админский бот инициализирован")
    
    def _register_handlers(self):
        """Регистрирует все обработчики команд"""
        
        @self.bot.message_handler(commands=['start'])
        def start(message):
            logger.info(f"Администратор вошел: {message.chat.id}")
            self._show_admin_menu(message.chat.id)
        
        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_query(call):
            chat_id = call.message.chat.id
            try:
                if call.data.startswith('call_'):
                    phone = call.data[5:]
                    self._show_call_confirmation(chat_id, phone)
                elif call.data.startswith('status_'):
                    parts = call.data.split('_')
                    row_id = int(parts[1])
                    new_status = parts[2]
                    self._update_request_status(chat_id, row_id, new_status)
                elif call.data == 'refresh':
                    self._check_new_requests(chat_id, force_refresh=True)
            except Exception as e:
                logger.error(f"Ошибка обработки callback: {e}")
                self.bot.send_message(chat_id, "Произошла ошибка. Пожалуйста, попробуйте позже.")
    
    def _run_reminders(self):
        """Запускает фоновый поток для проверки необработанных заявок"""
        logger.info("Запуск системы напоминаний")
        while True:
            try:
                now = datetime.now()
                if (self.last_reminder_check is None or 
                    now - self.last_reminder_check >= timedelta(minutes=10)):
                    
                    self._check_pending_requests()
                    self.last_reminder_check = now
                    logger.debug("Проверка необработанных заявок выполнена")
                
                time.sleep(600)  # Ожидание 10 минут
            except Exception as e:
                logger.error(f"Ошибка в потоке напоминаний: {e}")
                time.sleep(60)
    
    # Далее идут все вспомогательные методы класса (show_admin_menu, check_new_requests и т.д.)
    # Они остаются такими же, как в предыдущем примере, но с добавленным логированием
    
    def run(self):
        """Запускает бота в режиме опроса сервера Telegram"""
        logger.info("Запуск админского бота")
        self.bot.polling(none_stop=True, interval=1)

if __name__ == '__main__':
    bot = AdminBot()
    bot.run()