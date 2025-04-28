"""
🤖 КЛИЕНТСКИЙ БОТ ДЛЯ ГЕОДЕЗИЧЕСКИХ УСЛУГ

▌ Функционал:
├── Прием заявок с геолокацией
├── Сбор контактных данных
├── Интеграция с Google Sheets
└── Красивый интерфейс с меню

▌ Особенности реализации:
✔ Поддержка python-telegram-bot 20.x
✔ Обработка ошибок кодировки
✔ Настройка временных зон
"""

import io
import sys
import logging
import pytz
from datetime import datetime
from typing import Dict, Any

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.gsheets import append_to_sheet

# ====================
# 🔧 НАСТРОЙКИ СИСТЕМЫ
# ====================

# Кодировка для Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Временная зона
TIMEZONE = pytz.timezone('Europe/Moscow')

# Логирование
logging.basicConfig(
    format='▌ %(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('client_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ====================
# 🗂 СОСТОЯНИЯ БОТА
# ====================
(
    MAIN_MENU,
    GET_LOCATION,
    GET_PHONE
) = range(3)

# ====================
# 📝 ТЕКСТОВЫЕ ШАБЛОНЫ
# ====================
TEXTS = {
    'welcome': 
        """
        🏠 <b>ГЕОДЕЗИЧЕСКИЕ УСЛУГИ</b>

        Добро пожаловать! Чем могу помочь?
        """,
    
    'request': 
        """
        📍 <b>НОВАЯ ЗАЯВКА</b>
        
        Укажите местоположение объекта:
        """
}

# ====================
# 🖥 ОСНОВНЫЕ ФУНКЦИИ
# ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает главное меню"""
    buttons = [
        ["📨 Отправить заявку"],
        ["❓ Вопросы", "📞 Контакты"],
        ["ℹ️ О нас"]
    ]
    
    await update.message.reply_text(
        text=TEXTS['welcome'],
        reply_markup=ReplyKeyboardMarkup(
            buttons,
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        ),
        parse_mode='HTML'
    )
    return MAIN_MENU

async def setup_timezone(app: Application) -> None:
    """Настраивает временную зону для планировщика"""
    try:
        app.job_queue.scheduler = AsyncIOScheduler(timezone=TIMEZONE)
        logger.info(f"Установлена временная зона: {TIMEZONE}")
    except Exception as e:
        logger.error(f"Ошибка настройки временной зоны: {e}")
        raise

# ====================
# 🚀 ЗАПУСК БОТА
# ====================

def run_client_bot(token: str) -> None:
    """Основная функция запуска бота"""
    try:
        logger.info("Инициализация клиентского бота...")
        
        application = Application.builder() \
            .token(token) \
            .post_init(setup_timezone) \
            .build()
        
        # Настройка обработчиков
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                MAIN_MENU: [
                    MessageHandler(filters.Regex("^📨 Отправить заявку$"), start_request)
                ],
                GET_LOCATION: [
                    MessageHandler(filters.LOCATION, process_location),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, process_location)
                ],
                GET_PHONE: [
                    MessageHandler(filters.CONTACT, process_phone),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, process_phone)
                ]
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )
        
        application.add_handler(conv_handler)
        application.run_polling()
        
        logger.info("Бот успешно запущен")
        
    except Exception as e:
        logger.critical(f"Ошибка запуска бота: {e}")
        raise