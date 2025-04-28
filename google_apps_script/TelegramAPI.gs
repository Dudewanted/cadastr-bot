/**
 * Модуль для работы с Telegram Bot API
 */

function sendNotification(data) {
  const payload = {
    chat_id: CONFIG.CHAT_ID,
    text: _buildMessage(data),
    parse_mode: "Markdown",
    reply_markup: JSON.stringify(_buildKeyboard(data.phone))
  };
  
  _sendRequest('sendMessage', payload);
}

function sendCallbackResponse(callbackId, text) {
  _sendRequest('answerCallbackQuery', {
    callback_query_id: callbackId,
    text: text,
    show_alert: true
  });
}

// Внутренние функции
function _buildMessage(data) {
  return `📌 *Новая заявка #${data.id}*\n` +
         `├ Адрес: ${data.address}\n` +
         `├ Телефон: [${data.phone}](tel:${data.phone})\n` +
         `└ Дата: ${data.date}`;
}

function _buildKeyboard(phone) {
  return {
    inline_keyboard: [
      [
        { text: "☎️ Позвонить", callback_data: `call_${phone}` },
        { text: "✅ Позвонили", callback_data: `called_${phone}` }
      ],
      [
        { 
          text: "📋 Таблица", 
          url: `https://docs.google.com/spreadsheets/d/${CONFIG.SPREADSHEET_ID}/edit` 
        }
      ]
    ]
  };
}

function _sendRequest(method, payload) {
  const url = `https://api.telegram.org/bot${CONFIG.BOT_TOKEN}/${method}`;
  const options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload)
  };
  
  UrlFetchApp.fetch(url, options);
}