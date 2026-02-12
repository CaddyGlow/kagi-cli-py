from __future__ import annotations


import httpx
import pytest
import respx

from kagi_client.assistant import AssistantClient
from kagi_client.auth import KagiAuth
from kagi_client.errors import APIError
from kagi_client.models import AssistantResult
from tests.conftest import make_jwt_token

ASSISTANT_URL = "https://kagi.com/assistant/prompt"

KAGI_STREAM_RESPONSE = (
    'hi:{"v":"202509261613.stage.699a118","trace":"abc123"}\n'
    "thread_list.html:\n"
    '  <div class="hide-if-no-threads">content</div>\n'
    'thread.json:{"id":"thread-1","title":"Test","created_at":"2025-09-30T09:47:23Z",'
    '"expires_at":"2025-09-30T10:47:23Z","saved":false,"shared":false,'
    '"branch_id":"00000000-0000-4000-0000-000000000000","tag_ids":[]}\n'
    "messages.json:[]\n"
    'new_message.json:{"id":"msg-1","created_at":"2025-09-30T09:47:23Z",'
    '"state":"waiting","prompt":"Hello","reply":null,"md":null,'
    '"profile":{},"citations":null,"documents":[]}\n'
    'tokens.json:{"text":"","id":"msg-1"}\n'
    'tokens.json:{"text":"<p>Hi there!</p>","id":"msg-1"}\n'
    'tokens.json:{"text":"<p>Hi there!</p>","id":"msg-1"}\n'
    'new_message.json:{"id":"msg-1","created_at":"2025-09-30T09:47:23Z",'
    '"state":"done","prompt":"Hello","reply":"<p>Hi there!</p>",'
    '"md":"Hi there!","profile":{},"metadata":"","citations":[],"documents":[]}\n'
)


def _make_auth() -> KagiAuth:
    auth = KagiAuth(kagi_session="fake")
    auth._token = make_jwt_token()
    return auth


class TestAssistantClient:
    @respx.mock
    async def test_prompt_returns_result(self) -> None:
        respx.post(ASSISTANT_URL).mock(
            return_value=httpx.Response(200, text=KAGI_STREAM_RESPONSE)
        )
        auth = _make_auth()
        client = AssistantClient(auth=auth)
        result = await client.prompt("Hello")
        assert isinstance(result, AssistantResult)
        assert result.thread.id == "thread-1"
        assert result.thread.title == "Test"
        assert result.message.id == "msg-1"
        assert result.message.state == "done"
        assert result.message.reply == "<p>Hi there!</p>"
        assert result.message.md == "Hi there!"

    @respx.mock
    async def test_prompt_with_model(self) -> None:
        respx.post(ASSISTANT_URL).mock(
            return_value=httpx.Response(200, text=KAGI_STREAM_RESPONSE)
        )
        auth = _make_auth()
        client = AssistantClient(auth=auth)
        result = await client.prompt("Hello", model="claude-4-sonnet")
        assert isinstance(result, AssistantResult)

    @respx.mock
    async def test_prompt_raises_on_http_error(self) -> None:
        respx.post(ASSISTANT_URL).mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )
        auth = _make_auth()
        client = AssistantClient(auth=auth)
        with pytest.raises(APIError) as exc_info:
            await client.prompt("Hello")
        assert exc_info.value.status_code == 401

    @respx.mock
    async def test_prompt_stream(self) -> None:
        respx.post(ASSISTANT_URL).mock(
            return_value=httpx.Response(200, text=KAGI_STREAM_RESPONSE)
        )
        auth = _make_auth()
        client = AssistantClient(auth=auth)
        tokens = []
        async for token in client.prompt_stream("Hello"):
            tokens.append(token)
        # Should yield token text from tokens.json lines
        assert any(t == "<p>Hi there!</p>" for t in tokens)
