"""SQLite repository for manual glossary terms."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from yt_live_translator.core.models import SourceLanguage, TargetLanguage
from yt_live_translator.storage.db import connect_database, initialize_database
from yt_live_translator.translate.prompt_builder import GlossaryTerm


TERM_TYPES = (
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
)


@dataclass(frozen=True)
class GlossaryEntry:
    source: str
    target_zh_tw: str | None = None
    target_zh_cn: str | None = None
    source_lang: SourceLanguage = "auto"
    term_type: str = "other"
    note: str | None = None
    exact_match: bool = True
    case_sensitive: bool = False
    enabled: bool = True
    id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def target_for(self, target_language: TargetLanguage) -> str | None:
        return self.target_zh_tw if target_language == "zh-TW" else self.target_zh_cn

    def to_prompt_term(self) -> GlossaryTerm:
        return GlossaryTerm(
            source=self.source,
            target_zh_tw=self.target_zh_tw,
            target_zh_cn=self.target_zh_cn,
            source_lang=self.source_lang,
            term_type=self.term_type,
            note=self.note,
        )


class GlossaryRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        with connect_database(self.database_path) as connection:
            initialize_database(connection)

    def add_term(
        self,
        *,
        source: str,
        target_zh_tw: str | None = None,
        target_zh_cn: str | None = None,
        source_lang: SourceLanguage = "auto",
        term_type: str = "other",
        note: str | None = None,
        exact_match: bool = True,
        case_sensitive: bool = False,
        enabled: bool = True,
    ) -> GlossaryEntry:
        entry = GlossaryEntry(
            source=_required_source(source),
            target_zh_tw=_clean_optional(target_zh_tw),
            target_zh_cn=_clean_optional(target_zh_cn),
            source_lang=_source_language(source_lang),
            term_type=_term_type(term_type),
            note=_clean_optional(note),
            exact_match=exact_match,
            case_sensitive=case_sensitive,
            enabled=enabled,
        )
        now = _now()
        with connect_database(self.database_path) as connection:
            initialize_database(connection)
            cursor = connection.execute(
                """
                INSERT INTO glossary_terms (
                  source, target_zh_tw, target_zh_cn, source_lang, term_type,
                  note, exact_match, case_sensitive, enabled, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.source,
                    entry.target_zh_tw,
                    entry.target_zh_cn,
                    entry.source_lang,
                    entry.term_type,
                    entry.note,
                    int(entry.exact_match),
                    int(entry.case_sensitive),
                    int(entry.enabled),
                    now,
                    now,
                ),
            )
            connection.commit()
            return self.get_term(int(cursor.lastrowid))

    def get_term(self, term_id: int) -> GlossaryEntry:
        with connect_database(self.database_path) as connection:
            initialize_database(connection)
            row = connection.execute(
                "SELECT * FROM glossary_terms WHERE id = ?",
                (term_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Glossary term not found: {term_id}")
        return _entry_from_row(row)

    def list_terms(self, *, enabled_only: bool = False) -> list[GlossaryEntry]:
        query = "SELECT * FROM glossary_terms"
        params: tuple[object, ...] = ()
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY lower(source), id"
        with connect_database(self.database_path) as connection:
            initialize_database(connection)
            rows = connection.execute(query, params).fetchall()
        return [_entry_from_row(row) for row in rows]

    def find_matching_terms(
        self,
        *,
        text: str,
        source_language: SourceLanguage,
        target_language: TargetLanguage,
        limit: int = 20,
    ) -> list[GlossaryEntry]:
        if limit <= 0:
            return []

        source_text = text.strip()
        if not source_text:
            return []

        matches: list[GlossaryEntry] = []
        for entry in self.list_terms(enabled_only=True):
            if entry.source_lang not in ("auto", source_language):
                continue
            if not entry.target_for(target_language):
                continue
            if glossary_entry_matches(entry, source_text):
                matches.append(entry)
            if len(matches) >= limit:
                break
        return matches


def glossary_entry_matches(entry: GlossaryEntry, text: str) -> bool:
    if not entry.source:
        return False
    haystack = text if entry.case_sensitive else text.casefold()
    needle = entry.source if entry.case_sensitive else entry.source.casefold()
    if not entry.exact_match:
        return needle in haystack
    return re.search(_term_pattern(needle), haystack) is not None


def _term_pattern(term: str) -> str:
    escaped = re.escape(term)
    if re.fullmatch(r"[\w ]+", term, flags=re.ASCII):
        return rf"(?<!\w){escaped}(?!\w)"
    return escaped


def _entry_from_row(row: sqlite3.Row) -> GlossaryEntry:
    return GlossaryEntry(
        id=int(row["id"]),
        source=row["source"],
        target_zh_tw=row["target_zh_tw"],
        target_zh_cn=row["target_zh_cn"],
        source_lang=_source_language(row["source_lang"] or "auto"),
        term_type=_term_type(row["term_type"] or "other"),
        note=row["note"],
        exact_match=bool(row["exact_match"]),
        case_sensitive=bool(row["case_sensitive"]),
        enabled=bool(row["enabled"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _required_source(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("source must not be empty")
    return cleaned


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _source_language(value: str) -> SourceLanguage:
    if value not in ("auto", "en", "ja"):
        raise ValueError("source_lang must be auto, en, or ja")
    return value  # type: ignore[return-value]


def _term_type(value: str) -> str:
    if value not in TERM_TYPES:
        allowed = ", ".join(TERM_TYPES)
        raise ValueError(f"term_type must be one of: {allowed}")
    return value


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def prompt_terms(entries: Iterable[GlossaryEntry]) -> list[GlossaryTerm]:
    return [entry.to_prompt_term() for entry in entries]
