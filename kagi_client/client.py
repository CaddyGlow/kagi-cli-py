from __future__ import annotations

from collections.abc import AsyncIterator
from types import TracebackType
from typing import Any

from kagi_client.assistant import AssistantClient
from kagi_client.auth import KagiAuth
from kagi_client.models import (
    AssistantResult,
    ProofreadResult,
    SearchResult,
    SummaryResult,
    SummaryUpdate,
)
from kagi_client.proofread import ProofreadClient
from kagi_client.search import SearchClient
from kagi_client.summarizer import SummarizerClient


class KagiClient:
    def __init__(self, kagi_session: str) -> None:
        self._auth = KagiAuth(kagi_session=kagi_session)
        self._proofread = ProofreadClient(auth=self._auth)
        self._summarizer = SummarizerClient(auth=self._auth)
        self._assistant = AssistantClient(auth=self._auth)
        self._search = SearchClient(auth=self._auth)

    async def __aenter__(self) -> KagiClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        pass

    # -- Proofread --

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
        return await self._proofread.proofread(
            text,
            source_lang=source_lang,
            writing_style=writing_style,
            correction_level=correction_level,
            formality=formality,
            context=context,
            model=model,
        )

    async def proofread_stream(
        self,
        text: str,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        async for event in self._proofread.proofread_stream(text, **kwargs):
            yield event

    # -- Summarizer --

    async def summarize(
        self,
        url: str,
        summary_type: str = "takeaway",
    ) -> SummaryResult:
        return await self._summarizer.summarize(url, summary_type=summary_type)

    async def summarize_stream(
        self,
        url: str,
        summary_type: str = "takeaway",
    ) -> AsyncIterator[SummaryUpdate]:
        async for update in self._summarizer.summarize_stream(
            url, summary_type=summary_type
        ):
            yield update

    # -- Assistant --

    async def prompt(
        self,
        text: str,
        model: str = "gpt-5-mini",
        thread_id: str | None = None,
        internet_access: bool = True,
    ) -> AssistantResult:
        return await self._assistant.prompt(
            text,
            model=model,
            thread_id=thread_id,
            internet_access=internet_access,
        )

    async def prompt_stream(
        self,
        text: str,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        async for token in self._assistant.prompt_stream(text, **kwargs):
            yield token

    # -- Search --

    async def search(
        self,
        query: str,
        batch: int | None = None,
    ) -> SearchResult:
        return await self._search.search(query, batch=batch)

    async def search_all(
        self,
        query: str,
    ) -> AsyncIterator[SearchResult]:
        async for result in self._search.search_all(query):
            yield result
