from __future__ import annotations

from yt_live_translator.core.models import TranslationResult
from yt_live_translator.storage.subtitle_log_repo import SubtitleLogRepository


def test_subtitle_log_appends_and_lists_entries(tmp_path) -> None:
    repository = SubtitleLogRepository(tmp_path / "subtitles.jsonl")

    repository.append_translation(
        TranslationResult(
            segment_id=7,
            source_text="hello",
            translated_text="hello translated",
            source_language="en",
            target_language="zh-TW",
            total_latency_ms=123.0,
        ),
        start_time=1.0,
        end_time=2.5,
    )

    entries = repository.list_entries()
    assert len(entries) == 1
    assert entries[0].segment_id == 7
    assert entries[0].translated_text == "hello translated"
    assert entries[0].start_time == 1.0


def test_subtitle_log_exports_txt_and_srt(tmp_path) -> None:
    repository = SubtitleLogRepository(tmp_path / "subtitles.jsonl")
    repository.append_translation(
        TranslationResult(
            segment_id=1,
            source_text="Miko starts",
            translated_text="Miko translated",
            source_language="ja",
            target_language="zh-TW",
            total_latency_ms=10.0,
        ),
        start_time=3.0,
        end_time=5.25,
    )

    txt_path = repository.export_txt(tmp_path / "subtitles.txt")
    srt_path = repository.export_srt(tmp_path / "subtitles.srt")

    assert "Miko starts" in txt_path.read_text(encoding="utf-8")
    srt_text = srt_path.read_text(encoding="utf-8")
    assert "00:00:03,000 --> 00:00:05,250" in srt_text
    assert "Miko translated" in srt_text
