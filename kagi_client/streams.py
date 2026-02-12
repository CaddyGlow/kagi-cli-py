from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SSEEvent:
    event: str | None
    data: str
    id: str | None = None


@dataclass
class KagiStreamLine:
    tag: str
    payload: str


def parse_sse_events(text: str) -> list[SSEEvent]:
    """Parse standard Server-Sent Events text into a list of SSEEvent objects."""
    events: list[SSEEvent] = []
    current_event: str | None = None
    current_data: list[str] = []
    current_id: str | None = None

    for line in text.split("\n"):
        if line == "":
            # Empty line = event boundary
            if current_data:
                events.append(
                    SSEEvent(
                        event=current_event,
                        data="\n".join(current_data),
                        id=current_id,
                    )
                )
            current_event = None
            current_data = []
            current_id = None
        elif line.startswith("event:"):
            current_event = line[len("event:") :].strip()
        elif line.startswith("data:"):
            current_data.append(line[len("data:") :].strip())
        elif line.startswith("id:"):
            current_id = line[len("id:") :].strip()
        # Lines starting with ":" are comments -- skip
        # Other bare lines (like "hi") -- skip

    return events


# Regex matching a Kagi stream tag line: "tag:payload" where tag is a word
# possibly with dots/hyphens (e.g., "thread.json", "thread_list.html", "hi",
# "update", "final", "tokens.json").
_TAG_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_.\-]*):(.*)$")


def parse_kagi_stream_line(line: str) -> KagiStreamLine | None:
    """Parse a single Kagi stream line. Returns None if not a tag line."""
    m = _TAG_RE.match(line.strip())
    if m:
        return KagiStreamLine(tag=m.group(1), payload=m.group(2))
    return None


def parse_kagi_stream_lines(text: str) -> list[KagiStreamLine]:
    """Parse Kagi's custom 'tag:payload' streaming format.

    Handles both single-line payloads (JSON) and multi-line payloads (HTML).
    A new tag line starts a new entry; continuation lines (not matching tag
    pattern) are appended to the current entry's payload.
    """
    lines: list[KagiStreamLine] = []
    raw_lines = text.split("\n")
    i = 0

    while i < len(raw_lines):
        raw = raw_lines[i]
        if raw.strip() == "":
            i += 1
            continue

        m = _TAG_RE.match(raw)
        if m:
            tag = m.group(1)
            payload_parts = [m.group(2)]
            i += 1
            # Collect continuation lines (not a new tag, not blank before next tag)
            while i < len(raw_lines):
                next_line = raw_lines[i]
                if next_line.strip() == "":
                    i += 1
                    continue
                if _TAG_RE.match(next_line):
                    break
                payload_parts.append(next_line)
                i += 1
            payload = "\n".join(p for p in payload_parts if p.strip())
            lines.append(KagiStreamLine(tag=tag, payload=payload))
        else:
            i += 1

    return lines
