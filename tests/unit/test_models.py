from __future__ import annotations

from kagi_client.models import (
    AssistantMessage,
    AssistantResult,
    AssistantThread,
    AuthResponse,
    DetectedLanguage,
    DomainInfo,
    ProofreadAnalysis,
    ProofreadResult,
    ResponseMetadata,
    SearchInfo,
    SearchResult,
    SummaryResult,
    SummaryUpdate,
    TokenPayload,
    ToneAnalysis,
    WordStats,
    WritingStatistics,
)


class TestAuthModels:
    def test_auth_response(self) -> None:
        resp = AuthResponse(
            token="abc",
            id="123",
            logged_in=True,
            subscription=True,
            expires_at="2025-09-29T14:52:13.000Z",
            account_type="professional",
        )
        assert resp.token == "abc"
        assert resp.id == "123"
        assert resp.logged_in is True
        assert resp.subscription is True
        assert resp.account_type == "professional"

    def test_token_payload(self) -> None:
        payload = TokenPayload(
            subscription=True,
            id="489634",
            logged_in=True,
            account_type="professional",
            iat=1759151533,
            exp=1759157533,
        )
        assert payload.id == "489634"
        assert payload.iat == 1759151533
        assert payload.exp == 1759157533


class TestProofreadModels:
    def test_detected_language(self) -> None:
        lang = DetectedLanguage(iso="en", label="English")
        assert lang.iso == "en"
        assert lang.label == "English"

    def test_tone_analysis(self) -> None:
        tone = ToneAnalysis(overall_tone="neutral", description="No tone detected")
        assert tone.overall_tone == "neutral"

    def test_writing_statistics(self) -> None:
        stats = WritingStatistics(
            word_count=10,
            character_count=50,
            character_count_no_spaces=40,
            paragraph_count=1,
            sentence_count=2,
            average_words_per_sentence=5.0,
            average_characters_per_word=4.0,
            vocabulary_diversity=0.8,
            reading_time_minutes=0.1,
            reading_level="elementary",
            readability_score=20.0,
        )
        assert stats.word_count == 10
        assert stats.reading_level == "elementary"

    def test_proofread_analysis(self) -> None:
        analysis = ProofreadAnalysis(
            corrected_text="hello",
            changes=[],
            corrections_summary="No corrections.",
            tone_analysis=ToneAnalysis(overall_tone="neutral", description="Neutral"),
            writing_statistics=WritingStatistics(
                word_count=1,
                character_count=5,
                character_count_no_spaces=5,
                paragraph_count=1,
                sentence_count=1,
                average_words_per_sentence=1.0,
                average_characters_per_word=5.0,
                vocabulary_diversity=1.0,
                reading_time_minutes=0.1,
                reading_level="elementary",
                readability_score=20.0,
            ),
        )
        assert analysis.corrected_text == "hello"
        assert analysis.tone_analysis.overall_tone == "neutral"

    def test_proofread_result(self) -> None:
        result = ProofreadResult(
            detected_language=DetectedLanguage(iso="en", label="English"),
            text="hello",
            analysis=ProofreadAnalysis(
                corrected_text="hello",
                changes=[],
                corrections_summary="No corrections.",
                tone_analysis=ToneAnalysis(
                    overall_tone="neutral", description="Neutral"
                ),
                writing_statistics=WritingStatistics(
                    word_count=1,
                    character_count=5,
                    character_count_no_spaces=5,
                    paragraph_count=1,
                    sentence_count=1,
                    average_words_per_sentence=1.0,
                    average_characters_per_word=5.0,
                    vocabulary_diversity=1.0,
                    reading_time_minutes=0.1,
                    reading_level="elementary",
                    readability_score=20.0,
                ),
            ),
        )
        assert result.detected_language.iso == "en"
        assert result.text == "hello"


class TestSummarizerModels:
    def test_word_stats(self) -> None:
        ws = WordStats(n_tokens=100, n_words=80, n_pages=2, time_saved=5, length=None)
        assert ws.n_tokens == 100

    def test_response_metadata(self) -> None:
        meta = ResponseMetadata(
            speed=77.0,
            tokens=4154,
            total_time_second=12.12,
            model="Mistral Small",
            version="mistral-small-latest",
            cost=0.00048,
        )
        assert meta.model == "Mistral Small"

    def test_summary_update(self) -> None:
        update = SummaryUpdate(
            output_text="<p>Title</p>",
            status="generating",
            word_stats=WordStats(
                n_tokens=100, n_words=80, n_pages=2, time_saved=5, length=None
            ),
            tokens=100,
            type="update",
        )
        assert update.status == "generating"

    def test_summary_result(self) -> None:
        result = SummaryResult(
            output_text="<p>Title</p>",
            markdown="Title",
            status="completed",
            word_stats=WordStats(
                n_tokens=100, n_words=80, n_pages=2, time_saved=5, length=None
            ),
            response_metadata=ResponseMetadata(
                speed=77.0,
                tokens=4154,
                total_time_second=12.12,
                model="Mistral Small",
                version="mistral-small-latest",
                cost=0.00048,
            ),
            elapsed_seconds=12.1,
            title="Test Title",
        )
        assert result.title == "Test Title"
        assert result.markdown == "Title"


class TestAssistantModels:
    def test_assistant_thread(self) -> None:
        thread = AssistantThread(
            id="abc-123",
            title="Test Thread",
            created_at="2025-09-30T09:47:23Z",
            expires_at="2025-09-30T10:47:23Z",
            saved=False,
            shared=False,
        )
        assert thread.id == "abc-123"
        assert thread.title == "Test Thread"

    def test_assistant_message(self) -> None:
        msg = AssistantMessage(
            id="msg-1",
            created_at="2025-09-30T09:47:23Z",
            state="done",
            prompt="Hello",
            reply="<p>Hi there</p>",
            md="Hi there",
        )
        assert msg.state == "done"
        assert msg.reply == "<p>Hi there</p>"

    def test_assistant_result(self) -> None:
        result = AssistantResult(
            thread=AssistantThread(
                id="abc",
                title="Test",
                created_at="2025-09-30T09:47:23Z",
                expires_at="2025-09-30T10:47:23Z",
                saved=False,
                shared=False,
            ),
            message=AssistantMessage(
                id="msg-1",
                created_at="2025-09-30T09:47:23Z",
                state="done",
                prompt="Hello",
                reply="<p>Hi</p>",
                md="Hi",
            ),
        )
        assert result.thread.id == "abc"
        assert result.message.md == "Hi"


class TestSearchModels:
    def test_search_info(self) -> None:
        info = SearchInfo(
            share_url="https://kagi.com/search?q=test",
            curr_batch=1,
            curr_piece=1,
            next_batch=2,
            next_piece=1,
        )
        assert info.next_batch == 2

    def test_domain_info(self) -> None:
        di = DomainInfo(
            domain="example.com",
            favicon_url="https://p.kagi.com/proxy/favicons?c=...",
            domain_secure=True,
            trackers=5,
            registration_date="1999-06-25",
            website_speed="Fast",
        )
        assert di.domain == "example.com"
        assert di.trackers == 5

    def test_search_result(self) -> None:
        result = SearchResult(
            search_html="<div>results</div>",
            info=SearchInfo(
                share_url="https://kagi.com/search?q=test",
                curr_batch=1,
                curr_piece=1,
                next_batch=2,
                next_piece=1,
            ),
            domain_infos=[
                DomainInfo(
                    domain="example.com",
                    favicon_url="https://p.kagi.com/proxy/favicons?c=...",
                    domain_secure=True,
                    trackers=5,
                    registration_date="1999-06-25",
                    website_speed="Fast",
                )
            ],
        )
        assert result.info.curr_batch == 1
        assert len(result.domain_infos) == 1
