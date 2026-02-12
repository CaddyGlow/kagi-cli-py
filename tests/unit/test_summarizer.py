from __future__ import annotations


import httpx
import pytest
import respx

from kagi_client.auth import KagiAuth
from kagi_client.errors import APIError
from kagi_client.models import SummaryResult
from kagi_client.summarizer import SummarizerClient
from tests.conftest import make_jwt_token

SUMMARIZER_URL = "https://kagi.com/mother/summary_labs"

KAGI_STREAM_RESPONSE = (
    'update:{"output_text":"","output_data":{"status":"reading",'
    '"word_stats":{"n_tokens":0,"n_words":0,"n_pages":1,"time_saved":0,"length":null},'
    '"elapsed_seconds":null,"markdown":"",'
    '"response_metadata":{"speed":null,"tokens":0,"total_time_second":0,'
    '"model":"","version":"","cost":0},'
    '"images":[],"title":"","authors":null},"tokens":0,"type":"update"}\n'
    'update:{"output_text":"<p>Title: Test</p>",'
    '"output_data":{"status":"generating",'
    '"word_stats":{"n_tokens":100,"n_words":80,"n_pages":2,"time_saved":5,"length":null},'
    '"elapsed_seconds":null,"markdown":"",'
    '"response_metadata":{"speed":null,"tokens":0,"total_time_second":0,'
    '"model":"","version":"","cost":0},'
    '"images":[],"title":"","authors":null},"tokens":100,"type":"update"}\n'
    'final:{"output_text":"<p>Title: Test</p><ul><li>Point one</li></ul>",'
    '"output_data":{"status":"completed",'
    '"word_stats":{"n_tokens":100,"n_words":80,"n_pages":2,"time_saved":5,"length":null},'
    '"elapsed_seconds":12.1,'
    '"markdown":"Title: Test\\n\\n- Point one",'
    '"response_metadata":{"speed":77,"tokens":4154,"total_time_second":12.12,'
    '"model":"Mistral Small","version":"mistral-small-latest","cost":0.00048},'
    '"images":[],"title":"Test Article","authors":null},"tokens":3605,"type":"final"}\n'
)


def _make_auth() -> KagiAuth:
    auth = KagiAuth(kagi_session="fake")
    auth._token = make_jwt_token()
    return auth


class TestSummarizerClient:
    @respx.mock
    async def test_summarize_returns_result(self) -> None:
        respx.get(SUMMARIZER_URL).mock(
            return_value=httpx.Response(200, text=KAGI_STREAM_RESPONSE)
        )
        auth = _make_auth()
        client = SummarizerClient(auth=auth)
        result = await client.summarize("https://example.com/article")
        assert isinstance(result, SummaryResult)
        assert result.title == "Test Article"
        assert result.status == "completed"
        assert result.markdown == "Title: Test\n\n- Point one"
        assert result.response_metadata.model == "Mistral Small"
        assert result.response_metadata.speed == 77
        assert result.elapsed_seconds == 12.1

    @respx.mock
    async def test_summarize_with_summary_type(self) -> None:
        respx.get(SUMMARIZER_URL).mock(
            return_value=httpx.Response(200, text=KAGI_STREAM_RESPONSE)
        )
        auth = _make_auth()
        client = SummarizerClient(auth=auth)
        result = await client.summarize(
            "https://example.com/article", summary_type="summary"
        )
        assert isinstance(result, SummaryResult)

    @respx.mock
    async def test_summarize_raises_on_http_error(self) -> None:
        respx.get(SUMMARIZER_URL).mock(
            return_value=httpx.Response(403, text="Forbidden")
        )
        auth = _make_auth()
        client = SummarizerClient(auth=auth)
        with pytest.raises(APIError) as exc_info:
            await client.summarize("https://example.com")
        assert exc_info.value.status_code == 403

    @respx.mock
    async def test_summarize_stream(self) -> None:
        respx.get(SUMMARIZER_URL).mock(
            return_value=httpx.Response(200, text=KAGI_STREAM_RESPONSE)
        )
        auth = _make_auth()
        client = SummarizerClient(auth=auth)
        updates = []
        async for update in client.summarize_stream("https://example.com/article"):
            updates.append(update)
        # 2 updates + 1 final
        assert len(updates) == 3
        assert updates[-1].type == "final"
