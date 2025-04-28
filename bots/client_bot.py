import logging
from telebot import TeleBot, types
from telebot.types import ReplyKeyboardRemove
from config import Config
from services.gsheets import GoogleSheetsService
from services.utils import Validator
from services.logger import logger

class ClientBot:
    """Класс бота для взаимодействия с клиентами"""
    
    def __init__(self):
        """Инициализация бота"""
        self.bot = TeleBot(Config.CLIENT_BOT_TOKEN)
        self.gsheets = GoogleSheetsService()
        self.user_data = {}  # Для временного хранения данных пользователя между шагами
        
        # Регистрация обработчиков
        self._register_handlers()
        logger.info("Клиентский бот инициализирован")
    
    def _register_handlers(self):
        """Регистрирует все обработчики команд и сообщений"""
        
        # Обработчик команды /start
        @self.bot.message_handler(commands=['start'])
        def start(message):
            logger.info(f"Новый пользователь: {message.chat.id}")
            self._show_main_menu(message.chat.id)
        
        # Обработчик команды /cancel
        @self.bot.message_handler(commands=['cancel'])
        def cancel(message):
            chat_id = message.chat.id
            if chat_id in self.user_data:
                del self.user_data[chat_id]
                logger.info(f"Пользователь {chat_id} отменил действие")
            self._show_main_menu(chat_id)
        
        # Обработчик геолокации
        @self.bot.message_handler(content_types=['location'])
        def handle_location(message):
            chat_id = message.chat.id
            if chat_id in self.user_data and 'waiting_for_location' in self.user_data[chat_id]:
                if Validator.validate_location(message.location.latitude, message.location.longitude):
                    address = f"Геолокация: {message.location.latitude}, {message.location.longitude}"
                    self.user_data[chat_id]['address'] = address
                    del self.user_data[chat_id]['waiting_for_location']
                    logger.info(f"Получена геолокация от {chat_id}: {address}")
                    self._request_phone(chat_id)
                else:
                    self.bot.send_message(chat_id, "Неверные координаты. Пожалуйста, попробуйте еще раз.")
            else:
                self.bot.send_message(chat_id, "Пожалуйста, используйте меню для отправки геолокации.")
        
        # Обработчик контактов (телефона)
        @self.bot.message_handler(content_types=['contact'])
        def handle_contact(message):
            chat_id = message.chat.id
            if chat_id in self.user_data and 'waiting_for_phone' in self.user_data[chat_id]:
                phone = message.contact.phone_number
                self._process_phone(chat_id, phone)
        
        # Обработчик текстовых сообщений
        @self.bot.message_handler(func=lambda message: True)
        def handle_text(message):
            chat_id = message.chat.id
            if chat_id in self.user_data:
                if 'waiting_for_address' in self.user_data[chat_id]:
                    if Validator.validate_address(message.text):
                        self._process_address(chat_id, message.text)
                    else:
                        self.bot.send_message(chat_id, "Адрес слишком короткий. Пожалуйста, укажите полный адрес.")
                elif 'waiting_for_phone' in self.user_data[chat_id]:
                    self._process_phone(chat_id, message.text)
            else:
                self.bot.send_message(chat_id, "Пожалуйста, используйте меню.")
        
        # Обработчик callback-запросов (нажатий на кнопки)
        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_query(call):
            chat_id = call.message.chat.id
            try:
                if call.data == 'send_request':
                    self._init_request_process(chat_id)
                elif call.data == 'send_location':
                    self._request_location(chat_id)
                elif call.data == 'send_address':
                    self._request_address(chat_id)
                elif call.data == 'send_phone':
                    self._request_phone(chat_id)
                elif call.data == 'faq':
                    self._show_faq(chat_id)
                elif call.data == 'contacts':
                    self._show_contacts(chat_id)
                elif call.data == 'about':
                    self._show_about(chat_id)
                elif call.data == 'main_menu':
                    self._show_main_menu(chat_id)
                elif call.data.startswith('faq_'):
                    question = call.data[4:]
                    self._answer_faq(chat_id, question)
            except Exception as e:
                logger.error(f"Ошибка обработки callback: {e}")
                self.bot.send_message(chat_id, "Произошла ошибка. Пожалуйста, попробуйте позже.")
    
    # Далее идут все вспомогательные методы класса (show_main_menu, init_request_process и т.д.)
    # Они остаются такими же, как в предыдущем примере, но с добавленным логированием
    
    def run(self):
        """Запускает бота в режиме опроса сервера Telegram"""
        logger.info("Запуск клиентского бота")
        self.bot.polling(none_stop=True, interval=1)

if __name__ == '__main__':
    bot = ClientBot()
    bot.run()