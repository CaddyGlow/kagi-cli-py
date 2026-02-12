from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# -- Auth --


@dataclass
class AuthResponse:
    token: str
    id: str
    logged_in: bool
    subscription: bool
    expires_at: str
    account_type: str


@dataclass
class TokenPayload:
    subscription: bool
    id: str
    logged_in: bool
    account_type: str
    iat: int
    exp: int


# -- Proofread --


@dataclass
class DetectedLanguage:
    iso: str
    label: str


@dataclass
class ToneAnalysis:
    overall_tone: str
    description: str


@dataclass
class WritingStatistics:
    word_count: int
    character_count: int
    character_count_no_spaces: int
    paragraph_count: int
    sentence_count: int
    average_words_per_sentence: float
    average_characters_per_word: float
    vocabulary_diversity: float
    reading_time_minutes: float
    reading_level: str
    readability_score: float


@dataclass
class ProofreadAnalysis:
    corrected_text: str
    changes: list[dict[str, Any]]
    corrections_summary: str
    tone_analysis: ToneAnalysis
    writing_statistics: WritingStatistics


@dataclass
class ProofreadResult:
    detected_language: DetectedLanguage | None
    text: str
    analysis: ProofreadAnalysis | None


# -- Summarizer --


@dataclass
class WordStats:
    n_tokens: int
    n_words: int
    n_pages: int
    time_saved: int
    length: int | None


@dataclass
class ResponseMetadata:
    speed: float | None
    tokens: int
    total_time_second: float
    model: str
    version: str
    cost: float


@dataclass
class SummaryUpdate:
    output_text: str
    status: str
    word_stats: WordStats
    tokens: int
    type: str


@dataclass
class SummaryResult:
    output_text: str
    markdown: str
    status: str
    word_stats: WordStats
    response_metadata: ResponseMetadata
    elapsed_seconds: float | None
    title: str


# -- Assistant --


@dataclass
class AssistantThread:
    id: str
    title: str
    created_at: str
    expires_at: str
    saved: bool
    shared: bool


@dataclass
class AssistantMessage:
    id: str
    created_at: str
    state: str
    prompt: str
    reply: str | None
    md: str | None


@dataclass
class AssistantResult:
    thread: AssistantThread
    message: AssistantMessage


# -- Search --


@dataclass
class SearchInfo:
    share_url: str
    curr_batch: int
    curr_piece: int
    next_batch: int
    next_piece: int


@dataclass
class DomainInfo:
    domain: str
    favicon_url: str | None
    domain_secure: bool | None = None
    trackers: int | None = None
    registration_date: str | None = None
    website_speed: str | None = None
    rule_type: str | None = None
    description: str | None = None


@dataclass
class SearchItem:
    title: str
    url: str
    description: str
    web_archive_url: str | None = None
    date: str | None = None


@dataclass
class SearchResult:
    search_html: str
    info: SearchInfo
    items: list[SearchItem] = field(default_factory=list)
    domain_infos: list[DomainInfo] = field(default_factory=list)
