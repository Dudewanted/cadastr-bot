function onEdit(e) {
  const sheet = e.source.getActiveSheet();
  const range = e.range;
  
  // Проверяем, что редактирование было в нужном листе и столбце
  if (sheet.getName() === "Кадастровые заявки" && range.getColumn() === 5) {
    const row = range.getRow();
    const status = range.getValue();
    const requestData = sheet.getRange(row, 1, 1, 4).getValues()[0];
    
    // Отправляем уведомление
    sendTelegramNotification(requestData, status);
  }
}

function sendTelegramNotification(requestData, status) {
  const botToken = PropertiesService.getScriptProperties().getProperty('TELEGRAM_BOT_TOKEN');
  const chatId = PropertiesService.getScriptProperties().getProperty('ADMIN_CHAT_ID');
  
  const [id, address, phone, date] = requestData;
  
  const message = `🔄 Статус заявки изменен:\n\n` +
                 `📌 ID: ${id}\n` +
                 `📍 Адрес: ${address}\n` +
                 `📞 Телефон: ${phone}\n` +
                 `📅 Дата: ${date}\n` +
                 `🆕 Новый статус: <b>${status}</b>`;
  
  const payload = {
    method: "sendMessage",
    chat_id: chatId,
    text: message,
    parse_mode: "HTML"
  };
  
  const options = {
    method: "post",
    payload: payload
  };
  
  try {
    UrlFetchApp.fetch(`https://api.telegram.org/bot${botToken}/`, options);
  } catch (e) {
    console.error("Error sending Telegram notification:", e);
  }
}

function setWebhook() {
  const botToken = PropertiesService.getScriptProperties().getProperty('TELEGRAM_BOT_TOKEN');
  const webAppUrl = PropertiesService.getScriptProperties().getProperty('WEB_APP_URL');
  
  const payload = {
    method: "setWebhook",
    url: webAppUrl
  };
  
  const options = {
    method: "post",
    payload: payload
  };
  
  UrlFetchApp.fetch(`https://api.telegram.org/bot${botToken}/`, options);
}