from __future__ import annotations

import pytest

from yt_live_translator.audio.resampler import PCM16Audio
from yt_live_translator.audio.wasapi_capture import CaptureResult, LoopbackDevice
from yt_live_translator.core.config import load_config
from yt_live_translator.storage.glossary_repo import GlossaryRepository
from yt_live_translator.ui.overlay_pipeline_app import (
    OverlayPipelineOptions,
    _build_pipeline_config,
    _build_streaming_pipeline_config,
    _build_translator,
    _load_audio,
    _run_continuous_loopback_pipeline,
)


def test_build_translator_echo_mode_without_glossary() -> None:
    config = load_config()
    translator = _build_translator(
        config,
        OverlayPipelineOptions(translation_mode="echo", glossary_enabled=False),
    )

    assert translator("hello", "en", "zh-TW") == "[echo:zh-TW] hello"


def test_build_translator_echo_mode_applies_glossary(tmp_path) -> None:
    db_path = tmp_path / "glossary.sqlite3"
    GlossaryRepository(db_path).add_term(
        source="Miko",
        target_zh_tw="咪口",
        source_lang="ja",
    )
    config = load_config()
    translator = _build_translator(
        config,
        OverlayPipelineOptions(
            translation_mode="echo",
            glossary_db=str(db_path),
        ),
    )

    assert translator("Miko starts", "ja", "zh-TW") == "[echo:zh-TW] 咪口 starts"


def test_load_audio_requires_source() -> None:
    config = load_config()

    with pytest.raises(ValueError, match="Either audio_file or loopback_seconds"):
        _load_audio(config, OverlayPipelineOptions(audio_file=None, loopback_seconds=None))


def test_continuous_loopback_options_build_pipeline_config() -> None:
    config = load_config()
    options = OverlayPipelineOptions(
        continuous_loopback=True,
        loopback_chunk_seconds=4.0,
        max_loopback_chunks=2,
        max_segments=1,
    )

    pipeline_config = _build_pipeline_config(config, options)

    assert options.continuous_loopback is True
    assert options.loopback_chunk_seconds == 4.0
    assert options.max_loopback_chunks == 2
    assert pipeline_config.max_segments == 1


def test_streaming_pipeline_config_uses_language_overrides() -> None:
    config = load_config()
    streaming_config = _build_streaming_pipeline_config(
        config,
        OverlayPipelineOptions(
            source_language="ja",
            target_language="zh-TW",
            max_segments=3,
            streaming_strategy="local_agreement",
        ),
    )

    assert streaming_config.asr_tick_ms == config.streaming.ja.asr_tick_ms
    assert streaming_config.agreement.min_commit_tokens == config.streaming.ja.min_commit_tokens
    assert streaming_config.max_final_segments == 3


def test_continuous_loopback_skips_silence_fallback_chunks(monkeypatch, tmp_path) -> None:
    config = load_config()
    options = OverlayPipelineOptions(
        continuous_loopback=True,
        loopback_chunk_seconds=1.0,
        max_loopback_chunks=1,
        result_log=str(tmp_path / "continuous.log"),
    )
    capture_result = CaptureResult(
        device=LoopbackDevice(index=1, name="Test loopback", channels=2, sample_rate=44100),
        native_sample_rate=44100,
        native_channels=2,
        captured_frames=0,
        silence_fallback_frames=44100,
        elapsed_seconds=1.0,
        audio=PCM16Audio(pcm=b"\x00" * 16000 * 2, sample_rate=16000, channels=1),
    )
    statuses: list[str] = []

    monkeypatch.setattr(
        "yt_live_translator.ui.overlay_pipeline_app.capture_loopback",
        lambda **_kwargs: capture_result,
    )

    def fail_asr(_path):
        raise AssertionError("ASR should not run for silence fallback chunks")

    _run_continuous_loopback_pipeline(
        runtime_config=config,
        options=options,
        pipeline_config=_build_pipeline_config(config, options),
        streaming_config=_build_streaming_pipeline_config(config, options),
        asr=fail_asr,
        translate=lambda text, _source, _target: text,
        on_output=lambda *_args: None,
        on_streaming_event=lambda *_args: None,
        should_stop=lambda: False,
        update_status=statuses.append,
        subtitle_log=None,
    )

    assert "Skipping silent live audio chunk 1" in statuses
    assert "Skipping silent live audio chunk 1" in (tmp_path / "continuous.log").read_text(encoding="utf-8")
