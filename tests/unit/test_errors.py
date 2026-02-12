from __future__ import annotations

import pytest

from kagi_client.errors import (
    APIError,
    AuthError,
    KagiError,
    StreamParseError,
    TokenExpiredError,
)


class TestExceptionHierarchy:
    def test_kagi_error_is_base(self) -> None:
        assert issubclass(KagiError, Exception)

    def test_auth_error_inherits_kagi_error(self) -> None:
        assert issubclass(AuthError, KagiError)

    def test_token_expired_inherits_auth_error(self) -> None:
        assert issubclass(TokenExpiredError, AuthError)

    def test_stream_parse_error_inherits_kagi_error(self) -> None:
        assert issubclass(StreamParseError, KagiError)

    def test_api_error_inherits_kagi_error(self) -> None:
        assert issubclass(APIError, KagiError)


class TestKagiError:
    def test_message(self) -> None:
        err = KagiError("something went wrong")
        assert str(err) == "something went wrong"

    def test_catchable_as_exception(self) -> None:
        with pytest.raises(Exception):
            raise KagiError("fail")


class TestAPIError:
    def test_stores_status_and_body(self) -> None:
        err = APIError("bad request", status_code=400, body="invalid json")
        assert err.status_code == 400
        assert err.body == "invalid json"
        assert "bad request" in str(err)

    def test_default_body_is_none(self) -> None:
        err = APIError("server error", status_code=500)
        assert err.status_code == 500
        assert err.body is None


class TestTokenExpiredError:
    def test_message(self) -> None:
        err = TokenExpiredError("token expired")
        assert str(err) == "token expired"

    def test_catchable_as_auth_error(self) -> None:
        with pytest.raises(AuthError):
            raise TokenExpiredError("expired")


class TestStreamParseError:
    def test_message(self) -> None:
        err = StreamParseError("malformed SSE")
        assert str(err) == "malformed SSE"
