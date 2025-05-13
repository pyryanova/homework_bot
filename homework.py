import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telebot import TeleBot

from exceptions import ResponseCodeError

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler(
    __file__ + '.log',
    mode='a',
    encoding='utf-8'
)
formatter = logging.Formatter(
    '%(asctime)s,%(levelname)s,%(message)s,%(funcName)s,%(lineno)d'
)
handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(file_handler)


def check_tokens():
    """Проверяет наличие всех обязательных переменных окружения."""
    missing = [
        name for name, token in (
            ('PRACTICUM_TOKEN', PRACTICUM_TOKEN),
            ('TELEGRAM_TOKEN', TELEGRAM_TOKEN),
            ('TELEGRAM_CHAT_ID', TELEGRAM_CHAT_ID),
        ) if not token
    ]
    if missing:
        logger.critical(
            f'Отсутствуют переменные окружения: {", ".join(missing)}'
        )
        sys.exit(1)


def send_message(bot, message):
    """Отправляет сообщение в Telegram и логирует результат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug(f'Бот отправил сообщение: {message}')
        return True
    except Exception as error:
        logger.error(f'Ошибка при отправке сообщения в Telegram: {error}')
        return False


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API."""
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.exceptions.RequestException as error:
        raise ConnectionError(f'Ошибка запроса к API: {error}')
    if response.status_code != HTTPStatus.OK:
        raise ResponseCodeError(
            response.status_code,
            response.reason,
            response.text
        )
    return response.json()


def check_response(response):
    """Проверяет структуру ответа API на корректность."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API — не словарь')
    if 'homeworks' not in response:
        raise KeyError('Ключ "homeworks" отсутствует в ответе API')
    if not isinstance(response['homeworks'], list):
        raise TypeError('"homeworks" должен быть списком')
    return response['homeworks']


def parse_status(homework):
    """Извлекает имя и статус домашней работы."""
    if 'homework_name' not in homework:
        raise KeyError("В ответе отсутствует ключ 'homework_name'")
    if 'status' not in homework:
        raise KeyError("В ответе отсутствует ключ 'status'")

    homework_name = homework['homework_name']
    status = homework['status']

    if status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Недокументированный статус: {status}')
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


# def send_welcome_message(bot):
#     """Отправляет приветственное сообщение пользователю при старте бота."""
#     try:
#         user = bot.get_chat_member(TELEGRAM_CHAT_ID, TELEGRAM_CHAT_ID).user
#         user_name = user.first_name
#     except Exception as error:
#         logger.warning(f'Не удалось получить имя пользователя: {error}')
#         user_name = 'друг'
#     welcome_text = (
#         f"Привет, {user_name}! Я жив и слежу за твоими домашками. "
#         "Я тоже волнуюсь. Просто тише.\nЕсли что изменится — сразу скажу. "
#         "Ну, почти сразу."
#     )
#     send_message(bot, welcome_text)


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    # send_welcome_message(bot)  # для прохождения тестов
    timestamp = int(time.time())
    last_message = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                if message != last_message:
                    if send_message(bot, message):
                        last_message = message
                else:
                    logger.debug('Статус не изменился.')
            else:
                logger.debug('Нет новых статусов в ответе API.')
            timestamp = response.get('current_date', timestamp)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != last_message:
                if send_message(bot, message):
                    last_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
