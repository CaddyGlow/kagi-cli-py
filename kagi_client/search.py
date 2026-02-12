from __future__ import annotations

import json
import re
import secrets
from collections.abc import AsyncIterator
from html.parser import HTMLParser

import httpx

from kagi_client.auth import KagiAuth
from kagi_client.errors import APIError
from kagi_client.models import DomainInfo, SearchInfo, SearchItem, SearchResult
from kagi_client.streams import parse_sse_events

SEARCH_URL = "https://kagi.com/socket/search"


class SearchClient:
    def __init__(self, auth: KagiAuth) -> None:
        self._auth = auth

    async def _request(
        self,
        query: str,
        batch: int | None = None,
    ) -> httpx.Response:
        params: dict[str, str] = {"q": query}
        if batch is not None:
            params["batch"] = str(batch)
        else:
            params["nonce"] = secrets.token_hex(16)

        timeout = httpx.Timeout(10.0, read=300.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(
                SEARCH_URL,
                params=params,
                cookies={"kagi_session": self._auth.kagi_session},
                headers={
                    "accept": "text/event-stream",
                    "x-kagi-authorization": self._auth.kagi_session,
                    "referer": f"https://kagi.com/search?q={query}",
                },
            )
        if resp.status_code != 200:
            raise APIError(
                f"Search request failed: {resp.status_code}",
                status_code=resp.status_code,
                body=resp.text,
            )
        return resp

    async def search(
        self,
        query: str,
        batch: int | None = None,
    ) -> SearchResult:
        resp = await self._request(query, batch=batch)
        return _parse_search_response(resp.text)

    async def search_all(
        self,
        query: str,
    ) -> AsyncIterator[SearchResult]:
        result = await self.search(query)
        yield result
        while result.info.next_batch > 0:
            result = await self.search(query, batch=result.info.next_batch)
            yield result


class _TextExtractor(HTMLParser):
    """Extract plain text from HTML, stripping all tags."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts).strip()


def _extract_text(html: str) -> str:
    extractor = _TextExtractor()
    extractor.feed(html)
    return extractor.get_text()


# Split HTML into individual result blocks (each starts with _0_SRI class div)
_RESULT_BLOCK_RE = re.compile(r'<div\s+class="[^"]*_0_SRI[^"]*"', re.DOTALL)

# Extract URL and title from the title link
_TITLE_LINK_RE = re.compile(
    r'<a\s+class="[^"]*__sri_title_link[^"]*"[^>]*'
    r'href="([^"]*)"[^>]*>(.*?)</a>',
    re.DOTALL,
)

# Extract description from __sri-desc div
_DESC_RE = re.compile(
    r'<div\s+class="[^"]*__sri-desc[^"]*"[^>]*>(.*?)</div>\s*</div>',
    re.DOTALL,
)

# Extract date from __sri-time span
_DATE_RE = re.compile(
    r'<span\s+class="[^"]*__sri-time[^"]*"[^>]*>(.*?)</span>',
    re.DOTALL,
)

# Extract web archive URL
_ARCHIVE_RE = re.compile(
    r'href="(https://web\.archive\.org/[^"]*)"',
)


def _parse_search_items(html: str) -> list[SearchItem]:
    """Parse search result HTML into structured SearchItem objects."""
    items: list[SearchItem] = []

    # Find start positions of each result block
    starts = [m.start() for m in _RESULT_BLOCK_RE.finditer(html)]
    if not starts:
        return items

    # Split into blocks (each block runs from one start to the next)
    blocks: list[str] = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(html)
        blocks.append(html[start:end])

    for block in blocks:
        title_m = _TITLE_LINK_RE.search(block)
        if not title_m:
            continue

        url = title_m.group(1)
        title = _extract_text(title_m.group(2))

        desc_m = _DESC_RE.search(block)
        description = _extract_text(desc_m.group(1)) if desc_m else ""

        date_m = _DATE_RE.search(block)
        date = _extract_text(date_m.group(1)) if date_m else None

        archive_m = _ARCHIVE_RE.search(block)
        web_archive_url = archive_m.group(1) if archive_m else None

        items.append(
            SearchItem(
                title=title,
                url=url,
                description=description,
                web_archive_url=web_archive_url,
                date=date,
            )
        )

    return items


def _parse_search_response(response_text: str) -> SearchResult:
    events = parse_sse_events(response_text)

    search_html_parts: list[str] = []
    info: SearchInfo | None = None
    domain_infos: list[DomainInfo] = []

    for event in events:
        if not event.data or not event.data.strip():
            continue
        try:
            items = json.loads(event.data)
        except json.JSONDecodeError:
            continue

        if not isinstance(items, list):
            continue

        for item in items:
            tag = item.get("tag", "")
            payload = item.get("payload")

            if tag == "search":
                if isinstance(payload, dict):
                    search_html_parts.append(payload.get("content", ""))
                elif isinstance(payload, str):
                    search_html_parts.append(payload)

            elif tag == "search.info":
                if isinstance(payload, dict):
                    info = SearchInfo(
                        share_url=payload.get("share_url", ""),
                        curr_batch=payload.get("curr_batch", 1),
                        curr_piece=payload.get("curr_piece", 1),
                        next_batch=payload.get("next_batch", -1),
                        next_piece=payload.get("next_piece", 1),
                    )

            elif tag == "domain_info":
                raw = payload
                if isinstance(raw, str):
                    raw = json.loads(raw)
                if isinstance(raw, dict):
                    for d in raw.get("data", []):
                        domain_infos.append(
                            DomainInfo(
                                domain=d.get("domain", ""),
                                favicon_url=d.get("favicon_url"),
                                domain_secure=d.get("domain_secure"),
                                trackers=d.get("trackers"),
                                registration_date=d.get("registration_date"),
                                website_speed=d.get("website_speed"),
                                rule_type=d.get("rule_type"),
                                description=d.get("description"),
                            )
                        )

    if info is None:
        info = SearchInfo(
            share_url="",
            curr_batch=1,
            curr_piece=1,
            next_batch=-1,
            next_piece=1,
        )

    full_html = "\n".join(search_html_parts)
    return SearchResult(
        search_html=full_html,
        info=info,
        items=_parse_search_items(full_html),
        domain_infos=domain_infos,
    )
