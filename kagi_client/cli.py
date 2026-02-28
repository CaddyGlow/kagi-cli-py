from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from html.parser import HTMLParser
from importlib import metadata
from typing import Annotated

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from kagi_client.client import KagiClient
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

app = typer.Typer(
    name="kagi",
    help="CLI for Kagi API services.",
    invoke_without_command=True,
    no_args_is_help=True,
)
console = Console(force_terminal=sys.stdout.isatty())
err_console = Console(stderr=True)


# -- HTML stripping --


class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts)


def strip_html(html: str) -> str:
    stripper = _HTMLStripper()
    stripper.feed(html)
    return stripper.get_text()


class _HTMLToMarkdown(HTMLParser):
    """Convert HTML to Markdown, preserving code blocks and structure."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._in_pre = False
        self._in_code_block = False
        self._block_just_closed = False

    def _ensure_blank_line(self) -> None:
        """Add blank line separator between block elements if needed."""
        if self._parts and not self._parts[-1].endswith("\n\n"):
            if self._parts[-1].endswith("\n"):
                self._parts.append("\n")
            else:
                self._parts.append("\n\n")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._block_just_closed = False
        if tag == "pre":
            self._in_pre = True
            self._ensure_blank_line()
        elif tag == "code" and self._in_pre:
            self._in_code_block = True
            lang = ""
            for name, value in attrs:
                if name == "class" and value and value.startswith("language-"):
                    lang = value[9:]
            self._parts.append(f"```{lang}\n")
        elif tag == "p" and not self._in_pre:
            self._ensure_blank_line()
        elif tag == "br":
            self._parts.append("\n")
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._ensure_blank_line()
            level = int(tag[1])
            self._parts.append("#" * level + " ")
        elif tag == "li":
            if self._parts and not self._parts[-1].endswith("\n"):
                self._parts.append("\n")
            self._parts.append("- ")
        elif tag == "strong" or tag == "b":
            self._parts.append("**")
        elif tag == "em" or tag == "i":
            self._parts.append("*")
        elif tag == "code" and not self._in_pre:
            self._parts.append("`")

    def handle_endtag(self, tag: str) -> None:
        if tag == "code" and self._in_code_block:
            self._in_code_block = False
            # Ensure newline before closing fence
            if self._parts and not self._parts[-1].endswith("\n"):
                self._parts.append("\n")
            self._parts.append("```\n")
            self._block_just_closed = True
        elif tag == "pre":
            self._in_pre = False
        elif tag in ("strong", "b"):
            self._parts.append("**")
        elif tag in ("em", "i"):
            self._parts.append("*")
        elif tag == "code" and not self._in_pre:
            self._parts.append("`")
        elif tag in ("p", "h1", "h2", "h3", "h4", "h5", "h6"):
            self._block_just_closed = True

    def handle_data(self, data: str) -> None:
        if self._in_code_block:
            # Preserve whitespace exactly inside code blocks
            self._parts.append(data)
        elif self._block_just_closed and not data.strip():
            # Skip whitespace-only text between block elements
            pass
        else:
            self._block_just_closed = False
            self._parts.append(data)

    def get_markdown(self) -> str:
        return "".join(self._parts).strip()


def html_to_markdown(html: str) -> str:
    """Convert HTML to Markdown, preserving code blocks and structure."""
    converter = _HTMLToMarkdown()
    converter.feed(html)
    return converter.get_markdown()


def _split_thinking(html: str) -> tuple[str, str]:
    """Split HTML on the </details> boundary.

    Returns (thinking_text, response_html) where thinking_text is the stripped
    text inside the <details> block and response_html is everything after
    </details>.  If no </details> is found, returns ("", "").
    """
    marker = "</details>"
    idx = html.find(marker)
    if idx == -1:
        return ("", "")
    thinking_html = html[:idx]
    response_html = html[idx + len(marker) :]
    return (strip_html(thinking_html), response_html)


# -- Helpers --


def _resolve_version() -> str:
    # Prefer the checked-out git tag so `kagi --version` follows releases.
    git_commands = [
        ["git", "describe", "--tags", "--exact-match"],
        ["git", "describe", "--tags", "--always", "--dirty"],
    ]
    for command in git_commands:
        try:
            result = subprocess.run(
                command,
                check=True,
                text=True,
                capture_output=True,
            )
            version = result.stdout.strip()
            if version:
                return version
        except (subprocess.SubprocessError, OSError):
            continue

    try:
        return metadata.version("kagi-cli")
    except metadata.PackageNotFoundError:
        return "0.0.0+unknown"


def _version_callback(value: bool) -> None:
    if not value:
        return
    typer.echo(_resolve_version())
    raise typer.Exit(code=0)


def _get_session() -> str:
    session = os.environ.get("KAGI_SESSION", "")
    if not session:
        err_console.print("Error: KAGI_SESSION environment variable is required.")
        raise typer.Exit(code=1)
    return session


def _read_text(text: str) -> str:
    """Read text from argument or stdin if '-'."""
    if text == "-":
        return sys.stdin.read()
    return text


FormatOption = Annotated[
    OutputFormat,
    typer.Option("--format", "-F", help="Output format: console, json, md, csv"),
]


# -- Commands --


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=_version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = False,
) -> None:
    """Kagi CLI."""
    _ = version


@app.command()
def proofread(
    text: Annotated[str, typer.Argument(help="Text to proofread, or '-' for stdin")],
    lang: Annotated[str, typer.Option("--lang", "-l", help="Source language")] = "auto",
    style: Annotated[
        str, typer.Option("--style", "-s", help="Writing style")
    ] = "general",
    level: Annotated[str, typer.Option(help="Correction level")] = "standard",
    formality: Annotated[
        str, typer.Option("--formality", "-f", help="Formality level")
    ] = "default",
    context: Annotated[
        str, typer.Option("--context", "-c", help="Additional context")
    ] = "",
    model: Annotated[
        str, typer.Option("--model", "-m", help="Model selection")
    ] = "standard",
    fmt: FormatOption = OutputFormat.console,
) -> None:
    """Proofread text using Kagi."""
    session = _get_session()
    body = _read_text(text)

    async def _run() -> None:
        async with KagiClient(session) as client:
            result = await client.proofread(
                body,
                source_lang=lang,
                writing_style=style,
                correction_level=level,
                formality=formality,
                context=context,
                model=model,
            )

        if fmt == OutputFormat.json:
            print(proofread_json(result))
        elif fmt == OutputFormat.md:
            print(proofread_md(result), end="")
        elif fmt == OutputFormat.csv:
            print(proofread_csv(result), end="")
        elif result.analysis:
            console.print(Panel(result.analysis.corrected_text, title="Corrected Text"))
            console.print()
            console.print(
                f"[bold]Corrections:[/bold] {result.analysis.corrections_summary}"
            )
            console.print()

            tone = result.analysis.tone_analysis
            console.print(
                f"[bold]Tone:[/bold] {tone.overall_tone} -- {tone.description}"
            )
            console.print()

            stats = result.analysis.writing_statistics
            table = Table(title="Writing Statistics")
            table.add_column("Metric", style="bold")
            table.add_column("Value")
            table.add_row("Word Count", str(stats.word_count))
            table.add_row("Character Count", str(stats.character_count))
            table.add_row("Sentences", str(stats.sentence_count))
            table.add_row("Paragraphs", str(stats.paragraph_count))
            table.add_row(
                "Avg Words/Sentence", f"{stats.average_words_per_sentence:.1f}"
            )
            table.add_row("Vocabulary Diversity", f"{stats.vocabulary_diversity:.2f}")
            table.add_row("Reading Level", stats.reading_level)
            table.add_row("Readability Score", f"{stats.readability_score:.1f}")
            table.add_row("Reading Time", f"{stats.reading_time_minutes:.1f} min")
            console.print(table)
        else:
            console.print(result.text)

    asyncio.run(_run())


@app.command()
def summarize(
    url: Annotated[str, typer.Argument(help="URL to summarize")],
    summary_type: Annotated[
        str, typer.Option("--type", "-t", help="Summary type: takeaway or summary")
    ] = "takeaway",
    fmt: FormatOption = OutputFormat.console,
) -> None:
    """Summarize a URL using Kagi."""
    session = _get_session()

    async def _run() -> None:
        async with KagiClient(session) as client:
            result = await client.summarize(url, summary_type=summary_type)

        if fmt == OutputFormat.json:
            print(summarize_json(result))
        elif fmt == OutputFormat.md:
            print(summarize_md(result), end="")
        elif fmt == OutputFormat.csv:
            print(summarize_csv(result), end="")
        else:
            console.print(f"[bold]{result.title}[/bold]")
            console.print()
            console.print(Panel(Markdown(result.markdown), title="Summary"))
            console.print()

            meta = result.response_metadata
            ws = result.word_stats
            table = Table(title="Metadata")
            table.add_column("Field", style="bold")
            table.add_column("Value")
            table.add_row("Model", meta.model)
            if meta.speed is not None:
                table.add_row("Speed", f"{meta.speed:.1f} tok/s")
            table.add_row("Tokens", str(meta.tokens))
            table.add_row("Cost", f"${meta.cost:.4f}")
            if result.elapsed_seconds is not None:
                table.add_row("Elapsed", f"{result.elapsed_seconds:.1f}s")
            table.add_row("Source Words", str(ws.n_words))
            table.add_row("Source Pages", str(ws.n_pages))
            table.add_row("Time Saved", f"{ws.time_saved}s")
            console.print(table)

    asyncio.run(_run())


@app.command()
def ask(
    text: Annotated[str, typer.Argument(help="Prompt text, or '-' for stdin")],
    model: Annotated[
        str, typer.Option("--model", "-m", help="Model to use")
    ] = "gpt-5-mini",
    thread: Annotated[
        str | None, typer.Option("--thread", "-t", help="Thread ID to continue")
    ] = None,
    no_internet: Annotated[
        bool, typer.Option("--no-internet", help="Disable internet access")
    ] = False,
    fmt: FormatOption = OutputFormat.console,
) -> None:
    """Ask Kagi Assistant a question."""
    session = _get_session()
    body = _read_text(text)

    async def _run() -> None:
        async with KagiClient(session) as client:
            if fmt != OutputFormat.console:
                result = await client.prompt(
                    body,
                    model=model,
                    thread_id=thread,
                    internet_access=not no_internet,
                )
                if fmt == OutputFormat.json:
                    print(ask_json(result))
                elif fmt == OutputFormat.md:
                    print(ask_md(result), end="")
                elif fmt == OutputFormat.csv:
                    print(ask_csv(result), end="")
                return

            thinking_text_out = ""
            last_response_html = ""
            thinking_done = False
            async for snapshot in client.prompt_stream(
                body,
                model=model,
                thread_id=thread,
                internet_access=not no_internet,
            ):
                if not thinking_done:
                    thinking_text, response_html = _split_thinking(snapshot)
                    if not thinking_text:
                        continue
                    thinking_done = True
                    thinking_text_out = thinking_text
                    last_response_html = response_html
                else:
                    _, response_html = _split_thinking(snapshot)
                    last_response_html = response_html

        if thinking_text_out.strip():
            console.print(f"[dim]{thinking_text_out.strip()}[/dim]")
            console.print()
        if last_response_html:
            md = html_to_markdown(last_response_html)
            console.print(Markdown(md))

    asyncio.run(_run())


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Search query")],
    all_pages: Annotated[
        bool, typer.Option("--all", "-a", help="Fetch all pages")
    ] = False,
    fmt: FormatOption = OutputFormat.console,
) -> None:
    """Search using Kagi."""
    session = _get_session()

    async def _run() -> None:
        async with KagiClient(session) as client:
            if all_pages:
                results = []
                async for page in client.search_all(query):
                    results.append(page)
            else:
                results = [await client.search(query)]

        if fmt == OutputFormat.json:
            print(search_json(results))
        elif fmt == OutputFormat.md:
            print(search_md(results), end="")
        elif fmt == OutputFormat.csv:
            print(search_csv(results), end="")
        else:
            for result in results:
                if result.items:
                    for i, item in enumerate(result.items, 1):
                        console.print(f"[bold]{i}. {item.title}[/bold]")
                        console.print(f"   {item.url}")
                        if item.web_archive_url:
                            console.print(
                                f"   [dim]Archive: {item.web_archive_url}[/dim]"
                            )
                        if item.description:
                            console.print(f"   {item.description}")
                        console.print()
                else:
                    plain_text = strip_html(result.search_html)
                    console.print(Panel(plain_text, title="Search Results"))
                    console.print()

                console.print(f"[bold]Share:[/bold] {result.info.share_url}")

                if result.domain_infos:
                    console.print()
                    table = Table(title="Domains")
                    table.add_column("Domain", style="bold")
                    table.add_column("Speed")
                    table.add_column("Trackers")
                    table.add_column("Secure")
                    table.add_column("Registered")
                    for d in result.domain_infos:
                        table.add_row(
                            d.domain,
                            d.website_speed or "",
                            str(d.trackers) if d.trackers is not None else "",
                            "Yes"
                            if d.domain_secure
                            else "No"
                            if d.domain_secure is not None
                            else "",
                            d.registration_date or "",
                        )
                    console.print(table)

    asyncio.run(_run())
