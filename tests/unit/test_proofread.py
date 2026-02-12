from __future__ import annotations

import httpx
import pytest
import respx

from kagi_client.auth import KagiAuth
from kagi_client.errors import APIError
from kagi_client.models import ProofreadResult
from kagi_client.proofread import ProofreadClient
from tests.conftest import make_jwt_token

PROOFREAD_URL = "https://translate.kagi.com/api/proofread"

SSE_RESPONSE = (
    "event: message\n"
    'data: {"detected_language":{"iso":"en","label":"English"}}\n'
    "\n"
    "event: message\n"
    'data: {"delta":"Hello world"}\n'
    "\n"
    "event: message\n"
    'data: {"text_done":true}\n'
    "\n"
    "event: message\n"
    'data: {"analysis":{"corrected_text":"Hello world","changes":[],'
    '"corrections_summary":"No corrections needed.",'
    '"tone_analysis":{"overall_tone":"neutral","description":"Neutral tone."},'
    '"voice_consistency":{"active_voice_percentage":100,"passive_voice_percentage":0,'
    '"is_consistent":true,"passive_instances":[],"summary":"Active voice."},'
    '"repetition_detection":{"repeated_words":[],"repeated_phrases":[],'
    '"summary":"No repetition."},'
    '"writing_statistics":{"word_count":2,"character_count":11,'
    '"character_count_no_spaces":10,"paragraph_count":1,"sentence_count":1,'
    '"average_words_per_sentence":2.0,"average_characters_per_word":5.0,'
    '"sentence_length_distribution":{"short":1,"medium":0,"long":0},'
    '"vocabulary_diversity":1.0,"reading_time_minutes":0.1,'
    '"complex_sentences":0,"simple_sentences":1,'
    '"reading_level":"elementary","readability_score":20.0},'
    '"explanation_language":"en"}}\n'
    "\n"
    "event: message\n"
    'data: {"done":true}\n'
    "\n"
)


def _make_auth() -> KagiAuth:
    auth = KagiAuth(kagi_session="fake")
    auth._token = make_jwt_token()
    return auth


class TestProofreadClient:
    @respx.mock
    async def test_proofread_returns_result(self) -> None:
        respx.post(PROOFREAD_URL).mock(
            return_value=httpx.Response(200, text=SSE_RESPONSE)
        )
        auth = _make_auth()
        client = ProofreadClient(auth=auth)
        result = await client.proofread("Hello world")
        assert isinstance(result, ProofreadResult)
        assert result.text == "Hello world"
        assert result.detected_language is not None
        assert result.detected_language.iso == "en"
        assert result.analysis is not None
        assert result.analysis.corrected_text == "Hello world"
        assert result.analysis.writing_statistics.word_count == 2

    @respx.mock
    async def test_proofread_with_options(self) -> None:
        respx.post(PROOFREAD_URL).mock(
            return_value=httpx.Response(200, text=SSE_RESPONSE)
        )
        auth = _make_auth()
        client = ProofreadClient(auth=auth)
        result = await client.proofread(
            "Hello world",
            source_lang="en",
            writing_style="academic",
            correction_level="aggressive",
            formality="formal",
            context="test context",
        )
        assert isinstance(result, ProofreadResult)

    @respx.mock
    async def test_proofread_raises_on_http_error(self) -> None:
        respx.post(PROOFREAD_URL).mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        auth = _make_auth()
        client = ProofreadClient(auth=auth)
        with pytest.raises(APIError) as exc_info:
            await client.proofread("test")
        assert exc_info.value.status_code == 500

    @respx.mock
    async def test_proofread_stream(self) -> None:
        respx.post(PROOFREAD_URL).mock(
            return_value=httpx.Response(200, text=SSE_RESPONSE)
        )
        auth = _make_auth()
        client = ProofreadClient(auth=auth)
        events = []
        async for event in client.proofread_stream("Hello world"):
            events.append(event)
        # Should get: detected_language, delta, text_done, analysis, done
        assert len(events) == 5
