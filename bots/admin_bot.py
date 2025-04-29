"""
🛠 АДМИНИСТРАТИВНЫЙ БОТ ДЛЯ УПРАВЛЕНИЯ ЗАЯВКАМИ

▌ Основной функционал:
├── 📋 Уведомление о новых заявках (через Telegram Notifier в Google Apps Script)
├── ✏️ Изменение статуса заявки ("В работе", "Завершена")
├── 📞 Быстрый вызов клиента (инлайн-кнопка)
"""

import logging
import sys
import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CallbackQueryHandler, ContextTypes, CommandHandler
from services.gsheets import update_status
from config import TELEGRAM_ADMIN_TOKEN, ADMIN_CHAT_ID

logging.basicConfig(
    format="🛠 [%(asctime)s] %(name)s │ %(levelname)-8s │ %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("admin_bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# 🔔 Уведомление о новой заявке (вызывается Google Apps Script через Webhook)
async def notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = update.message.text  # Формат: ID;Адрес;Телефон;Дата;Статус
        if ";" not in data:
            await update.message.reply_text("⚠️ Получены некорректные данные.")
            return

        id_, address, phone, date, status = data.split(";")
        phone_url = "tel:" + phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 Позвонить", url=phone_url)],
            [
                InlineKeyboardButton("🟡 В работе", callback_data=f"status|{id_}|В работе"),
                InlineKeyboardButton("✅ Завершена", callback_data=f"status|{id_}|Завершена"),
            ]
        ])

        msg = (
            f"📬 <b>Новая заявка</b>\n\n"            f"<b>📍 Адрес:</b> {address}\n"            f"<b>📞 Телефон:</b> {phone}\n"            f"<b>🕒 Дата:</b> {date}\n"            f"<b>📌 Статус:</b> {status}"
        )

        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=msg,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.exception("Ошибка при обработке уведомления: %s", e)
        logger.exception("Ошибка при обработке уведомления")

# 🔄 Обработка callback кнопок (смена статуса)
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        if query.data.startswith("status|"):
            _, row_id, new_status = query.data.split("|")

            update_status(row_id, new_status)

            await query.edit_message_text(
                text=f"📝 Статус заявки №{row_id} обновлён на: {new_status}"
            )

    except Exception as e:
        logger.exception("Ошибка при смене статуса")
        await query.edit_message_text("❌ Не удалось обновить статус.")

# 🔄 Ручной тест уведомления (опционально)
async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fake = "42;г. Пример, ул. Ленина 10;+7-900-123-45-67;2025-04-29 15:42;Новая"
    update.message.text = fake
    await notify(update, context)

# 🚀 Запуск бота
async def run_admin_bot():
    app = Application.builder().token(TELEGRAM_ADMIN_TOKEN).build()

    app.add_handler(CommandHandler("test", test))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), notify))
    app.add_handler(CallbackQueryHandler(handle_callback))

    await app.run_polling()
async def show_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        rows = sheet.get_all_values()[1:]  # Пропускаем заголовки
        if not rows:
            await update.message.reply_text("❗️Заявок пока нет.")
            return

        # Группировка по статусу
        new = [row for row in rows if row[4] == "Новая"]
        working = [row for row in rows if row[4] == "В работе"]
        done = [row for row in rows if row[4] == "Завершена"]

        def format_entries(entries):
            if not entries:
                return "—"
            return "\n".join([f"#{row[0]} 📍 {row[1]} 📞 {row[2]} 🕒 {row[3]}" for row in entries])

        msg = (
            "<b>📋 Панель управления заявками</b>\n\n"
            f"<b>🆕 Новые:</b>\n{format_entries(new)}\n\n"
            f"<b>🛠 В работе:</b>\n{format_entries(working)}\n\n"
            f"<b>✅ Завершены:</b>\n{format_entries(done)}"
        )

        await update.message.reply_text(msg, parse_mode="HTML")
    except Exception as e:
        logger.exception("Ошибка в панели: %s", e)
        await update.message.reply_text("❌ Не удалось загрузить панель.")