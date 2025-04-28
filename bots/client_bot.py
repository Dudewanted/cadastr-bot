"""
📋 КЛИЕНТСКИЙ БОТ ДЛЯ ГЕОДЕЗИЧЕСКИХ УСЛУГ (v2.1)

Основные функции:
✅ Прием заявок с геолокацией/адресом
✅ Сбор контактных данных
✅ Интеграция с Google Sheets
✅ Красивый интерфейс с emoji
"""

import logging
import pytz
from datetime import datetime
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

# 〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️
# ⚙️ Н А С Т Р О Й К И
# 〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️

# 🕒 Настройка временной зоны
TIMEZONE = pytz.timezone('Europe/Moscow')

# 📊 Уровни логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='client_bot.log'
)
logger = logging.getLogger(__name__)

# 📌 Состояния диалога
(
    MAIN_MENU,
    GET_LOCATION,
    GET_PHONE
) = range(3)

# 🔠 Текстовые шаблоны с emoji
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

# 〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️
# 🖥 О С Н О В Н О Й   И Н Т Е Р Ф Е Й С
# 〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    🏠 Главное меню
    Показывает основные кнопки интерфейса
    """
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

# 〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️
# 📝 О Б Р А Б О Т Ч И К И   З А Я В О К
# 〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️

async def start_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    📨 Начало оформления заявки
    Предлагает выбрать способ указания местоположения
    """
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

async def process_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    📍 Обработка местоположения
    Сохраняет геолокацию или адрес и запрашивает телефон
    """
    if update.message.location:
        # 🌐 Обработка геолокации
        loc = update.message.location
        context.user_data['location'] = {
            'type': 'geo',
            'lat': loc.latitude,
            'lon': loc.longitude
        }
        logger.info(f"Получена геолокация: {loc.latitude},{loc.longitude}")
    else:
        # 🏠 Обработка адреса
        context.user_data['location'] = {
            'type': 'address',
            'text': update.message.text
        }
        logger.info(f"Получен адрес: {update.message.text}")

    # 📱 Запрос телефона
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

async def process_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    📞 Обработка телефона
    Сохраняет заявку и завершает процесс
    """
    # Получаем телефон
    phone = update.message.contact.phone_number if update.message.contact else update.message.text
    
    try:
        # 📊 Сохранение в Google Sheets
        location = context.user_data['location']
        address = (
            f"{location['lat']},{location['lon']}" 
            if location['type'] == 'geo' 
            else location['text']
        )
        
        append_to_sheet(
            address=address,
            phone=phone
        )
        
        logger.info("✅ Заявка сохранена")
        
        # 🎉 Подтверждение пользователю
        await update.message.reply_text(
            text=TEXTS['success'],
            reply_markup=ReplyKeyboardRemove(),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения: {e}")
        await update.message.reply_text(
            "⚠️ Произошла ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=ReplyKeyboardRemove()
        )
    
    return await show_main_menu(update, context)

# 〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️
# 🚀 З А П У С К   Б О Т А
# 〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️

def run_client_bot(token: str):
    """
    🔌 Основная функция запуска бота
    Настраивает и запускает Telegram-бота
    """
    try:
        logger.info("🔄 Инициализация бота...")
        
        # Создаем Application
        app = Application.builder() \
            .token(token) \
            .post_init(_setup_timezone) \
            .build()
        
        # Настраиваем обработчики
        _setup_handlers(app)
        
        logger.info("🤖 Бот запущен и готов к работе!")
        app.run_polling()
        
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка: {e}")
        raise

async def _setup_timezone(app: Application):
    """⏰ Установка временной зоны"""
    app.job_queue.scheduler.configure(timezone=TIMEZONE)
    logger.info(f"⏱ Установлена временная зона: {TIMEZONE}")

def _setup_handlers(app: Application):
    """🛠 Настройка обработчиков команд"""
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", show_main_menu),
            MessageHandler(filters.Regex("^📨 Отправить заявку$"), start_request)
        ],
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
        fallbacks=[
            MessageHandler(filters.Regex("^🔙 Назад$"), show_main_menu)
        ],
    )
    
    app.add_handler(conv_handler)