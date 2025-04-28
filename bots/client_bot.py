"""
Telegram бот для клиентов (версия python-telegram-bot v20.x)
Основной функционал:
- Прием заявок с геоданными
- Интерактивное меню
- Интеграция с Google Sheets
"""

import logging
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

# ==================== НАСТРОЙКА ЛОГИРОВАНИЯ ====================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename='client_bot.log'
)
logger = logging.getLogger(__name__)

# ==================== КОНСТАНТЫ И СОСТОЯНИЯ ====================
(
    MAIN_MENU,
    GET_LOCATION,
    GET_PHONE,
    FAQ_HANDLER
) = range(4)  # Состояния диалога

# Эмодзи для интерфейса
EMOJI = {
    'home': '🏠',
    'doc': '📄',
    'phone': '📱',
    'geo': '📍',
    'back': '🔙',
    'quest': '❓',
    'info': 'ℹ️'
}

# ==================== ТЕКСТОВЫЕ ШАБЛОНЫ ====================
TEXTS = {
    'welcome': (
        f"{EMOJI['home']} <b>Геодезические услуги</b>\n\n"
        "Выберите действие из меню ниже:"
    ),
    'request': (
        f"{EMOJI['doc']} <b>Новая заявка</b>\n\n"
        "Как вы хотите указать местоположение?"
    ),
    'location_received': (
        f"{EMOJI['geo']} <b>Местоположение получено</b>\n\n"
        "Теперь укажите ваш телефон:"
    ),
    'phone_received': (
        f"{EMOJI['phone']} <b>Заявка принята!</b>\n\n"
        "Наш специалист свяжется с вами в течение рабочего дня."
    ),
    'cancel': f"{EMOJI['back']} Действие отменено"
}

# ==================== ОСНОВНЫЕ ОБРАБОТЧИКИ ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик стартовой команды и главного меню"""
    menu_buttons = [
        [f"{EMOJI['doc']} Отправить заявку"],
        [f"{EMOJI['quest']} Вопросы", f"{EMOJI['info']} Контакты"],
        ["О компании"]
    ]
    
    await update.message.reply_text(
        text=TEXTS['welcome'],
        reply_markup=ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True),
        parse_mode='HTML'
    )
    return MAIN_MENU

async def handle_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик создания новой заявки"""
    location_buttons = [
        [KeyboardButton(f"{EMOJI['geo']} Отправить геолокацию", request_location=True)],
        ["Указать адрес вручную"],
        [f"{EMOJI['back']} Назад"]
    ]
    
    await update.message.reply_text(
        text=TEXTS['request'],
        reply_markup=ReplyKeyboardMarkup(location_buttons, resize_keyboard=True),
        parse_mode='HTML'
    )
    return GET_LOCATION

async def receive_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение местоположения (гео или адрес)"""
    if update.message.location:
        # Обработка геолокации
        loc = update.message.location
        context.user_data['location'] = f"lat:{loc.latitude}, lon:{loc.longitude}"
        logger.info(f"Получена геолокация: {loc.latitude}, {loc.longitude}")
    else:
        # Обработка текстового адреса
        context.user_data['location'] = update.message.text
        logger.info(f"Получен адрес: {update.message.text}")

    phone_buttons = [
        [KeyboardButton(f"{EMOJI['phone']} Отправить телефон", request_contact=True)],
        [f"{EMOJI['back']} Назад"]
    ]
    
    await update.message.reply_text(
        text=TEXTS['location_received'],
        reply_markup=ReplyKeyboardMarkup(phone_buttons, resize_keyboard=True),
        parse_mode='HTML'
    )
    return GET_PHONE

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение контактных данных"""
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text

    try:
        # Сохранение в Google Sheets
        append_to_sheet(
            address=context.user_data['location'],
            phone=phone
        )
        logger.info("Данные сохранены в Google Sheets")
        
        await update.message.reply_text(
            text=TEXTS['phone_received'],
            reply_markup=ReplyKeyboardRemove(),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        await update.message.reply_text(
            "⚠️ Ошибка при сохранении заявки. Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove()
        )
    
    return await start(update, context)  # Возврат в главное меню

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена текущего действия"""
    await update.message.reply_text(
        text=TEXTS['cancel'],
        reply_markup=ReplyKeyboardRemove()
    )
    return await start(update, context)

# ==================== ЗАПУСК БОТА ====================
def run_client_bot(token: str):
    """Инициализация и запуск бота"""
    try:
        logger.info("Инициализация клиентского бота...")
        
        # Создаем Application
        application = Application.builder().token(token).build()
        
        # Настройка ConversationHandler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                MAIN_MENU: [
                    MessageHandler(
                        filters.Regex(f"^{EMOJI['doc']} Отправить заявку$"),
                        handle_request
                    )
                ],
                GET_LOCATION: [
                    MessageHandler(filters.LOCATION, receive_location),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_location),
                    MessageHandler(
                        filters.Regex(f"^{EMOJI['back']} Назад$"),
                        cancel
                    )
                ],
                GET_PHONE: [
                    MessageHandler(filters.CONTACT, receive_phone),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone),
                    MessageHandler(
                        filters.Regex(f"^{EMOJI['back']} Назад$"),
                        cancel
                    )
                ]
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )
        
        # Регистрация обработчиков
        application.add_handler(conv_handler)
        
        # Запуск бота
        logger.info("Бот запущен в режиме polling...")
        application.run_polling()
        
    except Exception as e:
        logger.critical(f"Ошибка запуска бота: {e}")
        raise