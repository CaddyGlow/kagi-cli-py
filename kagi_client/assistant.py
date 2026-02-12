from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from kagi_client.auth import KagiAuth
from kagi_client.errors import APIError
from kagi_client.models import AssistantMessage, AssistantResult, AssistantThread
from kagi_client.streams import parse_kagi_stream_line, parse_kagi_stream_lines

_decoder = json.JSONDecoder()


def _parse_json(payload: str) -> Any:
    """Parse the first JSON object from a payload, ignoring trailing data."""
    obj, _ = _decoder.raw_decode(payload.strip())
    return obj


ASSISTANT_URL = "https://kagi.com/assistant/prompt"


class AssistantClient:
    def __init__(self, auth: KagiAuth) -> None:
        self._auth = auth

    def _build_body(
        self,
        text: str,
        model: str = "gpt-5-mini",
        thread_id: str | None = None,
        internet_access: bool = True,
    ) -> dict[str, Any]:
        return {
            "focus": {
                "thread_id": thread_id,
                "branch_id": "00000000-0000-4000-0000-000000000000",
                "prompt": text,
            },
            "profile": {
                "id": None,
                "personalizations": True,
                "internet_access": internet_access,
                "model": model,
                "lens_id": None,
            },
            "threads": [{"tag_ids": [], "saved": False, "shared": False}],
        }

    def _headers(self) -> dict[str, str]:
        return {
            "accept": "application/vnd.kagi.stream",
            "content-type": "application/json",
            "origin": "https://kagi.com",
            "referer": "https://kagi.com/assistant",
        }

    def _cookies(self) -> dict[str, str]:
        return {"kagi_session": self._auth.kagi_session}

    async def _request(
        self,
        text: str,
        model: str = "gpt-5-mini",
        thread_id: str | None = None,
        internet_access: bool = True,
    ) -> httpx.Response:
        body = self._build_body(text, model, thread_id, internet_access)
        timeout = httpx.Timeout(10.0, read=300.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                ASSISTANT_URL,
                json=body,
                cookies=self._cookies(),
                headers=self._headers(),
            )
        if resp.status_code != 200:
            raise APIError(
                f"Assistant request failed: {resp.status_code}",
                status_code=resp.status_code,
                body=resp.text,
            )
        return resp

    async def prompt(
        self,
        text: str,
        model: str = "gpt-5-mini",
        thread_id: str | None = None,
        internet_access: bool = True,
    ) -> AssistantResult:
        resp = await self._request(
            text,
            model=model,
            thread_id=thread_id,
            internet_access=internet_access,
        )
        return _parse_assistant_response(resp.text)

    async def prompt_stream(
        self,
        text: str,
        model: str = "gpt-5-mini",
        thread_id: str | None = None,
        internet_access: bool = True,
    ) -> AsyncIterator[str]:
        """Stream tokens via HTTP streaming, yielding full accumulated HTML snapshots."""
        body = self._build_body(text, model, thread_id, internet_access)
        prev_text = ""
        timeout = httpx.Timeout(10.0, read=300.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                ASSISTANT_URL,
                json=body,
                cookies=self._cookies(),
                headers=self._headers(),
            ) as resp:
                if resp.status_code != 200:
                    await resp.aread()
                    raise APIError(
                        f"Assistant request failed: {resp.status_code}",
                        status_code=resp.status_code,
                        body=resp.text,
                    )
                async for raw_line in resp.aiter_lines():
                    parsed = parse_kagi_stream_line(raw_line)
                    if parsed is None or parsed.tag != "tokens.json":
                        continue
                    try:
                        data = _parse_json(parsed.payload)
                    except (json.JSONDecodeError, ValueError):
                        continue
                    full_text = data.get("text", "")
                    if full_text and full_text != prev_text:
                        prev_text = full_text
                        yield full_text


def _parse_assistant_response(response_text: str) -> AssistantResult:
    lines = parse_kagi_stream_lines(response_text)

    thread: AssistantThread | None = None
    message: AssistantMessage | None = None

    for line in lines:
        if line.tag == "thread.json":
            data = _parse_json(line.payload)
            thread = AssistantThread(
                id=data["id"],
                title=data["title"],
                created_at=data["created_at"],
                expires_at=data.get("expires_at", ""),
                saved=data.get("saved", False),
                shared=data.get("shared", False),
            )
        elif line.tag == "new_message.json":
            data = _parse_json(line.payload)
            # Keep the last new_message (the "done" state one)
            message = AssistantMessage(
                id=data["id"],
                created_at=data["created_at"],
                state=data["state"],
                prompt=data["prompt"],
                reply=data.get("reply"),
                md=data.get("md"),
            )

    if thread is None:
        raise APIError(
            "No thread.json found in response",
            status_code=200,
            body=response_text,
        )
    if message is None:
        raise APIError(
            "No new_message.json found in response",
            status_code=200,
            body=response_text,
        )

    return AssistantResult(thread=thread, message=message)
