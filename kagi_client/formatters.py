from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from enum import Enum

from kagi_client.models import (
    AssistantResult,
    ProofreadResult,
    SearchResult,
    SummaryResult,
)


class OutputFormat(str, Enum):
    console = "console"
    json = "json"
    md = "md"
    csv = "csv"


# -- helpers --


def _to_json(obj: object) -> str:
    return json.dumps(asdict(obj), indent=2, ensure_ascii=False)  # type: ignore[arg-type]


def _strip_details(text: str) -> str:
    """Remove the <details>...</details> thinking block and return the rest."""
    import re

    return re.sub(r"<details>.*?</details>\s*", "", text, flags=re.DOTALL).strip()


def _strip_html(html: str) -> str:
    """Remove all HTML tags, keeping only text content."""
    import re

    return re.sub(r"<[^>]+>", "", html).strip()


def _extract_response(result: AssistantResult) -> str:
    """Extract the clean response text from an AssistantResult, without thinking."""
    if result.message.md:
        return _strip_details(result.message.md)
    if result.message.reply:
        return _strip_html(_strip_details(result.message.reply))
    return ""


def _csv_rows(header: list[str], rows: list[list[str]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(header)
    writer.writerows(rows)
    return buf.getvalue()


# -- proofread --


def proofread_json(result: ProofreadResult) -> str:
    return _to_json(result)


def proofread_md(result: ProofreadResult) -> str:
    parts: list[str] = []
    if result.analysis:
        a = result.analysis
        parts.append(f"## Corrected Text\n\n{a.corrected_text}")
        parts.append(f"## Corrections\n\n{a.corrections_summary}")
        t = a.tone_analysis
        parts.append(f"## Tone\n\n**{t.overall_tone}** -- {t.description}")
        s = a.writing_statistics
        lines = [
            "## Writing Statistics\n",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Word Count | {s.word_count} |",
            f"| Character Count | {s.character_count} |",
            f"| Sentences | {s.sentence_count} |",
            f"| Paragraphs | {s.paragraph_count} |",
            f"| Avg Words/Sentence | {s.average_words_per_sentence:.1f} |",
            f"| Vocabulary Diversity | {s.vocabulary_diversity:.2f} |",
            f"| Reading Level | {s.reading_level} |",
            f"| Readability Score | {s.readability_score:.1f} |",
            f"| Reading Time | {s.reading_time_minutes:.1f} min |",
        ]
        parts.append("\n".join(lines))
    else:
        parts.append(result.text)
    return "\n\n".join(parts) + "\n"


def proofread_csv(result: ProofreadResult) -> str:
    if not result.analysis:
        return _csv_rows(["text"], [[result.text]])
    a = result.analysis
    s = a.writing_statistics
    return _csv_rows(
        ["metric", "value"],
        [
            ["corrected_text", a.corrected_text],
            ["corrections_summary", a.corrections_summary],
            [
                "tone",
                f"{a.tone_analysis.overall_tone}: {a.tone_analysis.description}",
            ],
            ["word_count", str(s.word_count)],
            ["character_count", str(s.character_count)],
            ["sentence_count", str(s.sentence_count)],
            ["paragraph_count", str(s.paragraph_count)],
            ["avg_words_per_sentence", f"{s.average_words_per_sentence:.1f}"],
            ["vocabulary_diversity", f"{s.vocabulary_diversity:.2f}"],
            ["reading_level", s.reading_level],
            ["readability_score", f"{s.readability_score:.1f}"],
            ["reading_time_minutes", f"{s.reading_time_minutes:.1f}"],
        ],
    )


# -- summarize --


def summarize_json(result: SummaryResult) -> str:
    return _to_json(result)


def summarize_md(result: SummaryResult) -> str:
    parts: list[str] = []
    parts.append(f"# {result.title}")
    parts.append(result.markdown)
    meta = result.response_metadata
    ws = result.word_stats
    rows = [
        "## Metadata\n",
        "| Field | Value |",
        "|-------|-------|",
        f"| Model | {meta.model} |",
    ]
    if meta.speed is not None:
        rows.append(f"| Speed | {meta.speed:.1f} tok/s |")
    rows.append(f"| Tokens | {meta.tokens} |")
    rows.append(f"| Cost | ${meta.cost:.4f} |")
    if result.elapsed_seconds is not None:
        rows.append(f"| Elapsed | {result.elapsed_seconds:.1f}s |")
    rows.append(f"| Source Words | {ws.n_words} |")
    rows.append(f"| Source Pages | {ws.n_pages} |")
    rows.append(f"| Time Saved | {ws.time_saved}s |")
    parts.append("\n".join(rows))
    return "\n\n".join(parts) + "\n"


def summarize_csv(result: SummaryResult) -> str:
    meta = result.response_metadata
    ws = result.word_stats
    rows: list[list[str]] = [
        ["title", result.title],
        ["summary", result.markdown],
        ["model", meta.model],
        ["tokens", str(meta.tokens)],
        ["cost", f"{meta.cost:.4f}"],
        ["source_words", str(ws.n_words)],
        ["source_pages", str(ws.n_pages)],
        ["time_saved", str(ws.time_saved)],
    ]
    if meta.speed is not None:
        rows.append(["speed", f"{meta.speed:.1f}"])
    if result.elapsed_seconds is not None:
        rows.append(["elapsed_seconds", f"{result.elapsed_seconds:.1f}"])
    return _csv_rows(["field", "value"], rows)


# -- ask --


def ask_json(result: AssistantResult) -> str:
    data = asdict(result)
    data["response"] = _extract_response(result)
    return json.dumps(data, indent=2, ensure_ascii=False)


def ask_md(result: AssistantResult) -> str:
    response = _extract_response(result)
    if response:
        return response + "\n"
    return ""


def ask_csv(result: AssistantResult) -> str:
    t = result.thread
    m = result.message
    return _csv_rows(
        ["thread_id", "message_id", "prompt", "response"],
        [[t.id, m.id, m.prompt, _extract_response(result)]],
    )


# -- search --


def search_json(results: list[SearchResult]) -> str:
    if len(results) == 1:
        return _to_json(results[0])
    return json.dumps([asdict(r) for r in results], indent=2, ensure_ascii=False)


def search_md(results: list[SearchResult]) -> str:
    parts: list[str] = []
    for result in results:
        for i, item in enumerate(result.items, 1):
            parts.append(f"### {i}. [{item.title}]({item.url})")
            if item.description:
                parts.append(item.description)
            if item.web_archive_url:
                parts.append(f"[Archive]({item.web_archive_url})")
            if item.date:
                parts.append(f"*{item.date}*")
            parts.append("")
        parts.append(f"**Share:** {result.info.share_url}")
    return "\n".join(parts) + "\n"


def search_csv(results: list[SearchResult]) -> str:
    rows: list[list[str]] = []
    for result in results:
        for item in result.items:
            rows.append(
                [
                    item.title,
                    item.url,
                    item.description,
                    item.web_archive_url or "",
                    item.date or "",
                ]
            )
    return _csv_rows(
        ["title", "url", "description", "archive_url", "date"],
        rows,
    )
