"""Extract and classify glossary candidates from subtitle history."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import replace
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from yt_live_translator.core.config import DeepSeekConfig
from yt_live_translator.core.models import SourceLanguage
from yt_live_translator.storage.glossary_candidate_repo import GlossaryCandidate
from yt_live_translator.storage.glossary_repo import GlossaryRepository
from yt_live_translator.storage.subtitle_log_repo import SubtitleLogEntry
from yt_live_translator.translate.deepseek_client import DeepSeekAPIError, MissingAPIKeyError


ENGLISH_STOPWORDS = {
    "and",
    "are",
    "but",
    "for",
    "from",
    "hello",
    "just",
    "like",
    "stream",
    "that",
    "the",
    "this",
    "with",
    "you",
}


class CandidateClassifier(Protocol):
    def classify(self, candidates: list[GlossaryCandidate]) -> list[GlossaryCandidate]:
        """Return candidates with classification fields filled."""


class HeuristicCandidateClassifier:
    def classify(self, candidates: list[GlossaryCandidate]) -> list[GlossaryCandidate]:
        return [classify_candidate_heuristically(candidate) for candidate in candidates]


class DeepSeekCandidateClassifier:
    def __init__(
        self,
        *,
        config: DeepSeekConfig,
        api_key: str | None,
        opener=urlopen,
    ) -> None:
        self.config = config
        self.api_key = api_key
        self.opener = opener

    def classify(self, candidates: list[GlossaryCandidate]) -> list[GlossaryCandidate]:
        if not candidates:
            return []
        if not self.api_key:
            raise MissingAPIKeyError(
                f"DeepSeek API key is missing. Set {self.config.api_key_env} or add "
                "deepseek.api_key to config.toml."
            )
        request = Request(
            url=_chat_completions_url(self.config.base_url),
            data=json.dumps(_classification_payload(self.config.model, candidates)).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with self.opener(request, timeout=self.config.timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
        except HTTPError as exc:
            raise DeepSeekAPIError(f"DeepSeek candidate classification failed with HTTP {exc.code}") from exc
        except URLError as exc:
            raise DeepSeekAPIError(f"DeepSeek candidate classification failed: {exc.reason}") from exc
        except TimeoutError as exc:
            raise DeepSeekAPIError("DeepSeek candidate classification timed out") from exc

        return _apply_ai_classification(candidates, response_body)


def extract_glossary_candidates(
    entries: list[SubtitleLogEntry],
    *,
    glossary_repository: GlossaryRepository | None = None,
    min_occurrences: int = 2,
    limit: int = 30,
) -> list[GlossaryCandidate]:
    if min_occurrences < 1:
        raise ValueError("min_occurrences must be positive")
    if limit < 1:
        raise ValueError("limit must be positive")

    existing_terms = {
        entry.source.casefold()
        for entry in (glossary_repository.list_terms() if glossary_repository else [])
    }
    grouped: dict[tuple[str, SourceLanguage], list[SubtitleLogEntry]] = defaultdict(list)
    for entry in entries:
        source_language = _entry_source_language(entry)
        for term in _terms_from_text(entry.source_text):
            if term.casefold() in existing_terms:
                continue
            grouped[(term, source_language)].append(entry)

    candidates = []
    for (term, source_language), term_entries in grouped.items():
        if len(term_entries) < min_occurrences:
            continue
        variants = _translation_variants(term_entries, limit=5)
        candidates.append(
            classify_candidate_heuristically(
                GlossaryCandidate(
                    source=term,
                    source_lang=source_language,
                    occurrences=len(term_entries),
                    sample_text=term_entries[0].source_text,
                    translation_variants=variants,
                    inconsistent=len(variants) > 1,
                    classifier="heuristic",
                )
            )
        )

    candidates.sort(key=lambda item: (-item.occurrences, item.source.casefold()))
    return candidates[:limit]


def classify_candidate_heuristically(candidate: GlossaryCandidate) -> GlossaryCandidate:
    source = candidate.source
    if re.fullmatch(r"[ァ-ヴー]+", source):
        term_type = "character" if len(source) >= 3 else "other"
        confidence = 0.7
    elif re.fullmatch(r"[A-Z][A-Za-z0-9_'-]+(?: [A-Z][A-Za-z0-9_'-]+){0,2}", source):
        term_type = "person"
        confidence = 0.75
    elif source.isupper() and len(source) >= 3:
        term_type = "technical"
        confidence = 0.65
    else:
        term_type = "other"
        confidence = 0.45
    return replace(
        candidate,
        term_type=term_type,
        confidence=max(candidate.confidence, confidence),
        classifier=candidate.classifier or "heuristic",
    )


def classify_with_ai(
    candidates: list[GlossaryCandidate],
    classifier: CandidateClassifier,
) -> list[GlossaryCandidate]:
    return classifier.classify(candidates)


def _terms_from_text(text: str) -> list[str]:
    terms: list[str] = []
    for match in re.finditer(r"[ァ-ヴー]{2,}", text):
        terms.append(match.group(0))
    for match in re.finditer(
        r"\b[A-Z][A-Za-z0-9_'-]{2,}(?:\s+[A-Z][A-Za-z0-9_'-]{2,}){0,2}\b",
        text,
    ):
        terms.append(match.group(0))
    for match in re.finditer(r"\b[A-Za-z][A-Za-z0-9_'-]{2,}\b", text):
        value = match.group(0)
        if value.casefold() not in ENGLISH_STOPWORDS:
            terms.append(value)
    return _dedupe_preserving_order([_normalize_term(term) for term in terms if term.strip()])


def _normalize_term(term: str) -> str:
    return re.sub(r"\s+", " ", term.strip())


def _dedupe_preserving_order(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def _entry_source_language(entry: SubtitleLogEntry) -> SourceLanguage:
    if entry.source_language in ("auto", "en", "ja"):
        return entry.source_language  # type: ignore[return-value]
    if re.search(r"[ぁ-んァ-ヴー一-龯]", entry.source_text):
        return "ja"
    if re.search(r"[A-Za-z]", entry.source_text):
        return "en"
    return "auto"


def _translation_variants(entries: list[SubtitleLogEntry], *, limit: int) -> tuple[str, ...]:
    values = _dedupe_preserving_order(
        [entry.translated_text.strip() for entry in entries if entry.translated_text.strip()]
    )
    return tuple(values[:limit])


def _classification_payload(model: str, candidates: list[GlossaryCandidate]) -> dict:
    items = [
        {
            "source": candidate.source,
            "source_lang": candidate.source_lang,
            "occurrences": candidate.occurrences,
            "sample_text": candidate.sample_text,
            "translation_variants": list(candidate.translation_variants),
        }
        for candidate in candidates
    ]
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Classify livestream glossary candidates. Return only JSON with an "
                    "items array. Each item must contain source, term_type, "
                    "target_zh_tw, target_zh_cn, and confidence. term_type must be one "
                    "of person, game, character, ability, item, place, organization, "
                    "technical, slang, other."
                ),
            },
            {"role": "user", "content": json.dumps({"items": items}, ensure_ascii=False)},
        ],
        "temperature": 0.1,
    }


def _apply_ai_classification(
    candidates: list[GlossaryCandidate],
    response_body: str,
) -> list[GlossaryCandidate]:
    try:
        payload = json.loads(response_body)
        content = payload["choices"][0]["message"]["content"]
        parsed = json.loads(_strip_code_fence(content))
        items = parsed["items"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise DeepSeekAPIError("DeepSeek candidate classification returned invalid JSON") from exc

    by_source = {candidate.source: candidate for candidate in candidates}
    classified = []
    for item in items:
        source = item.get("source")
        if source not in by_source:
            continue
        candidate = by_source[source]
        term_type = item.get("term_type") or candidate.term_type
        if term_type not in {
            "person",
            "game",
            "character",
            "ability",
            "item",
            "place",
            "organization",
            "technical",
            "slang",
            "other",
        }:
            term_type = "other"
        classified.append(
            replace(
                candidate,
                term_type=term_type,
                suggested_target_zh_tw=_clean_optional(item.get("target_zh_tw")),
                suggested_target_zh_cn=_clean_optional(item.get("target_zh_cn")),
                confidence=_bounded_float(item.get("confidence"), candidate.confidence),
                classifier="deepseek",
            )
        )
    seen = {candidate.source for candidate in classified}
    classified.extend(candidate for candidate in candidates if candidate.source not in seen)
    return classified


def _strip_code_fence(value: str) -> str:
    text = value.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _bounded_float(value, fallback: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return fallback
    return min(1.0, max(0.0, parsed))


def _clean_optional(value) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _chat_completions_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{normalized}/chat/completions"
