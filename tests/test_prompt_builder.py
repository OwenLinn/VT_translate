from __future__ import annotations

import pytest

from yt_live_translator.translate.prompt_builder import GlossaryTerm, build_translation_prompt


def test_build_prompt_for_traditional_chinese() -> None:
    prompt = build_translation_prompt(
        text="Hello everyone, welcome to the stream.",
        target_language="zh-TW",
        source_language="en",
    )

    assert "Traditional Chinese" in prompt.system_prompt
    assert "zh-TW" in prompt.user_prompt
    assert "Hello everyone" in prompt.user_prompt


def test_build_prompt_for_simplified_chinese() -> None:
    prompt = build_translation_prompt(
        text="配信へようこそ",
        target_language="zh-CN",
        source_language="ja",
    )

    assert "Simplified Chinese" in prompt.system_prompt
    assert "zh-CN" in prompt.user_prompt
    assert "配信へようこそ" in prompt.user_prompt


def test_prompt_includes_matching_glossary_target() -> None:
    prompt = build_translation_prompt(
        text="The Tarnished enters Limgrave.",
        target_language="zh-TW",
        source_language="en",
        glossary_terms=[
            GlossaryTerm(
                source="Tarnished",
                target_zh_tw="褪色者",
                target_zh_cn="褪色者",
                term_type="game",
                note="Elden Ring player character",
            )
        ],
    )

    assert "Active glossary terms" in prompt.user_prompt
    assert "Tarnished => 褪色者" in prompt.user_prompt
    assert "Elden Ring player character" in prompt.user_prompt


def test_empty_text_is_rejected() -> None:
    with pytest.raises(ValueError, match="text must not be empty"):
        build_translation_prompt(text="   ", target_language="zh-TW")
