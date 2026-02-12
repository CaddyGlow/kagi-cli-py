from __future__ import annotations

import csv
import io
import json

from kagi_client.formatters import (
    OutputFormat,
    ask_csv,
    ask_json,
    ask_md,
    proofread_csv,
    proofread_json,
    proofread_md,
    search_csv,
    search_json,
    search_md,
    summarize_csv,
    summarize_json,
    summarize_md,
)
from kagi_client.models import (
    AssistantMessage,
    AssistantResult,
    AssistantThread,
    DetectedLanguage,
    DomainInfo,
    ProofreadAnalysis,
    ProofreadResult,
    ResponseMetadata,
    SearchInfo,
    SearchItem,
    SearchResult,
    SummaryResult,
    ToneAnalysis,
    WordStats,
    WritingStatistics,
)


# -- fixtures --


def _proofread_result() -> ProofreadResult:
    return ProofreadResult(
        detected_language=DetectedLanguage(iso="en", label="English"),
        text="Hello world.",
        analysis=ProofreadAnalysis(
            corrected_text="Hello world.",
            changes=[],
            corrections_summary="No corrections needed.",
            tone_analysis=ToneAnalysis(
                overall_tone="neutral", description="Neutral tone"
            ),
            writing_statistics=WritingStatistics(
                word_count=2,
                character_count=12,
                character_count_no_spaces=10,
                paragraph_count=1,
                sentence_count=1,
                average_words_per_sentence=2.0,
                average_characters_per_word=5.0,
                vocabulary_diversity=1.0,
                reading_time_minutes=0.01,
                reading_level="Elementary",
                readability_score=100.0,
            ),
        ),
    )


def _proofread_result_no_analysis() -> ProofreadResult:
    return ProofreadResult(
        detected_language=None,
        text="Just plain text.",
        analysis=None,
    )


def _summary_result() -> SummaryResult:
    return SummaryResult(
        output_text="<p>Key takeaways.</p>",
        markdown="Key takeaways.",
        status="complete",
        word_stats=WordStats(
            n_tokens=100, n_words=80, n_pages=1, time_saved=120, length=500
        ),
        response_metadata=ResponseMetadata(
            speed=1.5,
            tokens=100,
            total_time_second=2.3,
            model="claude-3",
            version="1.0",
            cost=0.001,
        ),
        elapsed_seconds=2.3,
        title="Test Article",
    )


def _assistant_result() -> AssistantResult:
    return AssistantResult(
        thread=AssistantThread(
            id="thread-123",
            title="Test Thread",
            created_at="2025-01-01T00:00:00Z",
            expires_at="2025-01-02T00:00:00Z",
            saved=False,
            shared=False,
        ),
        message=AssistantMessage(
            id="msg-456",
            created_at="2025-01-01T00:00:00Z",
            state="complete",
            prompt="hello",
            reply="<details><summary>Thinking</summary><p>Let me think</p></details><p>Hello! How can I help?</p>",
            md="<details><summary>Thinking</summary>\n\nLet me think\n\n</details>\n\nHello! How can I help?",
        ),
    )


def _assistant_result_no_thinking() -> AssistantResult:
    return AssistantResult(
        thread=AssistantThread(
            id="thread-123",
            title="Test Thread",
            created_at="2025-01-01T00:00:00Z",
            expires_at="2025-01-02T00:00:00Z",
            saved=False,
            shared=False,
        ),
        message=AssistantMessage(
            id="msg-456",
            created_at="2025-01-01T00:00:00Z",
            state="complete",
            prompt="hello",
            reply="Hello! How can I help?",
            md="Hello! How can I help?",
        ),
    )


def _search_result() -> SearchResult:
    return SearchResult(
        search_html="<div>Result</div>",
        info=SearchInfo(
            share_url="https://kagi.com/search?q=test",
            curr_batch=1,
            curr_piece=1,
            next_batch=-1,
            next_piece=1,
        ),
        items=[
            SearchItem(
                title="Example Result",
                url="https://example.com/page",
                description="A great example page.",
                web_archive_url="https://web.archive.org/web/20260212/https://example.com/page",
                date="Feb 12, 2026",
            ),
        ],
        domain_infos=[
            DomainInfo(
                domain="example.com",
                favicon_url="https://p.kagi.com/proxy/favicons?c=abc",
                domain_secure=True,
                trackers=5,
                registration_date="1995-08-14",
                website_speed="Fast",
            ),
        ],
    )


# -- OutputFormat enum --


class TestOutputFormat:
    def test_values(self) -> None:
        assert set(OutputFormat) == {
            OutputFormat.console,
            OutputFormat.json,
            OutputFormat.md,
            OutputFormat.csv,
        }

    def test_string_values(self) -> None:
        assert OutputFormat.console.value == "console"
        assert OutputFormat.json.value == "json"
        assert OutputFormat.md.value == "md"
        assert OutputFormat.csv.value == "csv"


# -- proofread JSON --


class TestProofreadJson:
    def test_valid_json(self) -> None:
        result = proofread_json(_proofread_result())
        parsed = json.loads(result)
        assert parsed["text"] == "Hello world."
        assert parsed["analysis"]["corrected_text"] == "Hello world."

    def test_statistics_present(self) -> None:
        parsed = json.loads(proofread_json(_proofread_result()))
        stats = parsed["analysis"]["writing_statistics"]
        assert stats["word_count"] == 2
        assert stats["readability_score"] == 100.0

    def test_no_analysis(self) -> None:
        parsed = json.loads(proofread_json(_proofread_result_no_analysis()))
        assert parsed["analysis"] is None
        assert parsed["text"] == "Just plain text."


# -- proofread MD --


class TestProofreadMd:
    def test_headings(self) -> None:
        result = proofread_md(_proofread_result())
        assert "## Corrected Text" in result
        assert "## Corrections" in result
        assert "## Tone" in result
        assert "## Writing Statistics" in result

    def test_content(self) -> None:
        result = proofread_md(_proofread_result())
        assert "Hello world." in result
        assert "No corrections needed." in result
        assert "neutral" in result

    def test_table(self) -> None:
        result = proofread_md(_proofread_result())
        assert "| Word Count | 2 |" in result
        assert "| Reading Level | Elementary |" in result

    def test_no_analysis(self) -> None:
        result = proofread_md(_proofread_result_no_analysis())
        assert "Just plain text." in result


# -- proofread CSV --


class TestProofreadCsv:
    def test_header(self) -> None:
        result = proofread_csv(_proofread_result())
        reader = csv.reader(io.StringIO(result))
        header = next(reader)
        assert header == ["metric", "value"]

    def test_rows(self) -> None:
        result = proofread_csv(_proofread_result())
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        metrics = [row[0] for row in rows[1:]]
        assert "corrected_text" in metrics
        assert "word_count" in metrics
        assert "reading_level" in metrics

    def test_no_analysis(self) -> None:
        result = proofread_csv(_proofread_result_no_analysis())
        reader = csv.reader(io.StringIO(result))
        header = next(reader)
        assert header == ["text"]
        row = next(reader)
        assert row == ["Just plain text."]


# -- summarize JSON --


class TestSummarizeJson:
    def test_valid_json(self) -> None:
        parsed = json.loads(summarize_json(_summary_result()))
        assert parsed["title"] == "Test Article"
        assert parsed["markdown"] == "Key takeaways."

    def test_metadata(self) -> None:
        parsed = json.loads(summarize_json(_summary_result()))
        assert parsed["response_metadata"]["model"] == "claude-3"
        assert parsed["word_stats"]["n_words"] == 80


# -- summarize MD --


class TestSummarizeMd:
    def test_title(self) -> None:
        result = summarize_md(_summary_result())
        assert "# Test Article" in result

    def test_summary_content(self) -> None:
        result = summarize_md(_summary_result())
        assert "Key takeaways." in result

    def test_metadata_table(self) -> None:
        result = summarize_md(_summary_result())
        assert "## Metadata" in result
        assert "| Model | claude-3 |" in result
        assert "| Source Words | 80 |" in result


# -- summarize CSV --


class TestSummarizeCsv:
    def test_header(self) -> None:
        result = summarize_csv(_summary_result())
        reader = csv.reader(io.StringIO(result))
        header = next(reader)
        assert header == ["field", "value"]

    def test_fields(self) -> None:
        result = summarize_csv(_summary_result())
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        fields = {row[0]: row[1] for row in rows[1:]}
        assert fields["title"] == "Test Article"
        assert fields["model"] == "claude-3"
        assert fields["source_words"] == "80"


# -- ask JSON --


class TestAskJson:
    def test_valid_json(self) -> None:
        parsed = json.loads(ask_json(_assistant_result()))
        assert parsed["thread"]["id"] == "thread-123"

    def test_response_field_strips_thinking(self) -> None:
        parsed = json.loads(ask_json(_assistant_result()))
        assert parsed["response"] == "Hello! How can I help?"
        assert "Thinking" not in parsed["response"]

    def test_response_field_no_thinking(self) -> None:
        parsed = json.loads(ask_json(_assistant_result_no_thinking()))
        assert parsed["response"] == "Hello! How can I help?"

    def test_raw_fields_preserved(self) -> None:
        parsed = json.loads(ask_json(_assistant_result()))
        assert "<details>" in parsed["message"]["reply"]
        assert "<details>" in parsed["message"]["md"]


# -- ask MD --


class TestAskMd:
    def test_strips_thinking(self) -> None:
        result = ask_md(_assistant_result())
        assert "Hello! How can I help?" in result
        assert "<details>" not in result
        assert "Thinking" not in result

    def test_no_thinking(self) -> None:
        result = ask_md(_assistant_result_no_thinking())
        assert "Hello! How can I help?" in result

    def test_fallback_to_reply(self) -> None:
        ar = _assistant_result_no_thinking()
        ar.message.md = None
        result = ask_md(ar)
        assert "Hello! How can I help?" in result

    def test_empty_when_no_content(self) -> None:
        ar = _assistant_result_no_thinking()
        ar.message.md = None
        ar.message.reply = None
        assert ask_md(ar) == ""


# -- ask CSV --


class TestAskCsv:
    def test_header_and_row(self) -> None:
        result = ask_csv(_assistant_result())
        reader = csv.reader(io.StringIO(result))
        header = next(reader)
        assert header == ["thread_id", "message_id", "prompt", "response"]
        row = next(reader)
        assert row[0] == "thread-123"
        assert row[2] == "hello"

    def test_response_strips_thinking(self) -> None:
        result = ask_csv(_assistant_result())
        reader = csv.reader(io.StringIO(result))
        next(reader)  # skip header
        row = next(reader)
        assert row[3] == "Hello! How can I help?"
        assert "Thinking" not in row[3]


# -- search JSON --


class TestSearchJson:
    def test_single_result(self) -> None:
        parsed = json.loads(search_json([_search_result()]))
        assert parsed["info"]["share_url"] == "https://kagi.com/search?q=test"
        assert parsed["items"][0]["title"] == "Example Result"

    def test_multiple_results(self) -> None:
        parsed = json.loads(search_json([_search_result(), _search_result()]))
        assert isinstance(parsed, list)
        assert len(parsed) == 2

    def test_domain_infos(self) -> None:
        parsed = json.loads(search_json([_search_result()]))
        assert parsed["domain_infos"][0]["domain"] == "example.com"


# -- search MD --


class TestSearchMd:
    def test_result_links(self) -> None:
        result = search_md([_search_result()])
        assert "[Example Result](https://example.com/page)" in result

    def test_description(self) -> None:
        result = search_md([_search_result()])
        assert "A great example page." in result

    def test_archive_link(self) -> None:
        result = search_md([_search_result()])
        assert "[Archive](" in result

    def test_share_url(self) -> None:
        result = search_md([_search_result()])
        assert "**Share:** https://kagi.com/search?q=test" in result


# -- search CSV --


class TestSearchCsv:
    def test_header(self) -> None:
        result = search_csv([_search_result()])
        reader = csv.reader(io.StringIO(result))
        header = next(reader)
        assert header == ["title", "url", "description", "archive_url", "date"]

    def test_rows(self) -> None:
        result = search_csv([_search_result()])
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        assert len(rows) == 2  # header + 1 item
        assert rows[1][0] == "Example Result"
        assert rows[1][1] == "https://example.com/page"

    def test_multiple_results(self) -> None:
        result = search_csv([_search_result(), _search_result()])
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        assert len(rows) == 3  # header + 2 items
