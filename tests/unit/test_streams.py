from __future__ import annotations


from kagi_client.streams import (
    KagiStreamLine,
    SSEEvent,
    parse_kagi_stream_lines,
    parse_sse_events,
)


class TestParseSSEEvents:
    def test_basic_sse(self) -> None:
        text = (
            "event: message\n"
            'data: {"detected_language":{"iso":"en","label":"English"}}\n'
            "\n"
            "event: message\n"
            'data: {"done":true}\n'
            "\n"
        )
        events = parse_sse_events(text)
        assert len(events) == 2
        assert events[0].event == "message"
        assert events[0].data == '{"detected_language":{"iso":"en","label":"English"}}'
        assert events[1].data == '{"done":true}'

    def test_data_only_events(self) -> None:
        text = 'data: {"foo":"bar"}\n\ndata: {"baz":1}\n\n'
        events = parse_sse_events(text)
        assert len(events) == 2
        assert events[0].event is None
        assert events[0].data == '{"foo":"bar"}'

    def test_multiline_data(self) -> None:
        text = "data: line1\ndata: line2\n\n"
        events = parse_sse_events(text)
        assert len(events) == 1
        assert events[0].data == "line1\nline2"

    def test_id_field(self) -> None:
        text = "id: 42\ndata: hello\n\n"
        events = parse_sse_events(text)
        assert events[0].id == "42"

    def test_empty_input(self) -> None:
        events = parse_sse_events("")
        assert events == []

    def test_ignores_comments(self) -> None:
        text = ": comment\ndata: real\n\n"
        events = parse_sse_events(text)
        assert len(events) == 1
        assert events[0].data == "real"

    def test_ignores_bare_lines(self) -> None:
        text = "hi\ndata: real\n\n"
        events = parse_sse_events(text)
        assert len(events) == 1
        assert events[0].data == "real"

    def test_close_id(self) -> None:
        text = "id: CLOSE\ndata: end\n\n"
        events = parse_sse_events(text)
        assert events[0].id == "CLOSE"


class TestParseKagiStreamLines:
    def test_basic_kagi_lines(self) -> None:
        text = (
            'hi:{"v":"202509261613"}\n'
            'thread.json:{"id":"abc","title":"Test"}\n'
            'tokens.json:{"text":"hello","id":"msg-1"}\n'
        )
        lines = parse_kagi_stream_lines(text)
        assert len(lines) == 3
        assert lines[0].tag == "hi"
        assert lines[0].payload == '{"v":"202509261613"}'
        assert lines[1].tag == "thread.json"
        assert lines[2].tag == "tokens.json"

    def test_html_payload(self) -> None:
        text = "thread_list.html:\n  <div>content</div>\n"
        lines = parse_kagi_stream_lines(text)
        assert len(lines) == 1
        assert lines[0].tag == "thread_list.html"
        assert "<div>content</div>" in lines[0].payload

    def test_update_final_lines(self) -> None:
        text = (
            'update:{"output_text":"<p>Title</p>","tokens":100,"type":"update"}\n'
            'final:{"output_text":"<p>Title</p>","tokens":200,"type":"final"}\n'
        )
        lines = parse_kagi_stream_lines(text)
        assert len(lines) == 2
        assert lines[0].tag == "update"
        assert lines[1].tag == "final"

    def test_empty_input(self) -> None:
        lines = parse_kagi_stream_lines("")
        assert lines == []

    def test_blank_lines_ignored(self) -> None:
        text = 'update:{"a":1}\n\nfinal:{"b":2}\n'
        lines = parse_kagi_stream_lines(text)
        assert len(lines) == 2

    def test_sse_event_dataclass(self) -> None:
        e = SSEEvent(event="message", data="test", id=None)
        assert e.event == "message"
        assert e.data == "test"
        assert e.id is None

    def test_kagi_stream_line_dataclass(self) -> None:
        line = KagiStreamLine(tag="update", payload='{"x":1}')
        assert line.tag == "update"
        assert line.payload == '{"x":1}'

    def test_multiline_html_payload(self) -> None:
        text = (
            "thread_list.html:\n"
            '  <div class="hide-if-no-threads">\n'
            '    <div class="thread-list-header">Today</div>\n'
            "  </div>\n"
            'tokens.json:{"text":"hi","id":"1"}\n'
        )
        lines = parse_kagi_stream_lines(text)
        assert len(lines) == 2
        assert lines[0].tag == "thread_list.html"
        assert "thread-list-header" in lines[0].payload
        assert lines[1].tag == "tokens.json"
