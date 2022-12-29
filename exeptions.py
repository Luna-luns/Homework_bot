class EnvironmentVariableError(Exception):
    def __str__(self) -> str:
        return 'Не получены все необходимые переменные окружения'


class AccessError(Exception):
    def __str__(self) -> str:
        return 'Эндпоинт не доступен'


class MyRequestError(Exception):
    def __str__(self) -> str:
        return 'Ошибка во время выполнения запроса'


class StatusError(Exception):
    def __str__(self) -> str:
        return 'Такого статуса не существует'


class SendingError(Exception):
    def __str__(self) -> str:
        return 'Сбой при отправке сообщения'
