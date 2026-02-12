from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from kagi_client.auth import KagiAuth
from kagi_client.errors import APIError
from kagi_client.models import (
    DetectedLanguage,
    ProofreadAnalysis,
    ProofreadResult,
    ToneAnalysis,
    WritingStatistics,
)
from kagi_client.streams import parse_sse_events

PROOFREAD_URL = "https://translate.kagi.com/api/proofread"


class ProofreadClient:
    def __init__(self, auth: KagiAuth) -> None:
        self._auth = auth

    async def _request(
        self,
        text: str,
        source_lang: str = "auto",
        writing_style: str = "general",
        correction_level: str = "standard",
        formality: str = "default",
        context: str = "",
        model: str = "standard",
    ) -> httpx.Response:
        token = await self._auth.get_valid_token()
        body = {
            "text": text,
            "source_lang": source_lang,
            "session_token": token,
            "model": model,
            "stream": True,
            "writing_style": writing_style,
            "correction_level": correction_level,
            "formality": formality,
            "context": context,
            "explanation_language": "en",
        }
        timeout = httpx.Timeout(10.0, read=300.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                PROOFREAD_URL,
                json=body,
                headers={
                    "content-type": "application/json",
                    "referer": "https://translate.kagi.com/proofread",
                },
            )
        if resp.status_code != 200:
            raise APIError(
                f"Proofread request failed: {resp.status_code}",
                status_code=resp.status_code,
                body=resp.text,
            )
        return resp

    async def proofread(
        self,
        text: str,
        source_lang: str = "auto",
        writing_style: str = "general",
        correction_level: str = "standard",
        formality: str = "default",
        context: str = "",
        model: str = "standard",
    ) -> ProofreadResult:
        resp = await self._request(
            text,
            source_lang=source_lang,
            writing_style=writing_style,
            correction_level=correction_level,
            formality=formality,
            context=context,
            model=model,
        )
        return _parse_proofread_response(resp.text)

    async def proofread_stream(
        self,
        text: str,
        source_lang: str = "auto",
        writing_style: str = "general",
        correction_level: str = "standard",
        formality: str = "default",
        context: str = "",
        model: str = "standard",
    ) -> AsyncIterator[dict[str, Any]]:
        resp = await self._request(
            text,
            source_lang=source_lang,
            writing_style=writing_style,
            correction_level=correction_level,
            formality=formality,
            context=context,
            model=model,
        )
        events = parse_sse_events(resp.text)
        for event in events:
            yield json.loads(event.data)


def _parse_writing_stats(raw: dict[str, Any]) -> WritingStatistics:
    return WritingStatistics(
        word_count=raw["word_count"],
        character_count=raw["character_count"],
        character_count_no_spaces=raw["character_count_no_spaces"],
        paragraph_count=raw["paragraph_count"],
        sentence_count=raw["sentence_count"],
        average_words_per_sentence=raw["average_words_per_sentence"],
        average_characters_per_word=raw["average_characters_per_word"],
        vocabulary_diversity=raw["vocabulary_diversity"],
        reading_time_minutes=raw["reading_time_minutes"],
        reading_level=raw["reading_level"],
        readability_score=raw["readability_score"],
    )


def _parse_proofread_response(response_text: str) -> ProofreadResult:
    events = parse_sse_events(response_text)
    detected_language: DetectedLanguage | None = None
    text_parts: list[str] = []
    analysis: ProofreadAnalysis | None = None

    for event in events:
        data = json.loads(event.data)

        if "detected_language" in data:
            dl = data["detected_language"]
            detected_language = DetectedLanguage(iso=dl["iso"], label=dl["label"])
        elif "delta" in data:
            text_parts.append(data["delta"])
        elif "analysis" in data:
            a = data["analysis"]
            ta = a["tone_analysis"]
            ws = a["writing_statistics"]
            analysis = ProofreadAnalysis(
                corrected_text=a["corrected_text"],
                changes=a.get("changes", []),
                corrections_summary=a["corrections_summary"],
                tone_analysis=ToneAnalysis(
                    overall_tone=ta["overall_tone"],
                    description=ta["description"],
                ),
                writing_statistics=_parse_writing_stats(ws),
            )

    return ProofreadResult(
        detected_language=detected_language,
        text="".join(text_parts),
        analysis=analysis,
    )
