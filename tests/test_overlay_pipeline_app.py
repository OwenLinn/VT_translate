from __future__ import annotations

import pytest

from yt_live_translator.core.config import load_config
from yt_live_translator.storage.glossary_repo import GlossaryRepository
from yt_live_translator.ui.overlay_pipeline_app import (
    OverlayPipelineOptions,
    _build_pipeline_config,
    _build_streaming_pipeline_config,
    _build_translator,
    _load_audio,
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
