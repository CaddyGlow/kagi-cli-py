from __future__ import annotations

import time

import httpx
import pytest
import respx

from kagi_client.auth import KagiAuth
from kagi_client.errors import AuthError
from kagi_client.models import TokenPayload
from tests.conftest import make_jwt_token


class TestDecodeToken:
    def test_decodes_valid_token(self, valid_token: str) -> None:
        auth = KagiAuth(kagi_session="fake")
        payload = auth.decode_token(valid_token)
        assert isinstance(payload, TokenPayload)
        assert payload.id == "123456"
        assert payload.subscription is True
        assert payload.account_type == "professional"
        assert payload.logged_in is True

    def test_decodes_expired_token(self, expired_token: str) -> None:
        auth = KagiAuth(kagi_session="fake")
        payload = auth.decode_token(expired_token)
        assert payload.exp < int(time.time())


class TestIsTokenExpired:
    def test_valid_token_not_expired(self, valid_token: str) -> None:
        auth = KagiAuth(kagi_session="fake")
        assert auth.is_token_expired(valid_token) is False

    def test_expired_token_is_expired(self, expired_token: str) -> None:
        auth = KagiAuth(kagi_session="fake")
        assert auth.is_token_expired(expired_token) is True


class TestRefreshToken:
    @respx.mock
    async def test_refresh_returns_new_token(self, fake_session: str) -> None:
        new_token = make_jwt_token(user_id="999")
        respx.get("https://translate.kagi.com/api/auth").mock(
            return_value=httpx.Response(
                200,
                json={
                    "token": new_token,
                    "id": "999",
                    "loggedIn": True,
                    "subscription": True,
                    "expiresAt": "2025-09-29T14:52:13.000Z",
                    "accountType": "professional",
                },
            )
        )
        auth = KagiAuth(kagi_session=fake_session)
        token = await auth.refresh_token()
        assert token == new_token

    @respx.mock
    async def test_refresh_raises_on_http_error(self, fake_session: str) -> None:
        respx.get("https://translate.kagi.com/api/auth").mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )
        auth = KagiAuth(kagi_session=fake_session)
        with pytest.raises(AuthError):
            await auth.refresh_token()


class TestGetValidToken:
    @respx.mock
    async def test_returns_cached_if_valid(self, fake_session: str) -> None:
        token = make_jwt_token()
        auth = KagiAuth(kagi_session=fake_session)
        auth._token = token
        result = await auth.get_valid_token()
        assert result == token

    @respx.mock
    async def test_refreshes_if_expired(self, fake_session: str) -> None:
        new_token = make_jwt_token(user_id="777")
        respx.get("https://translate.kagi.com/api/auth").mock(
            return_value=httpx.Response(
                200,
                json={
                    "token": new_token,
                    "id": "777",
                    "loggedIn": True,
                    "subscription": True,
                    "expiresAt": "2025-09-29T14:52:13.000Z",
                    "accountType": "professional",
                },
            )
        )
        auth = KagiAuth(kagi_session=fake_session)
        auth._token = make_jwt_token(expired=True)
        result = await auth.get_valid_token()
        assert result == new_token

    @respx.mock
    async def test_refreshes_if_no_token(self, fake_session: str) -> None:
        new_token = make_jwt_token()
        respx.get("https://translate.kagi.com/api/auth").mock(
            return_value=httpx.Response(
                200,
                json={
                    "token": new_token,
                    "id": "123",
                    "loggedIn": True,
                    "subscription": True,
                    "expiresAt": "2025-09-29T14:52:13.000Z",
                    "accountType": "professional",
                },
            )
        )
        auth = KagiAuth(kagi_session=fake_session)
        result = await auth.get_valid_token()
        assert result == new_token
