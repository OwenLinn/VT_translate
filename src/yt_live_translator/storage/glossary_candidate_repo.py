"""Repository for AI/manual glossary candidate suggestions."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from yt_live_translator.core.models import SourceLanguage
from yt_live_translator.storage.db import connect_database, initialize_database
from yt_live_translator.storage.glossary_repo import GlossaryRepository, TERM_TYPES


CANDIDATE_STATUSES = ("pending", "accepted", "ignored")


@dataclass(frozen=True)
class GlossaryCandidate:
    source: str
    source_lang: SourceLanguage
    occurrences: int
    sample_text: str | None = None
    translation_variants: tuple[str, ...] = ()
    inconsistent: bool = False
    suggested_target_zh_tw: str | None = None
    suggested_target_zh_cn: str | None = None
    term_type: str = "other"
    confidence: float = 0.0
    status: str = "pending"
    classifier: str = "heuristic"
    id: int | None = None
    accepted_glossary_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class GlossaryCandidateRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        with connect_database(self.database_path) as connection:
            initialize_database(connection)

    def upsert_candidate(self, candidate: GlossaryCandidate) -> GlossaryCandidate:
        _validate_candidate(candidate)
        now = _now()
        with connect_database(self.database_path) as connection:
            initialize_database(connection)
            existing = connection.execute(
                """
                SELECT * FROM glossary_candidates
                WHERE source = ? AND source_lang = ?
                """,
                (candidate.source, candidate.source_lang),
            ).fetchone()
            if existing is not None and existing["status"] != "pending":
                return _candidate_from_row(existing)
            connection.execute(
                """
                INSERT INTO glossary_candidates (
                  source, source_lang, occurrences, sample_text, translation_variants,
                  inconsistent, suggested_target_zh_tw, suggested_target_zh_cn,
                  term_type, confidence, status, classifier, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source, source_lang) DO UPDATE SET
                  occurrences = excluded.occurrences,
                  sample_text = excluded.sample_text,
                  translation_variants = excluded.translation_variants,
                  inconsistent = excluded.inconsistent,
                  suggested_target_zh_tw = COALESCE(
                    excluded.suggested_target_zh_tw,
                    glossary_candidates.suggested_target_zh_tw
                  ),
                  suggested_target_zh_cn = COALESCE(
                    excluded.suggested_target_zh_cn,
                    glossary_candidates.suggested_target_zh_cn
                  ),
                  term_type = excluded.term_type,
                  confidence = excluded.confidence,
                  classifier = excluded.classifier,
                  updated_at = excluded.updated_at
                """,
                (
                    candidate.source,
                    candidate.source_lang,
                    candidate.occurrences,
                    candidate.sample_text,
                    json.dumps(list(candidate.translation_variants), ensure_ascii=False),
                    int(candidate.inconsistent),
                    candidate.suggested_target_zh_tw,
                    candidate.suggested_target_zh_cn,
                    candidate.term_type,
                    candidate.confidence,
                    candidate.status,
                    candidate.classifier,
                    now,
                    now,
                ),
            )
            connection.commit()
        return self.get_by_source(candidate.source, candidate.source_lang)

    def upsert_many(self, candidates: Iterable[GlossaryCandidate]) -> list[GlossaryCandidate]:
        return [self.upsert_candidate(candidate) for candidate in candidates]

    def get_candidate(self, candidate_id: int) -> GlossaryCandidate:
        with connect_database(self.database_path) as connection:
            initialize_database(connection)
            row = connection.execute(
                "SELECT * FROM glossary_candidates WHERE id = ?",
                (candidate_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Glossary candidate not found: {candidate_id}")
        return _candidate_from_row(row)

    def get_by_source(self, source: str, source_lang: SourceLanguage) -> GlossaryCandidate:
        with connect_database(self.database_path) as connection:
            initialize_database(connection)
            row = connection.execute(
                """
                SELECT * FROM glossary_candidates
                WHERE source = ? AND source_lang = ?
                """,
                (source, source_lang),
            ).fetchone()
        if row is None:
            raise KeyError(f"Glossary candidate not found: {source}")
        return _candidate_from_row(row)

    def list_candidates(self, *, status: str | None = "pending") -> list[GlossaryCandidate]:
        query = "SELECT * FROM glossary_candidates"
        params: tuple[object, ...] = ()
        if status is not None:
            _validate_status(status)
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY occurrences DESC, lower(source), id"
        with connect_database(self.database_path) as connection:
            initialize_database(connection)
            rows = connection.execute(query, params).fetchall()
        return [_candidate_from_row(row) for row in rows]

    def ignore_candidate(self, candidate_id: int) -> GlossaryCandidate:
        return self._set_status(candidate_id, "ignored", accepted_glossary_id=None)

    def accept_candidate(
        self,
        candidate_id: int,
        glossary_repository: GlossaryRepository,
        *,
        target_zh_tw: str | None = None,
        target_zh_cn: str | None = None,
    ) -> GlossaryCandidate:
        candidate = self.get_candidate(candidate_id)
        if candidate.status == "accepted":
            return candidate
        target_tw = _clean_optional(target_zh_tw) or candidate.suggested_target_zh_tw
        target_cn = _clean_optional(target_zh_cn) or candidate.suggested_target_zh_cn
        glossary_entry = glossary_repository.add_term(
            source=candidate.source,
            target_zh_tw=target_tw,
            target_zh_cn=target_cn,
            source_lang=candidate.source_lang,
            term_type=candidate.term_type,
            note=f"Accepted from Stage 10 candidate #{candidate.id}",
            exact_match=True,
            case_sensitive=False,
            enabled=True,
        )
        return self._set_status(
            candidate_id,
            "accepted",
            accepted_glossary_id=glossary_entry.id,
        )

    def _set_status(
        self,
        candidate_id: int,
        status: str,
        *,
        accepted_glossary_id: int | None,
    ) -> GlossaryCandidate:
        _validate_status(status)
        with connect_database(self.database_path) as connection:
            initialize_database(connection)
            connection.execute(
                """
                UPDATE glossary_candidates
                SET status = ?, accepted_glossary_id = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, accepted_glossary_id, _now(), candidate_id),
            )
            connection.commit()
        return self.get_candidate(candidate_id)


def _candidate_from_row(row: sqlite3.Row) -> GlossaryCandidate:
    variants = tuple(json.loads(row["translation_variants"] or "[]"))
    return GlossaryCandidate(
        id=int(row["id"]),
        source=row["source"],
        source_lang=_source_language(row["source_lang"]),
        occurrences=int(row["occurrences"]),
        sample_text=row["sample_text"],
        translation_variants=variants,
        inconsistent=bool(row["inconsistent"]),
        suggested_target_zh_tw=row["suggested_target_zh_tw"],
        suggested_target_zh_cn=row["suggested_target_zh_cn"],
        term_type=_term_type(row["term_type"] or "other"),
        confidence=float(row["confidence"] or 0.0),
        status=row["status"],
        classifier=row["classifier"] or "heuristic",
        accepted_glossary_id=row["accepted_glossary_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _validate_candidate(candidate: GlossaryCandidate) -> None:
    if not candidate.source.strip():
        raise ValueError("candidate source must not be empty")
    _source_language(candidate.source_lang)
    _term_type(candidate.term_type)
    _validate_status(candidate.status)
    if candidate.occurrences < 1:
        raise ValueError("candidate occurrences must be positive")
    if candidate.confidence < 0.0 or candidate.confidence > 1.0:
        raise ValueError("candidate confidence must be between 0 and 1")


def _source_language(value: str) -> SourceLanguage:
    if value not in ("auto", "en", "ja"):
        raise ValueError("source_lang must be auto, en, or ja")
    return value  # type: ignore[return-value]


def _term_type(value: str) -> str:
    if value not in TERM_TYPES:
        allowed = ", ".join(TERM_TYPES)
        raise ValueError(f"term_type must be one of: {allowed}")
    return value


def _validate_status(value: str) -> None:
    if value not in CANDIDATE_STATUSES:
        allowed = ", ".join(CANDIDATE_STATUSES)
        raise ValueError(f"candidate status must be one of: {allowed}")


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
