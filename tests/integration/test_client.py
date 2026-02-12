from __future__ import annotations


import httpx
import respx

from kagi_client.client import KagiClient
from kagi_client.models import (
    AssistantResult,
    ProofreadResult,
    SearchResult,
    SummaryResult,
)
from tests.conftest import FAKE_KAGI_SESSION, make_jwt_token

AUTH_URL = "https://translate.kagi.com/api/auth"
PROOFREAD_URL = "https://translate.kagi.com/api/proofread"
SUMMARIZER_URL = "https://kagi.com/mother/summary_labs"
ASSISTANT_URL = "https://kagi.com/assistant/prompt"
SEARCH_URL = "https://kagi.com/socket/search"


def _mock_auth() -> str:
    token = make_jwt_token()
    respx.get(AUTH_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "token": token,
                "id": "123",
                "loggedIn": True,
                "subscription": True,
                "expiresAt": "2025-09-29T14:52:13.000Z",
                "accountType": "professional",
            },
        )
    )
    return token


PROOFREAD_SSE = (
    "event: message\n"
    'data: {"detected_language":{"iso":"en","label":"English"}}\n\n'
    'event: message\ndata: {"delta":"test"}\n\n'
    'event: message\ndata: {"text_done":true}\n\n'
    "event: message\n"
    'data: {"analysis":{"corrected_text":"test","changes":[],'
    '"corrections_summary":"OK",'
    '"tone_analysis":{"overall_tone":"neutral","description":"Neutral"},'
    '"voice_consistency":{"active_voice_percentage":0,"passive_voice_percentage":0,'
    '"is_consistent":true,"passive_instances":[],"summary":"N/A"},'
    '"repetition_detection":{"repeated_words":[],"repeated_phrases":[],"summary":"N/A"},'
    '"writing_statistics":{"word_count":1,"character_count":4,"character_count_no_spaces":4,'
    '"paragraph_count":1,"sentence_count":1,"average_words_per_sentence":1.0,'
    '"average_characters_per_word":4.0,"sentence_length_distribution":{"short":1,"medium":0,"long":0},'
    '"vocabulary_diversity":1.0,"reading_time_minutes":0.1,"complex_sentences":0,'
    '"simple_sentences":1,"reading_level":"elementary","readability_score":20.0},'
    '"explanation_language":"en"}}\n\n'
    'event: message\ndata: {"done":true}\n\n'
)

SUMMARIZER_STREAM = (
    'final:{"output_text":"<p>Summary</p>","output_data":{"status":"completed",'
    '"word_stats":{"n_tokens":50,"n_words":40,"n_pages":1,"time_saved":2,"length":null},'
    '"elapsed_seconds":5.0,"markdown":"Summary",'
    '"response_metadata":{"speed":50,"tokens":100,"total_time_second":5.0,'
    '"model":"Test","version":"v1","cost":0.001},'
    '"images":[],"title":"Test","authors":null},"tokens":100,"type":"final"}\n'
)

ASSISTANT_STREAM = (
    'hi:{"v":"v1"}\n'
    'thread.json:{"id":"t1","title":"Test","created_at":"2025-01-01T00:00:00Z",'
    '"expires_at":"2025-01-01T01:00:00Z","saved":false,"shared":false,'
    '"branch_id":"00000000","tag_ids":[]}\n'
    'new_message.json:{"id":"m1","created_at":"2025-01-01T00:00:00Z",'
    '"state":"done","prompt":"Hi","reply":"<p>Hello</p>","md":"Hello",'
    '"profile":{},"citations":[],"documents":[]}\n'
)

SEARCH_SSE = (
    "id: 1\n"
    'data: [{"tag":"search.info","payload":{"share_url":"https://kagi.com/search?q=test",'
    '"curr_batch":1,"curr_piece":1,"next_batch":-1,"next_piece":1},'
    '"sent_at":1,"kagi_version":"v1"}]\n\n'
    "id: 2\n"
    'data: [{"tag":"search","payload":{"content":"<div>Result</div>"},'
    '"sent_at":1,"kagi_version":"v1"}]\n\n'
)


class TestKagiClient:
    @respx.mock
    async def test_context_manager(self) -> None:
        _mock_auth()
        async with KagiClient(kagi_session=FAKE_KAGI_SESSION) as client:
            assert client is not None

    @respx.mock
    async def test_proofread(self) -> None:
        _mock_auth()
        respx.post(PROOFREAD_URL).mock(
            return_value=httpx.Response(200, text=PROOFREAD_SSE)
        )
        async with KagiClient(kagi_session=FAKE_KAGI_SESSION) as client:
            result = await client.proofread("test")
        assert isinstance(result, ProofreadResult)
        assert result.text == "test"

    @respx.mock
    async def test_summarize(self) -> None:
        _mock_auth()
        respx.get(SUMMARIZER_URL).mock(
            return_value=httpx.Response(200, text=SUMMARIZER_STREAM)
        )
        async with KagiClient(kagi_session=FAKE_KAGI_SESSION) as client:
            result = await client.summarize("https://example.com")
        assert isinstance(result, SummaryResult)
        assert result.title == "Test"

    @respx.mock
    async def test_assistant(self) -> None:
        _mock_auth()
        respx.post(ASSISTANT_URL).mock(
            return_value=httpx.Response(200, text=ASSISTANT_STREAM)
        )
        async with KagiClient(kagi_session=FAKE_KAGI_SESSION) as client:
            result = await client.prompt("Hi")
        assert isinstance(result, AssistantResult)
        assert result.message.md == "Hello"

    @respx.mock
    async def test_search(self) -> None:
        _mock_auth()
        respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, text=SEARCH_SSE))
        async with KagiClient(kagi_session=FAKE_KAGI_SESSION) as client:
            result = await client.search("test")
        assert isinstance(result, SearchResult)
        assert "Result" in result.search_html
