"""Glossary matching and conservative translation post-processing."""

from __future__ import annotations

import re
from pathlib import Path

from yt_live_translator.core.config import RuntimeConfig
from yt_live_translator.core.models import SourceLanguage, TargetLanguage
from yt_live_translator.storage.db import resolve_database_path
from yt_live_translator.storage.glossary_repo import (
    GlossaryEntry,
    GlossaryRepository,
    glossary_entry_matches,
    prompt_terms,
)
from yt_live_translator.translate.deepseek_client import DeepSeekClient
from yt_live_translator.translate.prompt_builder import GlossaryTerm


def open_glossary_repository(
    runtime_config: RuntimeConfig,
    database_path: str | Path | None = None,
) -> GlossaryRepository:
    return GlossaryRepository(resolve_database_path(runtime_config, database_path))


def get_prompt_glossary_terms(
    repository: GlossaryRepository | None,
    *,
    text: str,
    source_language: SourceLanguage,
    target_language: TargetLanguage,
) -> list[GlossaryTerm]:
    if repository is None:
        return []
    entries = repository.find_matching_terms(
        text=text,
        source_language=source_language,
        target_language=target_language,
    )
    return prompt_terms(entries)


def translate_with_glossary(
    client: DeepSeekClient,
    *,
    text: str,
    source_language: SourceLanguage,
    target_language: TargetLanguage,
    repository: GlossaryRepository | None,
) -> str:
    matched_entries = (
        repository.find_matching_terms(
            text=text,
            source_language=source_language,
            target_language=target_language,
        )
        if repository is not None
        else []
    )
    translated = client.translate(
        text=text,
        source_language=source_language,
        target_language=target_language,
        glossary_terms=prompt_terms(matched_entries),
    )
    return apply_conservative_post_processing(
        source_text=text,
        translated_text=translated,
        matched_terms=matched_entries,
        target_language=target_language,
    )


def apply_conservative_post_processing(
    *,
    source_text: str,
    translated_text: str,
    matched_terms: list[GlossaryEntry],
    target_language: TargetLanguage,
) -> str:
    """Replace only obvious leftover source terms with glossary targets."""

    result = translated_text
    for entry in matched_terms:
        target = entry.target_for(target_language)
        if not target or target in result:
            continue
        if not glossary_entry_matches(entry, source_text):
            continue
        result = _replace_literal_term(
            result,
            source=entry.source,
            target=target,
            case_sensitive=entry.case_sensitive,
            exact_match=entry.exact_match,
        )
    return result


def _replace_literal_term(
    text: str,
    *,
    source: str,
    target: str,
    case_sensitive: bool,
    exact_match: bool,
) -> str:
    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = re.escape(source)
    if exact_match and re.fullmatch(r"[\w ]+", source, flags=re.ASCII):
        pattern = rf"(?<!\w){pattern}(?!\w)"
    return re.sub(pattern, target, text, flags=flags)
