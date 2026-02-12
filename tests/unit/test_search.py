from __future__ import annotations

import json

import httpx
import pytest
import respx

from kagi_client.auth import KagiAuth
from kagi_client.errors import APIError
from kagi_client.models import SearchResult
from kagi_client.search import SearchClient, _parse_search_items
from tests.conftest import make_jwt_token

SEARCH_URL = "https://kagi.com/socket/search"

DOMAIN_INFO_DATA = json.dumps(
    {
        "too_many_rules": False,
        "data": [
            {
                "domain": "example.com",
                "rule_type": None,
                "description": "Example site",
                "favicon_url": "https://p.kagi.com/proxy/favicons?c=abc",
                "domain_secure": True,
                "trackers": 5,
                "scam_list_site": None,
                "registration_date": "1995-08-14",
                "language": None,
                "website_speed": "Fast",
            }
        ],
    }
)

SSE_RESPONSE = (
    "hi\n"
    "\n"
    "id: 1\n"
    'data: [{"tag":"top_content","payload":"<div>10 results</div>",'
    '"sent_at":1770905073337,"kagi_version":"v1"}]\n'
    "\n"
    "id: 2\n"
    'data: [{"tag":"search.info","payload":{"share_url":"https://kagi.com/search?q=test",'
    '"curr_batch":1,"curr_piece":1,"next_batch":2,"next_piece":1},'
    '"sent_at":1770905073337,"kagi_version":"v1"}]\n'
    "\n"
    "id: 3\n"
    'data: [{"tag":"search","payload":{"content":"<div class=\\"result\\">Result 1</div>"},'
    '"sent_at":1770905073337,"kagi_version":"v1"}]\n'
    "\n"
    "id: 4\n"
    f'data: [{{"tag":"domain_info","payload":{json.dumps(DOMAIN_INFO_DATA)},'
    '"sent_at":1770905073337,"kagi_version":"v1"}]\n'
    "\n"
    "id: CLOSE\n"
    "data: \n"
    "\n"
)

SSE_RESPONSE_PAGE2 = (
    "hi\n"
    "\n"
    "id: 1\n"
    'data: [{"tag":"search.info","payload":{"share_url":"https://kagi.com/search?q=test",'
    '"curr_batch":2,"curr_piece":1,"next_batch":-1,"next_piece":1},'
    '"sent_at":1770905073337,"kagi_version":"v1"}]\n'
    "\n"
    "id: 2\n"
    'data: [{"tag":"search","payload":{"content":"<div>Result 2</div>"},'
    '"sent_at":1770905073337,"kagi_version":"v1"}]\n'
    "\n"
    "id: CLOSE\n"
    "data: \n"
    "\n"
)


def _make_auth() -> KagiAuth:
    auth = KagiAuth(kagi_session="fake")
    auth._token = make_jwt_token()
    return auth


class TestSearchClient:
    @respx.mock
    async def test_search_returns_result(self) -> None:
        respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, text=SSE_RESPONSE))
        auth = _make_auth()
        client = SearchClient(auth=auth)
        result = await client.search("test")
        assert isinstance(result, SearchResult)
        assert result.info.curr_batch == 1
        assert result.info.next_batch == 2
        assert "Result 1" in result.search_html
        assert len(result.domain_infos) == 1
        assert result.domain_infos[0].domain == "example.com"
        assert result.domain_infos[0].trackers == 5

    @respx.mock
    async def test_search_raises_on_http_error(self) -> None:
        respx.get(SEARCH_URL).mock(
            return_value=httpx.Response(429, text="Rate limited")
        )
        auth = _make_auth()
        client = SearchClient(auth=auth)
        with pytest.raises(APIError) as exc_info:
            await client.search("test")
        assert exc_info.value.status_code == 429

    @respx.mock
    async def test_search_all_pagination(self) -> None:
        route = respx.get(SEARCH_URL)
        route.side_effect = [
            httpx.Response(200, text=SSE_RESPONSE),
            httpx.Response(200, text=SSE_RESPONSE_PAGE2),
        ]
        auth = _make_auth()
        client = SearchClient(auth=auth)
        results = []
        async for result in client.search_all("test"):
            results.append(result)
        assert len(results) == 2
        assert results[0].info.curr_batch == 1
        assert results[1].info.curr_batch == 2
        assert results[1].info.next_batch == -1


RESULT_HTML = (
    '<div class="_0_SRI search-result">'
    '<div class="_0_TITLE __sri-title">'
    '<h3 class="__sri-title-box">'
    '<a class="__sri_title_link _0_URL" href="https://example.com/page"'
    ' title="Example Page" target="_blank">Example Page</a></h3>'
    '<div class="__sri_more_menu">'
    '<a href="https://web.archive.org/web/20260212/https://example.com/page"'
    ' title="Open Web Archive">Open page in Web Archive</a>'
    "</div></div>"
    '<div class="__sri-body"><div class="_0_DESC __sri-desc"><div>'
    '<span class="__sri-time">Feb 12, 2026</span>'
    "A test description.</div></div></div></div>"
    '<div class="_0_SRI search-result">'
    '<div class="_0_TITLE __sri-title">'
    '<h3 class="__sri-title-box">'
    '<a class="__sri_title_link _0_URL" href="https://other.com"'
    ' target="_blank">Other Result</a></h3>'
    "</div>"
    '<div class="__sri-body"><div class="_0_DESC __sri-desc"><div>'
    "No date here.</div></div></div></div>"
)


class TestParseSearchItems:
    def test_extracts_items(self) -> None:
        items = _parse_search_items(RESULT_HTML)
        assert len(items) == 2

    def test_first_item_fields(self) -> None:
        items = _parse_search_items(RESULT_HTML)
        first = items[0]
        assert first.title == "Example Page"
        assert first.url == "https://example.com/page"
        assert first.description == "Feb 12, 2026A test description."
        assert first.web_archive_url == (
            "https://web.archive.org/web/20260212/https://example.com/page"
        )
        assert first.date == "Feb 12, 2026"

    def test_second_item_no_archive(self) -> None:
        items = _parse_search_items(RESULT_HTML)
        second = items[1]
        assert second.title == "Other Result"
        assert second.url == "https://other.com"
        assert second.web_archive_url is None
        assert second.date is None

    def test_empty_html(self) -> None:
        assert _parse_search_items("") == []

    def test_no_results_html(self) -> None:
        assert _parse_search_items("<div>no results</div>") == []
