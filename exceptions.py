class ResponseCodeError(Exception):
    """Исключение для ошибок ответа от API с некорректным статус-кодом."""

    def __init__(self, status_code, reason=None, text=None):
        self.status_code = status_code
        self.reason = reason
        self.text = text
        message = (
            f'Эндпоинт недоступен. Код ответа: {status_code}. '
            f'Причина: {reason}. Ответ: {text}'
        )
        super().__init__(message)
