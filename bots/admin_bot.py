"""
Административный бот (версия python-telegram-bot v20.x)
Функционал:
- Уведомления о новых заявках
- Управление статусами
- Быстрый доступ к контактам
"""

import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from services.gsheets import get_worksheet

# ==================== НАСТРОЙКА ====================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename='admin_bot.log'
)
logger = logging.getLogger(__name__)

# Эмодзи для интерфейса
EMOJI = {
    'new': '🆕',
    'call': '📞',
    'work': '🔄',
    'done': '✅',
    'back': '🔙'
}

# ==================== ОБРАБОТЧИКИ ====================
async def check_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка новых заявок"""
    try:
        worksheet = get_worksheet()
        records = worksheet.get_all_records()
        new_requests = [r for r in records if r['Статус'] == 'Новая']
        
        if not new_requests:
            await update.message.reply_text("📭 Нет новых заявок")
            return
        
        for req in new_requests:
            buttons = [
                [f"{EMOJI['call']} Позвонить {req['Телефон']}"],
                [f"{EMOJI['work']} В работе #{req['ID']}"],
                [f"{EMOJI['done']} Завершено #{req['ID']}"]
            ]
            
            text = (
                f"{EMOJI['new']} <b>Новая заявка #{req['ID']}</b>\n\n"
                f"📍 <b>Адрес:</b> {req['Адрес']}\n"
                f"📞 <b>Телефон:</b> {req['Телефон']}\n"
                f"📅 <b>Дата:</b> {req['Дата']}"
            )
            
            await update.message.reply_text(
                text=text,
                reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True),
                parse_mode='HTML'
            )
            
    except Exception as e:
        logger.error(f"Ошибка проверки заявок: {e}")
        await update.message.reply_text("⚠️ Ошибка загрузки заявок")

async def update_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обновление статуса заявки"""
    try:
        text = update.message.text
        req_id = text.split('#')[1]
        new_status = 'В работе' if EMOJI['work'] in text else 'Завершено'
        
        worksheet = get_worksheet()
        cell = worksheet.find(req_id)
        worksheet.update_cell(cell.row, 5, new_status)
        
        await update.message.reply_text(
            f"✅ Статус заявки #{req_id} изменен на '{new_status}'"
        )
        
    except Exception as e:
        logger.error(f"Ошибка обновления статуса: {e}")
        await update.message.reply_text("⚠️ Ошибка обновления статуса")

# ==================== ЗАПУСК БОТА ====================
def run_admin_bot(token: str):
    """Запуск административного бота"""
    try:
        logger.info("Инициализация админского бота...")
        
        application = Application.builder().token(token).build()
        
        # Регистрация обработчиков
        application.add_handler(CommandHandler("start", check_requests))
        application.add_handler(
            MessageHandler(filters.Regex(f"^{EMOJI['call']}"), 
                         lambda u, c: u.message.reply_text(f"Наберите: {u.message.text.split()[-1]}"))
        )
        application.add_handler(
            MessageHandler(filters.Regex(f"^({EMOJI['work']}|{EMOJI['done']})"), 
                         update_status)
        )
        
        logger.info("Админский бот запущен")
        application.run_polling()
        
    except Exception as e:
        logger.critical(f"Ошибка запуска админского бота: {e}")
        raise