from __future__ import annotations

import time

import jwt
import pytest


FAKE_KAGI_SESSION = "fakeSess_abc123.fakeSignature_xyz789"


def make_jwt_token(
    *,
    expired: bool = False,
    subscription: bool = True,
    user_id: str = "123456",
    account_type: str = "professional",
) -> str:
    now = int(time.time())
    if expired:
        iat = now - 7200
        exp = now - 3600
    else:
        iat = now
        exp = now + 6000
    payload = {
        "subscription": subscription,
        "id": user_id,
        "loggedIn": True,
        "theme": None,
        "mobileTheme": None,
        "customCssEnabled": True,
        "language": None,
        "customCssAvailable": False,
        "accountType": account_type,
        "iat": iat,
        "exp": exp,
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")


@pytest.fixture
def fake_session() -> str:
    return FAKE_KAGI_SESSION


@pytest.fixture
def valid_token() -> str:
    return make_jwt_token()


@pytest.fixture
def expired_token() -> str:
    return make_jwt_token(expired=True)
