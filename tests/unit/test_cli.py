from __future__ import annotations

import csv
import io
import json
from importlib import metadata as importlib_metadata
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

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

runner = CliRunner()


def _import_app():
    from kagi_client.cli import app

    return app


def _make_proofread_result() -> ProofreadResult:
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


def _make_summary_result() -> SummaryResult:
    return SummaryResult(
        output_text="<p>Key takeaways from the article.</p>",
        markdown="Key takeaways from the article.",
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


def _make_assistant_result() -> AssistantResult:
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


def _make_search_result() -> SearchResult:
    return SearchResult(
        search_html='<div class="result">Result <b>1</b></div>',
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
                description="A great example page with useful info.",
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


async def _async_iter(items: list[str]):
    for item in items:
        yield item


def _mock_client(**method_results: Any) -> AsyncMock:
    """Create a mock KagiClient with specified method return values."""
    mock = AsyncMock()
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=False)
    for method_name, result in method_results.items():
        getattr(mock, method_name).return_value = result
    return mock


# -- No session tests --


class TestNoSession:
    def test_proofread_no_session(self) -> None:
        app = _import_app()
        result = runner.invoke(app, ["proofread", "hello"], env={"KAGI_SESSION": ""})
        assert result.exit_code != 0
        assert "KAGI_SESSION" in result.output

    def test_summarize_no_session(self) -> None:
        app = _import_app()
        result = runner.invoke(
            app, ["summarize", "https://example.com"], env={"KAGI_SESSION": ""}
        )
        assert result.exit_code != 0
        assert "KAGI_SESSION" in result.output

    def test_ask_no_session(self) -> None:
        app = _import_app()
        result = runner.invoke(app, ["ask", "hello"], env={"KAGI_SESSION": ""})
        assert result.exit_code != 0
        assert "KAGI_SESSION" in result.output

    def test_search_no_session(self) -> None:
        app = _import_app()
        result = runner.invoke(app, ["search", "test query"], env={"KAGI_SESSION": ""})
        assert result.exit_code != 0
        assert "KAGI_SESSION" in result.output


# -- Proofread tests --


class TestProofreadCommand:
    @patch("kagi_client.cli.KagiClient")
    def test_basic(self, mock_cls: Any) -> None:
        mock_cls.return_value = _mock_client(proofread=_make_proofread_result())
        app = _import_app()
        result = runner.invoke(
            app, ["proofread", "hello world"], env={"KAGI_SESSION": "fake"}
        )
        assert result.exit_code == 0
        assert "Hello world." in result.output

    @patch("kagi_client.cli.KagiClient")
    def test_stdin(self, mock_cls: Any) -> None:
        mock_cls.return_value = _mock_client(proofread=_make_proofread_result())
        app = _import_app()
        result = runner.invoke(
            app, ["proofread", "-"], input="hello world", env={"KAGI_SESSION": "fake"}
        )
        assert result.exit_code == 0
        assert "Hello world." in result.output

    @patch("kagi_client.cli.KagiClient")
    def test_options_forwarding(self, mock_cls: Any) -> None:
        mock = _mock_client(proofread=_make_proofread_result())
        mock_cls.return_value = mock
        app = _import_app()
        result = runner.invoke(
            app,
            [
                "proofread",
                "hello",
                "--lang",
                "en",
                "--style",
                "academic",
                "--level",
                "aggressive",
                "--formality",
                "formal",
                "--context",
                "essay",
                "--model",
                "premium",
            ],
            env={"KAGI_SESSION": "fake"},
        )
        assert result.exit_code == 0
        mock.proofread.assert_called_once_with(
            "hello",
            source_lang="en",
            writing_style="academic",
            correction_level="aggressive",
            formality="formal",
            context="essay",
            model="premium",
        )

    @patch("kagi_client.cli.KagiClient")
    def test_statistics_display(self, mock_cls: Any) -> None:
        mock_cls.return_value = _mock_client(proofread=_make_proofread_result())
        app = _import_app()
        result = runner.invoke(
            app, ["proofread", "hello world"], env={"KAGI_SESSION": "fake"}
        )
        assert result.exit_code == 0
        assert "Word Count" in result.output or "word_count" in result.output.lower()
        assert "2" in result.output


# -- Summarize tests --


class TestSummarizeCommand:
    @patch("kagi_client.cli.KagiClient")
    def test_basic(self, mock_cls: Any) -> None:
        mock_cls.return_value = _mock_client(summarize=_make_summary_result())
        app = _import_app()
        result = runner.invoke(
            app,
            ["summarize", "https://example.com"],
            env={"KAGI_SESSION": "fake"},
        )
        assert result.exit_code == 0
        assert "takeaways" in result.output.lower() or "Key" in result.output

    @patch("kagi_client.cli.KagiClient")
    def test_type_option(self, mock_cls: Any) -> None:
        mock = _mock_client(summarize=_make_summary_result())
        mock_cls.return_value = mock
        app = _import_app()
        result = runner.invoke(
            app,
            ["summarize", "https://example.com", "--type", "summary"],
            env={"KAGI_SESSION": "fake"},
        )
        assert result.exit_code == 0
        mock.summarize.assert_called_once_with(
            "https://example.com", summary_type="summary"
        )


# -- Ask tests --


class TestAskCommand:
    @patch("kagi_client.cli.KagiClient")
    def test_basic(self, mock_cls: Any) -> None:
        mock = _mock_client()
        mock.prompt_stream = MagicMock(
            return_value=_async_iter(
                [
                    "<details><summary>Thinking</summary><p>Let me think</p></details>"
                    "<p>Hello! How can I help?</p>",
                ]
            )
        )
        mock_cls.return_value = mock
        app = _import_app()
        result = runner.invoke(app, ["ask", "hello"], env={"KAGI_SESSION": "fake"})
        assert result.exit_code == 0
        assert "Hello! How can I help?" in result.output

    @patch("kagi_client.cli.KagiClient")
    def test_stdin(self, mock_cls: Any) -> None:
        mock = _mock_client()
        mock.prompt_stream = MagicMock(
            return_value=_async_iter(
                [
                    "<details><summary>Thinking</summary><p>Hmm</p></details>"
                    "<p>Hello! How can I help?</p>",
                ]
            )
        )
        mock_cls.return_value = mock
        app = _import_app()
        result = runner.invoke(
            app, ["ask", "-"], input="hello", env={"KAGI_SESSION": "fake"}
        )
        assert result.exit_code == 0
        assert "Hello! How can I help?" in result.output

    @patch("kagi_client.cli.KagiClient")
    def test_options(self, mock_cls: Any) -> None:
        mock = _mock_client()
        mock.prompt_stream = MagicMock(
            return_value=_async_iter(["<details><p>T</p></details><p>response</p>"])
        )
        mock_cls.return_value = mock
        app = _import_app()
        result = runner.invoke(
            app,
            [
                "ask",
                "hello",
                "--model",
                "claude-3",
                "--thread",
                "t-1",
                "--no-internet",
            ],
            env={"KAGI_SESSION": "fake"},
        )
        assert result.exit_code == 0
        mock.prompt_stream.assert_called_once_with(
            "hello",
            model="claude-3",
            thread_id="t-1",
            internet_access=False,
        )

    @patch("kagi_client.cli.KagiClient")
    def test_streaming_phases(self, mock_cls: Any) -> None:
        """Thinking is shown dim, response is rendered as markdown."""
        mock = _mock_client()
        mock.prompt_stream = MagicMock(
            return_value=_async_iter(
                [
                    # Phase 1: still thinking (no </details> yet)
                    "<details><summary>Thinking</summary><p>Hmm",
                    # Phase 1 complete: thinking done
                    "<details><summary>Thinking</summary><p>Hmm</p></details>"
                    "<p>Hello</p>",
                    # Phase 2: response grows (final snapshot used for render)
                    "<details><summary>Thinking</summary><p>Hmm</p></details>"
                    "<p>Hello world</p>",
                ]
            )
        )
        mock_cls.return_value = mock
        app = _import_app()
        result = runner.invoke(app, ["ask", "hello"], env={"KAGI_SESSION": "fake"})
        assert result.exit_code == 0
        assert "Hmm" in result.output
        assert "Hello world" in result.output

    @patch("kagi_client.cli.KagiClient")
    def test_code_blocks_preserved(self, mock_cls: Any) -> None:
        """Code blocks should render properly in console output."""
        mock = _mock_client()
        mock.prompt_stream = MagicMock(
            return_value=_async_iter(
                [
                    "<details><p>T</p></details>"
                    "<p>Use this:</p>"
                    '<pre><code class="language-bash">'
                    "cat file.txt | xargs echo"
                    "</code></pre>"
                    "<p>Done.</p>",
                ]
            )
        )
        mock_cls.return_value = mock
        app = _import_app()
        result = runner.invoke(app, ["ask", "hello"], env={"KAGI_SESSION": "fake"})
        assert result.exit_code == 0
        assert "cat file.txt | xargs echo" in result.output
        assert "Use this" in result.output
        assert "Done" in result.output


# -- Search tests --


class TestSearchCommand:
    @patch("kagi_client.cli.KagiClient")
    def test_basic(self, mock_cls: Any) -> None:
        mock_cls.return_value = _mock_client(search=_make_search_result())
        app = _import_app()
        result = runner.invoke(
            app, ["search", "test query"], env={"KAGI_SESSION": "fake"}
        )
        assert result.exit_code == 0
        assert "Example Result" in result.output
        assert "https://example.com/page" in result.output
        assert "kagi.com/search" in result.output

    @patch("kagi_client.cli.KagiClient")
    def test_description_and_archive(self, mock_cls: Any) -> None:
        mock_cls.return_value = _mock_client(search=_make_search_result())
        app = _import_app()
        result = runner.invoke(
            app, ["search", "test query"], env={"KAGI_SESSION": "fake"}
        )
        assert result.exit_code == 0
        assert "A great example page" in result.output
        assert "web.archive.org" in result.output

    @patch("kagi_client.cli.KagiClient")
    def test_domain_table(self, mock_cls: Any) -> None:
        mock_cls.return_value = _mock_client(search=_make_search_result())
        app = _import_app()
        result = runner.invoke(
            app, ["search", "test query"], env={"KAGI_SESSION": "fake"}
        )
        assert result.exit_code == 0
        assert "example.com" in result.output


# -- Thinking split tests --


class TestSplitThinking:
    def test_no_thinking_block(self) -> None:
        from kagi_client.cli import _split_thinking

        assert _split_thinking("<p>Hello</p>") == ("", "")

    def test_with_thinking_block(self) -> None:
        from kagi_client.cli import _split_thinking

        thinking, response = _split_thinking(
            "<details><summary>Thinking</summary><p>Hmm</p></details><p>Answer</p>"
        )
        assert thinking == "ThinkingHmm"
        assert response == "<p>Answer</p>"

    def test_incomplete_thinking(self) -> None:
        from kagi_client.cli import _split_thinking

        assert _split_thinking("<details><p>Thinking...") == ("", "")

    def test_empty_response_after_thinking(self) -> None:
        from kagi_client.cli import _split_thinking

        thinking, response = _split_thinking("<details><p>Done</p></details>")
        assert thinking == "Done"
        assert response == ""


# -- HTML stripping tests --


class TestHTMLStripping:
    def test_simple_tags(self) -> None:
        from kagi_client.cli import strip_html

        assert strip_html("<b>bold</b> text") == "bold text"

    def test_nested_tags(self) -> None:
        from kagi_client.cli import strip_html

        assert strip_html("<div><p>nested <b>bold</b></p></div>") == "nested bold"

    def test_empty_string(self) -> None:
        from kagi_client.cli import strip_html

        assert strip_html("") == ""

    def test_plain_text(self) -> None:
        from kagi_client.cli import strip_html

        assert strip_html("no tags here") == "no tags here"


# -- HTML to Markdown tests --


class TestHTMLToMarkdown:
    def test_code_block(self) -> None:
        from kagi_client.cli import html_to_markdown

        html = '<pre><code class="language-bash">echo hello</code></pre>'
        result = html_to_markdown(html)
        assert "```bash" in result
        assert "echo hello" in result
        assert result.strip().endswith("```")

    def test_code_block_no_language(self) -> None:
        from kagi_client.cli import html_to_markdown

        html = "<pre><code>x = 1</code></pre>"
        result = html_to_markdown(html)
        assert "```" in result
        assert "x = 1" in result

    def test_paragraphs(self) -> None:
        from kagi_client.cli import html_to_markdown

        html = "<p>First paragraph</p><p>Second paragraph</p>"
        result = html_to_markdown(html)
        assert "First paragraph" in result
        assert "Second paragraph" in result
        # Paragraphs should be separated by blank line
        assert "First paragraph\n\nSecond paragraph" in result

    def test_headers(self) -> None:
        from kagi_client.cli import html_to_markdown

        html = "<h2>Title</h2><p>Content</p>"
        result = html_to_markdown(html)
        assert "## Title" in result
        assert "Content" in result

    def test_list_items(self) -> None:
        from kagi_client.cli import html_to_markdown

        html = "<ul><li>First</li><li>Second</li></ul>"
        result = html_to_markdown(html)
        assert "- First" in result
        assert "- Second" in result

    def test_mixed_content(self) -> None:
        from kagi_client.cli import html_to_markdown

        html = (
            "<p>Use this command:</p>"
            '<pre><code class="language-bash">cat file.txt | xargs echo</code></pre>'
            "<p>That will print each line.</p>"
        )
        result = html_to_markdown(html)
        assert "Use this command:" in result
        assert "```bash" in result
        assert "cat file.txt | xargs echo" in result
        assert "That will print each line." in result

    def test_plain_text(self) -> None:
        from kagi_client.cli import html_to_markdown

        assert html_to_markdown("no tags") == "no tags"

    def test_preserves_code_content(self) -> None:
        from kagi_client.cli import html_to_markdown

        html = '<pre><code class="language-python">if x > 0:\n    print(x)</code></pre>'
        result = html_to_markdown(html)
        assert "if x > 0:" in result
        assert "    print(x)" in result

    def test_bold_and_italic(self) -> None:
        from kagi_client.cli import html_to_markdown

        html = "<p>This is <strong>bold</strong> and <em>italic</em>.</p>"
        result = html_to_markdown(html)
        assert "**bold**" in result
        assert "*italic*" in result

    def test_inline_code(self) -> None:
        from kagi_client.cli import html_to_markdown

        html = "<p>Use <code>-t</code> flag.</p>"
        result = html_to_markdown(html)
        assert "`-t`" in result

    def test_no_excess_blank_lines(self) -> None:
        from kagi_client.cli import html_to_markdown

        html = "<p>One</p>\n\n<p>Two</p>\n\n<p>Three</p>"
        result = html_to_markdown(html)
        # Should not have more than 2 consecutive newlines
        assert "\n\n\n" not in result


# -- Help tests --


class TestHelp:
    def test_no_args_shows_help(self) -> None:
        app = _import_app()
        result = runner.invoke(app, [])
        assert "proofread" in result.output
        assert "summarize" in result.output
        assert "ask" in result.output
        assert "search" in result.output

    def test_help_flag(self) -> None:
        app = _import_app()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "proofread" in result.output


class TestVersion:
    @patch("kagi_client.cli.subprocess.run")
    def test_uses_git_exact_tag(self, mock_run: Any) -> None:
        mock_run.return_value = MagicMock(stdout="v1.2.3\n")
        app = _import_app()
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert result.output.strip() == "v1.2.3"

    @patch("kagi_client.cli.metadata.version")
    @patch("kagi_client.cli.subprocess.run", side_effect=OSError)
    def test_falls_back_to_package_metadata(
        self, _mock_run: Any, mock_version: Any
    ) -> None:
        mock_version.return_value = "1.2.4"
        app = _import_app()
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert result.output.strip() == "1.2.4"

    @patch("kagi_client.cli.metadata.version")
    @patch("kagi_client.cli.subprocess.run", side_effect=OSError)
    def test_unknown_when_no_git_and_no_package_metadata(
        self, _mock_run: Any, mock_version: Any
    ) -> None:
        mock_version.side_effect = importlib_metadata.PackageNotFoundError
        app = _import_app()
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert result.output.strip() == "0.0.0+unknown"


# -- Format option tests --


class TestProofreadFormats:
    @patch("kagi_client.cli.KagiClient")
    def test_json(self, mock_cls: Any) -> None:
        mock_cls.return_value = _mock_client(proofread=_make_proofread_result())
        app = _import_app()
        result = runner.invoke(
            app,
            ["proofread", "hello world", "--format", "json"],
            env={"KAGI_SESSION": "fake"},
        )
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["text"] == "Hello world."
        assert parsed["analysis"]["corrected_text"] == "Hello world."

    @patch("kagi_client.cli.KagiClient")
    def test_md(self, mock_cls: Any) -> None:
        mock_cls.return_value = _mock_client(proofread=_make_proofread_result())
        app = _import_app()
        result = runner.invoke(
            app,
            ["proofread", "hello world", "--format", "md"],
            env={"KAGI_SESSION": "fake"},
        )
        assert result.exit_code == 0
        assert "## Corrected Text" in result.output
        assert "## Writing Statistics" in result.output

    @patch("kagi_client.cli.KagiClient")
    def test_csv(self, mock_cls: Any) -> None:
        mock_cls.return_value = _mock_client(proofread=_make_proofread_result())
        app = _import_app()
        result = runner.invoke(
            app,
            ["proofread", "hello world", "--format", "csv"],
            env={"KAGI_SESSION": "fake"},
        )
        assert result.exit_code == 0
        reader = csv.reader(io.StringIO(result.output))
        header = next(reader)
        assert header == ["metric", "value"]


class TestSummarizeFormats:
    @patch("kagi_client.cli.KagiClient")
    def test_json(self, mock_cls: Any) -> None:
        mock_cls.return_value = _mock_client(summarize=_make_summary_result())
        app = _import_app()
        result = runner.invoke(
            app,
            ["summarize", "https://example.com", "--format", "json"],
            env={"KAGI_SESSION": "fake"},
        )
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["title"] == "Test Article"

    @patch("kagi_client.cli.KagiClient")
    def test_md(self, mock_cls: Any) -> None:
        mock_cls.return_value = _mock_client(summarize=_make_summary_result())
        app = _import_app()
        result = runner.invoke(
            app,
            ["summarize", "https://example.com", "--format", "md"],
            env={"KAGI_SESSION": "fake"},
        )
        assert result.exit_code == 0
        assert "# Test Article" in result.output
        assert "Key takeaways" in result.output

    @patch("kagi_client.cli.KagiClient")
    def test_csv(self, mock_cls: Any) -> None:
        mock_cls.return_value = _mock_client(summarize=_make_summary_result())
        app = _import_app()
        result = runner.invoke(
            app,
            ["summarize", "https://example.com", "--format", "csv"],
            env={"KAGI_SESSION": "fake"},
        )
        assert result.exit_code == 0
        reader = csv.reader(io.StringIO(result.output))
        header = next(reader)
        assert header == ["field", "value"]


class TestAskFormats:
    @patch("kagi_client.cli.KagiClient")
    def test_json(self, mock_cls: Any) -> None:
        mock_cls.return_value = _mock_client(prompt=_make_assistant_result())
        app = _import_app()
        result = runner.invoke(
            app,
            ["ask", "hello", "--format", "json"],
            env={"KAGI_SESSION": "fake"},
        )
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["thread"]["id"] == "thread-123"
        assert parsed["response"] == "Hello! How can I help?"

    @patch("kagi_client.cli.KagiClient")
    def test_md(self, mock_cls: Any) -> None:
        mock_cls.return_value = _mock_client(prompt=_make_assistant_result())
        app = _import_app()
        result = runner.invoke(
            app,
            ["ask", "hello", "--format", "md"],
            env={"KAGI_SESSION": "fake"},
        )
        assert result.exit_code == 0
        assert "Hello! How can I help?" in result.output

    @patch("kagi_client.cli.KagiClient")
    def test_csv(self, mock_cls: Any) -> None:
        mock_cls.return_value = _mock_client(prompt=_make_assistant_result())
        app = _import_app()
        result = runner.invoke(
            app,
            ["ask", "hello", "--format", "csv"],
            env={"KAGI_SESSION": "fake"},
        )
        assert result.exit_code == 0
        reader = csv.reader(io.StringIO(result.output))
        header = next(reader)
        assert header == ["thread_id", "message_id", "prompt", "response"]

    @patch("kagi_client.cli.KagiClient")
    def test_json_uses_prompt_not_stream(self, mock_cls: Any) -> None:
        """Non-console formats should use client.prompt(), not prompt_stream()."""
        mock = _mock_client(prompt=_make_assistant_result())
        mock_cls.return_value = mock
        app = _import_app()
        runner.invoke(
            app,
            ["ask", "hello", "--format", "json"],
            env={"KAGI_SESSION": "fake"},
        )
        mock.prompt.assert_called_once()
        mock.prompt_stream.assert_not_called()


class TestSearchFormats:
    @patch("kagi_client.cli.KagiClient")
    def test_json(self, mock_cls: Any) -> None:
        mock_cls.return_value = _mock_client(search=_make_search_result())
        app = _import_app()
        result = runner.invoke(
            app,
            ["search", "test query", "--format", "json"],
            env={"KAGI_SESSION": "fake"},
        )
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["items"][0]["title"] == "Example Result"

    @patch("kagi_client.cli.KagiClient")
    def test_md(self, mock_cls: Any) -> None:
        mock_cls.return_value = _mock_client(search=_make_search_result())
        app = _import_app()
        result = runner.invoke(
            app,
            ["search", "test query", "--format", "md"],
            env={"KAGI_SESSION": "fake"},
        )
        assert result.exit_code == 0
        assert "[Example Result](https://example.com/page)" in result.output

    @patch("kagi_client.cli.KagiClient")
    def test_csv(self, mock_cls: Any) -> None:
        mock_cls.return_value = _mock_client(search=_make_search_result())
        app = _import_app()
        result = runner.invoke(
            app,
            ["search", "test query", "--format", "csv"],
            env={"KAGI_SESSION": "fake"},
        )
        assert result.exit_code == 0
        reader = csv.reader(io.StringIO(result.output))
        header = next(reader)
        assert header == ["title", "url", "description", "archive_url", "date"]
        row = next(reader)
        assert row[0] == "Example Result"

    @patch("kagi_client.cli.KagiClient")
    def test_short_flag(self, mock_cls: Any) -> None:
        """The -F short flag should work."""
        mock_cls.return_value = _mock_client(search=_make_search_result())
        app = _import_app()
        result = runner.invoke(
            app,
            ["search", "test query", "-F", "json"],
            env={"KAGI_SESSION": "fake"},
        )
        assert result.exit_code == 0
        json.loads(result.output)  # should be valid JSON
