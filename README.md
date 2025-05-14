# Homework Status Bot

## Описание

Это Telegram-бот, который отслеживает статус проверки домашних заданий 
на платформе Яндекс.Практикум.  
Бот отправляет уведомление в Telegram, когда статус работы изменяется.

## Используемые технологии

- Python 3.10+
- requests
- python-dotenv
- pyTelegramBotAPI (TeleBot)
- logging

## Установка и запуск

### 1. Клонируйте репозиторий

```
git clone https://github.com/yourusername/homework-bot.git
cd homework-bot
```

### 2. Создайте виртуальное окружение и активируйте его

```
python3 -m venv venv
source venv/bin/activate
```

### 3. Установите зависимости

```
pip install -r requirements.txt
```

### 4. Создайте файл `.env` и добавьте в него переменные

```
PRACTICUM_TOKEN=<ваш_токен_практикума>
TELEGRAM_TOKEN=<токен_вашего_бота>
TELEGRAM_CHAT_ID=<ваш_telegram_chat_id>
```

### 5. Запустите бота

```
python homework.py
```

## Тестирование

Для запуска тестов используйте:

```
pytest
```

## Структура проекта

- `homework.py` — основной файл с логикой бота
- `exceptions.py` — пользовательские исключения
- `requirements.txt` — список зависимостей
- `tests/` — модульные тесты на pytest
- `.env` — файл с переменными окружения (не добавляется в git)

## Лицензия

Проект разработан в учебных целях в рамках курса 
"Python-разработчик расширенный" от Яндекс.Практикума.
