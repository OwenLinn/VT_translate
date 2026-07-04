"""Local Agreement state for low-latency streaming subtitles."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from yt_live_translator.core.models import SourceLanguage


FINAL_PUNCTUATION = set(".?!。！？")


@dataclass(frozen=True)
class LocalAgreementConfig:
    source_language: SourceLanguage = "auto"
    agreement_n: int = 2
    min_commit_sec: float = 1.2
    max_commit_sec: float = 3.0
    max_unconfirmed_sec: float = 4.0
    min_commit_tokens: int = 5
    enable_partial_subtitle: bool = True
    enable_final_revision: bool = True
    partial_min_words_en: int = 6
    partial_min_chars_ja: int = 10
    partial_interval_sec: float = 1.5


@dataclass(frozen=True)
class AgreementUpdate:
    confirmed_delta: str
    unconfirmed_tail: str
    partial_text: str
    final_text: str
    should_translate_partial: bool
    should_finalize: bool
    confirmed_text: str


@dataclass
class LocalAgreement:
    config: LocalAgreementConfig
    confirmed_text: str = ""
    _hypotheses: list[str] = field(default_factory=list)
    _pending_since_sec: float | None = None
    _sentence_started_sec: float | None = None
    _last_partial_text: str = ""
    _last_partial_sec: float | None = None

    def update(
        self,
        hypothesis: str,
        *,
        now_sec: float,
        confirmed_text: str | None = None,
        silence_final: bool = False,
    ) -> AgreementUpdate:
        if self.config.agreement_n <= 0:
            raise ValueError("agreement_n must be greater than 0")
        if confirmed_text is not None:
            self.confirmed_text = confirmed_text.strip()

        clean_hypothesis = hypothesis.strip()
        if self._sentence_started_sec is None and clean_hypothesis:
            self._sentence_started_sec = now_sec
        self._hypotheses.append(clean_hypothesis)
        self._hypotheses = self._hypotheses[-self.config.agreement_n :]

        common_prefix = self._common_prefix(self._hypotheses)
        candidate_delta = _remove_confirmed_prefix(
            common_prefix,
            self.confirmed_text,
            self.config.source_language,
        )
        if candidate_delta and self._pending_since_sec is None:
            self._pending_since_sec = now_sec

        commit_due_to_size = _token_count(candidate_delta, self.config.source_language) >= self.config.min_commit_tokens
        wait_sec = 0.0 if self._pending_since_sec is None else now_sec - self._pending_since_sec
        commit_due_to_wait = bool(candidate_delta) and wait_sec >= self.config.max_commit_sec
        commit_due_to_min_wait = (
            bool(candidate_delta)
            and wait_sec >= self.config.min_commit_sec
            and _looks_like_complete_phrase(candidate_delta, self.config.source_language)
        )
        confirmed_delta = candidate_delta if commit_due_to_size or commit_due_to_wait or commit_due_to_min_wait else ""
        if confirmed_delta:
            self.confirmed_text = _join_text(self.confirmed_text, confirmed_delta, self.config.source_language)
            self._pending_since_sec = None

        unconfirmed_tail = _remove_confirmed_prefix(
            clean_hypothesis,
            self.confirmed_text,
            self.config.source_language,
        )
        partial_text = _join_text(confirmed_delta, unconfirmed_tail, self.config.source_language)
        should_translate_partial = self._should_translate_partial(partial_text, now_sec)

        final_candidate = clean_hypothesis or self.confirmed_text
        unconfirmed_age = 0.0 if self._pending_since_sec is None else now_sec - self._pending_since_sec
        sentence_age = 0.0 if self._sentence_started_sec is None else now_sec - self._sentence_started_sec
        should_finalize = bool(final_candidate) and (
            silence_final
            or _ends_with_final_punctuation(clean_hypothesis)
            or sentence_age >= self.config.max_commit_sec
            or unconfirmed_age >= self.config.max_unconfirmed_sec
        )

        return AgreementUpdate(
            confirmed_delta=confirmed_delta,
            unconfirmed_tail=unconfirmed_tail,
            partial_text=partial_text,
            final_text=final_candidate if should_finalize else "",
            should_translate_partial=should_translate_partial,
            should_finalize=should_finalize,
            confirmed_text=self.confirmed_text,
        )

    def mark_finalized(self) -> None:
        self.confirmed_text = ""
        self._hypotheses.clear()
        self._pending_since_sec = None
        self._sentence_started_sec = None
        self._last_partial_text = ""
        self._last_partial_sec = None

    def _common_prefix(self, hypotheses: list[str]) -> str:
        usable = [text for text in hypotheses if text]
        if len(usable) < self.config.agreement_n:
            return ""
        if _language_mode(self.config.source_language, " ".join(usable)) == "en":
            return _common_word_prefix(usable)
        return _common_char_prefix(usable)

    def _should_translate_partial(self, partial_text: str, now_sec: float) -> bool:
        if not self.config.enable_partial_subtitle or not partial_text:
            return False
        if not self._last_partial_text:
            self._last_partial_text = partial_text
            self._last_partial_sec = now_sec
            return True

        if _language_mode(self.config.source_language, partial_text) == "en":
            enough_growth = _token_count(
                _remove_confirmed_prefix(partial_text, self._last_partial_text, "en"),
                "en",
            ) >= self.config.partial_min_words_en
        else:
            enough_growth = len(
                _remove_confirmed_prefix(partial_text, self._last_partial_text, "ja")
            ) >= self.config.partial_min_chars_ja
        enough_time = self._last_partial_sec is not None and now_sec - self._last_partial_sec >= self.config.partial_interval_sec
        if enough_growth or enough_time:
            self._last_partial_text = partial_text
            self._last_partial_sec = now_sec
            return True
        return False


def _language_mode(language: SourceLanguage, text: str = "") -> str:
    if language == "ja" or (language == "auto" and _contains_japanese(text)):
        return "ja"
    return "en"


def _common_word_prefix(texts: list[str]) -> str:
    token_lists = [_word_tokens(text) for text in texts]
    limit = min(len(tokens) for tokens in token_lists)
    index = 0
    while index < limit:
        values = [_normalize_word(tokens[index]) for tokens in token_lists]
        if any(not value for value in values) or len(set(values)) != 1:
            break
        index += 1
    return " ".join(token_lists[-1][:index]).strip()


def _common_char_prefix(texts: list[str]) -> str:
    if not texts:
        return ""
    shortest = min(texts, key=len)
    limit = len(shortest)
    index = 0
    while index < limit and all(text[index] == shortest[index] for text in texts):
        index += 1
    return shortest[:index].strip()


def _word_tokens(text: str) -> list[str]:
    return re.findall(r"\S+", text.strip())


def _normalize_word(token: str) -> str:
    return token.strip().lower()


def _remove_confirmed_prefix(text: str, confirmed: str, language: SourceLanguage) -> str:
    clean_text = text.strip()
    clean_confirmed = confirmed.strip()
    if not clean_confirmed:
        return clean_text
    if _language_mode(language, clean_text + clean_confirmed) == "en":
        text_tokens = _word_tokens(clean_text)
        confirmed_tokens = _word_tokens(clean_confirmed)
        if len(text_tokens) >= len(confirmed_tokens) and [
            _normalize_word(token) for token in text_tokens[: len(confirmed_tokens)]
        ] == [_normalize_word(token) for token in confirmed_tokens]:
            return " ".join(text_tokens[len(confirmed_tokens) :]).strip()
    elif clean_text.startswith(clean_confirmed):
        return clean_text[len(clean_confirmed) :].strip()
    return clean_text


def _token_count(text: str, language: SourceLanguage) -> int:
    if not text.strip():
        return 0
    if _language_mode(language, text) == "en":
        return len(_word_tokens(text))
    return len(text.strip())


def _join_text(left: str, right: str, language: SourceLanguage) -> str:
    left = left.strip()
    right = right.strip()
    if not left:
        return right
    if not right:
        return left
    if _language_mode(language, left + right) == "en":
        return f"{left} {right}"
    return f"{left}{right}"


def _looks_like_complete_phrase(text: str, language: SourceLanguage) -> bool:
    return _ends_with_final_punctuation(text) or _token_count(text, language) >= 2


def _ends_with_final_punctuation(text: str) -> bool:
    stripped = text.strip()
    return bool(stripped) and stripped[-1] in FINAL_PUNCTUATION


def _contains_japanese(text: str) -> bool:
    return any(
        "\u3040" <= char <= "\u30ff" or "\u4e00" <= char <= "\u9fff"
        for char in text
    )
