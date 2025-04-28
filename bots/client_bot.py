"""
🤖 КЛИЕНТСКИЙ БОТ ДЛЯ ГЕОДЕЗИЧЕСКИХ УСЛУГ

▌ Основной функционал:
├── 📍 Прием геолокации/адреса
├── 📞 Сбор контактных данных
├── 📊 Интеграция с Google Sheets
└── 🎨 Удобный интерфейс с меню

▌ Особенности реализации:
✔ Поддержка python-telegram-bot 20.x
✔ Корректная обработка Unicode (emoji, кириллица)
✔ Подробное логирование всех операций
✔ Настройка временной зоны (Europe/Moscow)
"""

import sys
import logging
import pytz
from datetime import datetime
from typing import Dict, Any

# ====================
# ⚙️ НАСТРОЙКА СИСТЕМЫ
# ====================

# Установка временной зоны
TIMEZONE = pytz.timezone('Europe/Moscow')

# Конфигурация логирования
logging.basicConfig(
    format='▌ %(asctime)s │ %(name)-15s │ %(levelname)-8s │ %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('client_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ====================
# 📦 ИМПОРТ КОМПОНЕНТОВ
# ====================

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
from services.gsheets import append_to_sheet

# ====================
# 🗂 СОСТОЯНИЯ ДИАЛОГА
# ====================

(
    MAIN_MENU,      # Главное меню
    GET_LOCATION,   # Получение местоположения
    GET_PHONE       # Получение телефона
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
        """,
    
    'location_received':
        """
        ✅ <b>МЕСТОПОЛОЖЕНИЕ ПРИНЯТО</b>
        
        Теперь укажите ваш телефон:
        """,
    
    'success':
        """
        ✨ <b>ЗАЯВКА ПРИНЯТА!</b>
        
        Наш специалист свяжется с вами 
        в течение 24 часов.
        """
}

# ====================
# 🖥 ОСНОВНЫЕ ОБРАБОТЧИКИ
# ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /start - показывает главное меню"""
    menu_buttons = [
        ["📨 Отправить заявку"],
        ["❓ Частые вопросы", "📞 Контакты"],
        ["ℹ️ О компании"]
    ]
    
    await update.message.reply_text(
        text=TEXTS['welcome'],
        reply_markup=ReplyKeyboardMarkup(
            menu_buttons,
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        ),
        parse_mode='HTML'
    )
    return MAIN_MENU

async def start_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает процесс оформления новой заявки"""
    location_buttons = [
        [KeyboardButton("📍 Отправить геолокацию", request_location=True)],
        ["🏠 Указать адрес"],
        ["🔙 Назад"]
    ]
    
    await update.message.reply_text(
        text=TEXTS['request'],
        reply_markup=ReplyKeyboardMarkup(
            location_buttons,
            resize_keyboard=True
        ),
        parse_mode='HTML'
    )
    return GET_LOCATION

async def process_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает получение местоположения"""
    try:
        if update.message.location:
            # Геолокация
            loc = update.message.location
            context.user_data['location'] = {
                'type': 'geo',
                'lat': loc.latitude,
                'lon': loc.longitude
            }
            logger.info("Получена геолокация: %s,%s", loc.latitude, loc.longitude)
        else:
            # Текстовый адрес
            context.user_data['location'] = {
                'type': 'address',
                'text': update.message.text
            }
            logger.info("Получен адрес: %s", update.message.text)

        # Запрос телефона
        phone_buttons = [
            [KeyboardButton("📱 Отправить телефон", request_contact=True)],
            ["🔙 Назад"]
        ]
        
        await update.message.reply_text(
            text=TEXTS['location_received'],
            reply_markup=ReplyKeyboardMarkup(
                phone_buttons,
                resize_keyboard=True
            ),
            parse_mode='HTML'
        )
        return GET_PHONE

    except Exception as e:
        logger.error("Ошибка обработки местоположения: %s", e)
        await update.message.reply_text("⚠️ Ошибка обработки данных")
        return await start(update, context)

async def process_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает получение телефона"""
    try:
        # Получаем телефон
        phone = update.message.contact.phone_number if update.message.contact else update.message.text
        
        # Формируем адрес
        location = context.user_data['location']
        address = f"{location['lat']},{location['lon']}" if location['type'] == 'geo' else location['text']
        
        # Сохраняем в Google Sheets
        append_to_sheet(
            address=address,
            phone=phone
        )
        
        logger.info("Заявка сохранена: %s, %s", address, phone)
        
        # Подтверждение пользователю
        await update.message.reply_text(
            text=TEXTS['success'],
            reply_markup=ReplyKeyboardRemove(),
            parse_mode='HTML'
        )
        
        return await start(update, context)

    except Exception as e:
        logger.error("Ошибка сохранения заявки: %s", e)
        await update.message.reply_text(
            "⚠️ Произошла ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=ReplyKeyboardRemove()
        )
        return await start(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет текущее действие и возвращает в меню"""
    await update.message.reply_text(
        "Действие отменено",
        reply_markup=ReplyKeyboardRemove()
    )
    return await start(update, context)

# ====================
# 🚀 ЗАПУСК БОТА
# ====================

def run_client_bot(token: str) -> None:
    """Основная функция запуска клиентского бота"""
    try:
        logger.info("Инициализация клиентского бота...")
        
        # Создаем Application Builder
        application = Application.builder() \
            .token(token) \
            .build()
        
        # Настройка ConversationHandler
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", start),
                MessageHandler(filters.Regex("^📨 Отправить заявку$"), start_request)
            ],
            states={
                MAIN_MENU: [
                    MessageHandler(filters.Regex("^📨 Отправить заявку$"), start_request)
                ],
                GET_LOCATION: [
                    MessageHandler(filters.LOCATION, process_location),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, process_location),
                    MessageHandler(filters.Regex("^🔙 Назад$"), cancel)
                ],
                GET_PHONE: [
                    MessageHandler(filters.CONTACT, process_phone),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, process_phone),
                    MessageHandler(filters.Regex("^🔙 Назад$"), cancel)
                ]
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )
        
        # Регистрация обработчиков
        application.add_handler(conv_handler)
        
        # Запуск бота
        logger.info("Бот запущен в режиме polling...")
        application.run_polling()
        logger.info("Бот успешно остановлен")
        
    except Exception as e:
        logger.critical("Критическая ошибка: %s", e)
        raise