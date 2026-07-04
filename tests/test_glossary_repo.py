from __future__ import annotations

from yt_live_translator.storage.glossary_repo import GlossaryRepository


def test_add_and_list_glossary_term(tmp_path) -> None:
    repository = GlossaryRepository(tmp_path / "glossary.sqlite3")

    entry = repository.add_term(
        source="Tarnished",
        target_zh_tw="褪色者",
        target_zh_cn="褪色者",
        source_lang="en",
        term_type="character",
        note="Elden Ring player character",
    )

    entries = repository.list_terms()
    assert entry.id is not None
    assert len(entries) == 1
    assert entries[0].source == "Tarnished"
    assert entries[0].target_zh_tw == "褪色者"
    assert entries[0].note == "Elden Ring player character"


def test_find_matching_terms_filters_language_and_target(tmp_path) -> None:
    repository = GlossaryRepository(tmp_path / "glossary.sqlite3")
    repository.add_term(source="Miko", target_zh_tw="咪口", source_lang="ja")
    repository.add_term(source="Limgrave", target_zh_cn="宁姆格福", source_lang="en")
    repository.add_term(source="disabled", target_zh_tw="停用", enabled=False)

    matches = repository.find_matching_terms(
        text="Miko starts the stream",
        source_language="ja",
        target_language="zh-TW",
    )

    assert [entry.source for entry in matches] == ["Miko"]


def test_exact_english_terms_use_word_boundaries(tmp_path) -> None:
    repository = GlossaryRepository(tmp_path / "glossary.sqlite3")
    repository.add_term(source="art", target_zh_tw="美術", source_lang="en")

    assert repository.find_matching_terms(
        text="This is a party.",
        source_language="en",
        target_language="zh-TW",
    ) == []
    assert repository.find_matching_terms(
        text="This art is nice.",
        source_language="en",
        target_language="zh-TW",
    )[0].source == "art"
