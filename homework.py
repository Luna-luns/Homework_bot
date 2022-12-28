import os
import time
import requests
import telegram
import logging
from exeptions import EnvironmentVariableError, \
    AccessError, MyRequestError, StatusError, SendingError
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

    for key in tokens:
        if tokens[key] is None:
            logging.critical(
                f'Отсутствует обязательная переменная окружения: {key}\n'
                f'Программа принудительно остановлена.'
            )
            raise EnvironmentVariableError


def get_api_answer(timestamp: int) -> dict:
    """Делает запрос к эндпоинту API-сервиса."""
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=timestamp)
        status = response.status_code

        if status != HTTPStatus.OK:
            raise AccessError(status)
        return response.json()
    except requests.RequestException as error:
        logging.error(f'Сбой в работе программы: '
                      f'Эндпоинт {ENDPOINT} недоступен.')
        raise MyRequestError from error


def check_response(response) -> list:
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является словарем.')
    elif 'homeworks' not in response or 'current_date' not in response:
        raise KeyError
    elif not isinstance(response['homeworks'], list):
        raise TypeError('Ответ API не является списком.')

    return response['homeworks']


def parse_status(homework: dict) -> str:
    """Извлекает статус из информации о конкретной домашней работе."""
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise StatusError
    elif 'homework_name' not in homework:
        raise KeyError
    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot: Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(message, TELEGRAM_CHAT_ID)
        logging.debug('Сообщение об изменении статуса отправленно в Telegram')
    except telegram.error.TelegramError as error:
        logging.error('Сбой при отправке сообщения в Telegram')
        raise SendingError from error


def main() -> None:
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            if homework:
                message = parse_status(homework[0])
                send_message(bot, message)
            else:
                logging.debug('Отсутствие в ответе новых статусов')
        except AccessError as error:
            logging.error(f'Сбой в работе программы: Эндпоинт {ENDPOINT} \
            недоступен. Код ответа API: {error.status}')
        except TypeError as error:
            logging.error(error.message)
        except KeyError:
            logging.error('Отсутствие ожидаемых ключей в ответе API')
        except StatusError:
            logging.error('Неожиданный статус домашней работы, '
                          'обнаруженный в ответе API')

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
