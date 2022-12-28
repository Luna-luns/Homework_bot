class EnvironmentVariableError(Exception):
    def __str__(self) -> str:
        return 'Не получены все необходимые переменные окружения'


class AccessError(Exception):
    def __int__(self, status: int) -> None:
        self.status = status

    def __str__(self) -> str:
        return 'Эндпоинт не доступен'


class StatusError(Exception):
    def __str__(self) -> str:
        return 'Такого статуса не существует'
