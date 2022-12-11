from http import HTTPStatus


class ApiException(Exception):
    def __init__(
        self,
        request,
        message: str,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        previous: Exception = None
    ):
        super().__init__(message)

        self._request = request
        self._status_code = status_code
        self._message = message
        self._previous = previous

    @property
    def request(self):
        return self._request

    @property
    def status_code(self) -> int:
        return self._status_code

    @property
    def message(self) -> str:
        return self._message

    @property
    def previous(self) -> Exception:
        return self._previous

    @property
    def payload(self) -> dict:
        result = {
            'message': self.message,
            'code': self.status_code
        }

        return result
