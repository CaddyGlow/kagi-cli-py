from __future__ import annotations

import time

import httpx
import jwt

from kagi_client.errors import AuthError
from kagi_client.models import TokenPayload

AUTH_URL = "https://translate.kagi.com/api/auth"


class KagiAuth:
    def __init__(self, kagi_session: str) -> None:
        self.kagi_session = kagi_session
        self._token: str | None = None

    def decode_token(self, token: str) -> TokenPayload:
        payload = jwt.decode(
            token,
            algorithms=["HS256"],
            options={"verify_signature": False},
        )
        return TokenPayload(
            subscription=payload["subscription"],
            id=payload["id"],
            logged_in=payload["loggedIn"],
            account_type=payload["accountType"],
            iat=payload["iat"],
            exp=payload["exp"],
        )

    def is_token_expired(self, token: str) -> bool:
        payload = self.decode_token(token)
        return payload.exp <= int(time.time())

    async def refresh_token(self) -> str:
        timeout = httpx.Timeout(10.0, read=300.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(
                AUTH_URL,
                cookies={"kagi_session": self.kagi_session},
            )
        if resp.status_code != 200:
            raise AuthError(
                f"Auth refresh failed with status {resp.status_code}: {resp.text}"
            )
        data = resp.json()
        self._token = data["token"]
        return self._token

    async def get_valid_token(self) -> str:
        if self._token is not None and not self.is_token_expired(self._token):
            return self._token
        return await self.refresh_token()
