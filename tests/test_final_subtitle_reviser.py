from __future__ import annotations

from yt_live_translator.translate.final_subtitle_reviser import FinalSubtitleReviser


def test_final_subtitle_reviser_translates_full_source_text() -> None:
    calls = []

    def translate(text, source, target):
        calls.append((text, source, target))
        return f"{target}:{text}"

    revision = FinalSubtitleReviser(translate).revise(
        source_text="hello stream today.",
        source_language="en",
        target_language="zh-TW",
    )

    assert calls == [("hello stream today.", "en", "zh-TW")]
    assert revision.translated_text == "zh-TW:hello stream today."
    assert revision.latency_ms >= 0
