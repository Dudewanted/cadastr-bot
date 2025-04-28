"""
Telegram бот для администратора кадастровых услуг.
Основные функции:
- Уведомления о новых заявках
- Быстрый набор телефона клиента
- Изменение статуса заявки
"""

import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from services.gsheets import get_worksheet

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="admin_bot.log"
)
logger = logging.getLogger(__name__)

# =============================================
# ТЕКСТОВЫЕ ШАБЛОНЫ
# =============================================

TEXTS = {
    "new_request": "🚨 <b>Новая заявка #{id}</b>\n\n"
                   "📍 <b>Адрес:</b> {address}\n"
                   "📞 <b>Телефон:</b> {phone}\n"
                   "📅 <b>Дата:</b> {date}\n\n"
                   "Выберите действие:",
    "no_requests": "📭 Новых заявок нет.",
    "call": "Наберите номер: {phone}",
    "status_changed": "✅ Статус заявки #{id} изменен на '{status}'"
}

# =============================================
# ОСНОВНЫЕ ФУНКЦИИ БОТА
# =============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start - проверяет новые заявки"""
    try:
        worksheet = get_worksheet()
        records = worksheet.get_all_records()
        new_requests = [r for r in records if r["Статус"] == "Новая"]
        
        if not new_requests:
            await update.message.reply_html(TEXTS["no_requests"])
            return
        
        for request in new_requests:
            message = TEXTS["new_request"].format(
                id=request["ID"],
                address=request["Адрес"],
                phone=request["Телефон"],
                date=request["Дата"]
            )
            
            buttons = [
                [f"📞 Позвонить {request['Телефон']}"],
                [f"🔄 В работе #{request['ID']}"],
                [f"✅ Завершено #{request['ID']}"]
            ]
            reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
            
            await update.message.reply_html(
                text=message,
                reply_markup=reply_markup
            )
            
    except Exception as e:
        logger.error(f"Ошибка при проверке заявок: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при загрузке заявок")

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки звонка"""
    phone = update.message.text.replace("📞 Позвонить ", "")
    await update.message.reply_text(
        TEXTS["call"].format(phone=phone)
    )

async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик изменения статуса заявки"""
    try:
        text = update.message.text
        request_id = text.split("#")[1]
        status = "В работе" if "🔄" in text else "Завершено"
        
        worksheet = get_worksheet()
        cell = worksheet.find(request_id)
        worksheet.update_cell(cell.row, 5, status)
        
        await update.message.reply_html(
            TEXTS["status_changed"].format(id=request_id, status=status)
        )
        
    except Exception as e:
        logger.error(f"Ошибка при изменении статуса: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при изменении статуса")

# =============================================
# ЗАПУСК БОТА
# =============================================

def run_admin_bot(token: str):
    """Запуск админского бота"""
    try:
        logger.info("Запуск админского бота...")
        
        application = ApplicationBuilder().token(token).build()
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.Regex("^📞 Позвонить"), handle_call))
        application.add_handler(MessageHandler(filters.Regex("^(🔄|✅)"), handle_status))
        
        # Запускаем бота
        application.run_polling()
        logger.info("Админский бот успешно запущен")
        
    except Exception as e:
        logger.critical(f"Ошибка при запуске админского бота: {e}")
        raise