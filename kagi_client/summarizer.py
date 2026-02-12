from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from kagi_client.auth import KagiAuth
from kagi_client.errors import APIError
from kagi_client.models import (
    ResponseMetadata,
    SummaryResult,
    SummaryUpdate,
    WordStats,
)
from kagi_client.streams import parse_kagi_stream_lines

SUMMARIZER_URL = "https://kagi.com/mother/summary_labs"


class SummarizerClient:
    def __init__(self, auth: KagiAuth) -> None:
        self._auth = auth

    async def _request(
        self,
        url: str,
        summary_type: str = "takeaway",
    ) -> httpx.Response:
        timeout = httpx.Timeout(10.0, read=300.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(
                SUMMARIZER_URL,
                params={
                    "url": url,
                    "stream": "1",
                    "target_language": "",
                    "summary_type": summary_type,
                },
                cookies={"kagi_session": self._auth.kagi_session},
                headers={
                    "accept": "application/vnd.kagi.stream",
                    "referer": "https://kagi.com/summarizer",
                },
            )
        if resp.status_code != 200:
            raise APIError(
                f"Summarizer request failed: {resp.status_code}",
                status_code=resp.status_code,
                body=resp.text,
            )
        return resp

    async def summarize(
        self,
        url: str,
        summary_type: str = "takeaway",
    ) -> SummaryResult:
        resp = await self._request(url, summary_type=summary_type)
        return _parse_summary_response(resp.text)

    async def summarize_stream(
        self,
        url: str,
        summary_type: str = "takeaway",
    ) -> AsyncIterator[SummaryUpdate]:
        resp = await self._request(url, summary_type=summary_type)
        lines = parse_kagi_stream_lines(resp.text)
        for line in lines:
            data = json.loads(line.payload)
            od = data.get("output_data", {})
            ws_raw = od.get("word_stats", {})
            yield SummaryUpdate(
                output_text=data.get("output_text", ""),
                status=od.get("status", ""),
                word_stats=WordStats(
                    n_tokens=ws_raw.get("n_tokens", 0),
                    n_words=ws_raw.get("n_words", 0),
                    n_pages=ws_raw.get("n_pages", 0),
                    time_saved=ws_raw.get("time_saved", 0),
                    length=ws_raw.get("length"),
                ),
                tokens=data.get("tokens", 0),
                type=data.get("type", "update"),
            )


def _parse_summary_response(response_text: str) -> SummaryResult:
    lines = parse_kagi_stream_lines(response_text)
    # Find the "final" line
    final_data = None
    for line in lines:
        data = json.loads(line.payload)
        if data.get("type") == "final":
            final_data = data
            break

    if final_data is None:
        # Fall back to last update
        for line in reversed(lines):
            data = json.loads(line.payload)
            if data.get("output_data", {}).get("status") == "completed":
                final_data = data
                break

    if final_data is None:
        # Use the last line
        final_data = json.loads(lines[-1].payload)

    od = final_data.get("output_data", {})
    ws_raw = od.get("word_stats", {})
    rm_raw = od.get("response_metadata", {})

    return SummaryResult(
        output_text=final_data.get("output_text", ""),
        markdown=od.get("markdown", ""),
        status=od.get("status", ""),
        word_stats=WordStats(
            n_tokens=ws_raw.get("n_tokens", 0),
            n_words=ws_raw.get("n_words", 0),
            n_pages=ws_raw.get("n_pages", 0),
            time_saved=ws_raw.get("time_saved", 0),
            length=ws_raw.get("length"),
        ),
        response_metadata=ResponseMetadata(
            speed=rm_raw.get("speed"),
            tokens=rm_raw.get("tokens", 0),
            total_time_second=rm_raw.get("total_time_second", 0),
            model=rm_raw.get("model", ""),
            version=rm_raw.get("version", ""),
            cost=rm_raw.get("cost", 0),
        ),
        elapsed_seconds=od.get("elapsed_seconds"),
        title=od.get("title", ""),
    )
