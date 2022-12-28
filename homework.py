import os
import time
import requests
import telegram
import logging
from exeptions import *
from dotenv import load_dotenv
from telegram import Bot
from http import HTTPStatus

load_dotenv()
logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.DEBUG
)

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


def check_tokens() -> None:
    """Проверяет доступность переменных окружения."""
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }

    for key, value in tokens:
        if tokens[key] is None:
            logging.critical(
                f'Отсутствует обязательная переменная окружения: {key}\n'
                f'Программа принудительно остановлена.'
            )
            raise EnvironmentVariableError


def get_api_answer(timestamp: int) -> dict:
    """Делает запрос к эндпоинту API-сервиса."""
    response = requests.get(ENDPOINT, headers=HEADERS, params=timestamp)
    status = response.status_code

    if status != HTTPStatus.OK:
        raise AccessError(status)

    return response.json()


def check_response(response) -> dict:
    """Проверяет ответ API на соответствие документации."""
    if type(response) != dict:
        raise TypeError
    elif 'homeworks' and 'current_date' not in response:
        raise KeyError
    elif not response['homeworks']:
        logging.debug('Отсутствие в ответе новых статусов')

    return response['homeworks'][0]


def parse_status(homework: dict) -> str:
    """Извлекает из информации о конкретной домашней работе статус этой работы."""
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise StatusError
    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot: Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат."""
    bot.send_message(message, chat_id=TELEGRAM_CHAT_ID)


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)
        except AccessError as error:
            logging.error(f'Сбой в работе программы: Эндпоинт {ENDPOINT} '
                      f'недоступен. Код ответа API: {error.status}')
        except TypeError:
            logging.error(f'Ответ API не является словарем.')
        except KeyError:
            logging.error('Отсутствие ожидаемых ключей в ответе API')
        except StatusError:
            logging.error('Неожиданный статус домашней работы, обнаруженный в ответе API')


if __name__ == '__main__':
    main()
