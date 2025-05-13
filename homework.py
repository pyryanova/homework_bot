import os
import sys
import time
import logging
import requests
from dotenv import load_dotenv
from http import HTTPStatus
from telebot import TeleBot

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


def check_tokens():
    """Проверяет наличие всех обязательных переменных окружения."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    return all(tokens)


def send_message(bot, message):
    """Отправляет сообщение в Telegram и логирует результат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f'Бот отправил сообщение: {message}')
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения в Telegram: {error}')


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API."""
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        raise ConnectionError(f'Ошибка запроса к API: {error}')
    if response.status_code != HTTPStatus.OK:
        raise ValueError(
            f'Эндпоинт {ENDPOINT} недоступен. '
            f'Код ответа API: {response.status_code}'
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
#     user = bot.get_chat_member(TELEGRAM_CHAT_ID, TELEGRAM_CHAT_ID).user
#     user_name = user.first_name
#     welcome_text = (
#         f"Привет, {user_name}! Я жив и слежу за твоими домашками. "
#         "Я тоже волнуюсь. Просто тише.\nЕсли что изменится — сразу скажу. "
#         "Ну, почти сразу."
#     )
#     send_message(bot, welcome_text)


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical(
            'Отсутствует обязательная переменная окружения'
        )
        sys.exit(1)

    bot = TeleBot(token=TELEGRAM_TOKEN)
    # send_welcome_message(bot)  # отключено для прохождения тестов
    timestamp = int(time.time())
    last_message = ''
    last_status = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                if message != last_message:
                    send_message(bot, message)
                    last_message = message
                    last_status = homeworks[0].get('status', '')
                else:
                    logging.debug('Статус не изменился.')
            else:
                logging.debug('Нет новых статусов в ответе API.')

            timestamp = response.get('current_date', timestamp)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if message != last_message:
                send_message(bot, message)
                last_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        stream=sys.stdout
    )
    main()
