# 📍 Кадастровый Telegram-бот

Бот для автоматизации обработки заявок на геодезические работы, межевание и кадастровый учет. Интегрируется с Google Sheets и Telegram API.

## 🛠 Функционал

- **Клиентский бот**:
  - Прием заявок через Telegram
  - Сбор геолокации/адреса
  - Ответы на частые вопросы
- **Бот-уведомитель**:
  - Отправка оповещений о новых заявках
  - Кнопка быстрого звонка клиенту
  - Автоматическое обновление статусов
- **Google Sheets**:
  - Автосохранение заявок в таблицу
  - Синхронизация статусов

## 📦 Установка

1. Клонируйте репозиторий:

```bash
git clone https://github.com/yourusername/cadastr-bot.git
cd cadastr-bot
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```
## ⚙️ Настройка

1. Конфигурация
- Создайте файл `.env` по образцу `.env.example`

2. Google Sheets API
 - Создайте сервисный аккаунт в Google Cloud Console
 - Скачайте service_account.json в папку secure/
 - Дайте доступ к таблице для email из service_account.json
 
3. Telegram:
- Создайте ботов через `@BotFather`
- Для бота-уведомителя включите inline-режим

## 🚀 Запуск
Клиентский бот:
```bash
python -m client_bot.main
```

Бот-уведомитель:
```bash
python -m notifier_bot.main
```
## 🌐 Google Apps Script
1. Разверните скрипт из папки `google_apps_script/`
2. Настройте триггер `onEdit()` для таблицы
3. Включите веб-приложение с доступом: "Выполнять от моего имени"

## 🔒 Безопасность
Не публикуйте в репозитории:
- Файлы `.env`
- `service_account.json`
- `client_secret.json`
- Любые файлы с токенами
