from __future__ import annotations


class KagiError(Exception):
    pass


class AuthError(KagiError):
    pass


class TokenExpiredError(AuthError):
    pass


class StreamParseError(KagiError):
    pass


class APIError(KagiError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        body: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body
