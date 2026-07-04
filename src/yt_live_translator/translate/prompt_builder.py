"""Build translation prompts for livestream subtitles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from yt_live_translator.core.models import SourceLanguage, TargetLanguage


@dataclass(frozen=True)
class GlossaryTerm:
    source: str
    target_zh_tw: str | None = None
    target_zh_cn: str | None = None
    source_lang: SourceLanguage = "auto"
    term_type: str = "other"
    note: str | None = None


@dataclass(frozen=True)
class TranslationPrompt:
    system_prompt: str
    user_prompt: str


_TARGET_LABELS: dict[TargetLanguage, str] = {
    "zh-TW": "Traditional Chinese",
    "zh-CN": "Simplified Chinese",
}


def build_translation_prompt(
    text: str,
    target_language: TargetLanguage,
    source_language: SourceLanguage = "auto",
    glossary_terms: Iterable[GlossaryTerm] | None = None,
) -> TranslationPrompt:
    if target_language not in _TARGET_LABELS:
        raise ValueError("target_language must be zh-TW or zh-CN")
    if source_language not in ("auto", "en", "ja"):
        raise ValueError("source_language must be auto, en, or ja")

    clean_text = text.strip()
    if not clean_text:
        raise ValueError("text must not be empty")

    system_prompt = _system_prompt(target_language)
    user_parts = [
        f"Source language: {source_language}",
        f"Target language: {_TARGET_LABELS[target_language]} ({target_language})",
    ]

    glossary_block = _format_glossary_terms(target_language, glossary_terms or [])
    if glossary_block:
        user_parts.append(glossary_block)

    user_parts.append("Translate this livestream subtitle text:")
    user_parts.append(clean_text)
    return TranslationPrompt(system_prompt=system_prompt, user_prompt="\n\n".join(user_parts))


def _system_prompt(target_language: TargetLanguage) -> str:
    if target_language == "zh-TW":
        return (
            "You are a professional livestream subtitle translator. Translate English or "
            "Japanese speech into natural Traditional Chinese using Taiwan usage. "
            "Use ONLY Traditional Chinese characters (繁體字). "
            "Use Taiwan-common expressions (e.g. 影片 not 視頻, 透過 not 通過, 品質 not 質量). "
            "Preserve names, game terms, numbers, and streamer tone. "
            "Preserve interjections and laughter (e.g. 啊哈哈, ふふっ). "
            "Return only the translated subtitle text. No explanations."
        )
    return (
        "You are a professional livestream subtitle translator. Translate English or "
        "Japanese speech into natural Simplified Chinese. Preserve names, game terms, "
        "numbers, and streamer tone. Return only the translated subtitle text."
    )


def _format_glossary_terms(
    target_language: TargetLanguage,
    glossary_terms: Iterable[GlossaryTerm],
) -> str:
    lines = []
    for term in glossary_terms:
        target = term.target_zh_tw if target_language == "zh-TW" else term.target_zh_cn
        if not term.source or not target:
            continue
        note = f" ({term.note})" if term.note else ""
        lines.append(f"- {term.source} => {target}; type={term.term_type}{note}")

    if not lines:
        return ""

    return "Active glossary terms. Use these translations when they match clearly:\n" + "\n".join(
        lines
    )
