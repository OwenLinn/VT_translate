from __future__ import annotations

from yt_live_translator.storage.glossary_repo import GlossaryEntry, GlossaryRepository
from yt_live_translator.translate.glossary_apply import (
    apply_conservative_post_processing,
    get_prompt_glossary_terms,
)


def test_get_prompt_glossary_terms_only_returns_matches(tmp_path) -> None:
    repository = GlossaryRepository(tmp_path / "glossary.sqlite3")
    repository.add_term(source="Miko", target_zh_tw="咪口", source_lang="ja")
    repository.add_term(source="Tarnished", target_zh_tw="褪色者", source_lang="en")

    terms = get_prompt_glossary_terms(
        repository,
        text="Miko is laughing",
        source_language="ja",
        target_language="zh-TW",
    )

    assert [term.source for term in terms] == ["Miko"]
    assert terms[0].target_zh_tw == "咪口"


def test_post_processing_replaces_leftover_source_term() -> None:
    entry = GlossaryEntry(source="Miko", target_zh_tw="咪口", source_lang="ja")

    result = apply_conservative_post_processing(
        source_text="Miko starts the stream",
        translated_text="Miko 開始直播",
        matched_terms=[entry],
        target_language="zh-TW",
    )

    assert result == "咪口 開始直播"


def test_post_processing_does_not_append_missing_target() -> None:
    entry = GlossaryEntry(source="Miko", target_zh_tw="咪口", source_lang="ja")

    result = apply_conservative_post_processing(
        source_text="Miko starts the stream",
        translated_text="她開始直播",
        matched_terms=[entry],
        target_language="zh-TW",
    )

    assert result == "她開始直播"
