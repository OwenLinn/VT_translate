from __future__ import annotations

from pathlib import Path

import pytest

from yt_live_translator.core.config import ConfigError, load_config, parse_config


def test_load_config_falls_back_to_example() -> None:
    config = load_config()

    assert config.source_path.name == "config.example.toml"
    assert config.app.target_language == "zh-TW"
    assert config.app.source_language == "auto"
    assert config.deepseek.api_key_env == "DEEPSEEK_API_KEY"
    assert config.deepseek.api_key is None
    assert config.ui.overlay_frontend == "qml"
    assert config.asr.model == "models/faster-whisper-large-v3"
    assert config.overlay.glass.enabled is True
    assert config.overlay.animation.enabled is True
    assert config.overlay.native_effect.enabled is False
    assert config.streaming.enabled is True
    assert config.streaming.strategy == "local_agreement"
    assert config.streaming.en.asr_tick_ms == 800
    assert config.streaming.ja.silence_end_ms == 450
    assert config.qml_overlay.width == 900
    assert config.qml_overlay.subtitle.translation_font_size == 30
    assert config.qml_overlay.glass.iridescence_enabled is True


def test_env_api_key_takes_priority(monkeypatch: pytest.MonkeyPatch) -> None:
    raw_config = _minimal_raw_config()
    raw_config["deepseek"]["api_key"] = "config-key"
    raw_config["deepseek"]["api_key_env"] = "TEST_DEEPSEEK_KEY"
    monkeypatch.setenv("TEST_DEEPSEEK_KEY", "env-key")

    config = parse_config(raw_config, Path("config.toml"))

    assert config.resolve_deepseek_api_key() == "env-key"


def test_config_api_key_used_when_env_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    raw_config = _minimal_raw_config()
    raw_config["deepseek"]["api_key"] = "config-key"
    raw_config["deepseek"]["api_key_env"] = "TEST_DEEPSEEK_KEY"
    monkeypatch.delenv("TEST_DEEPSEEK_KEY", raising=False)

    config = parse_config(raw_config, Path("config.toml"))

    assert config.resolve_deepseek_api_key() == "config-key"


def test_deepseek_model_can_be_flash_or_pro() -> None:
    raw_config = _minimal_raw_config()
    raw_config["deepseek"]["model"] = "deepseek-v4-pro"

    config = parse_config(raw_config, Path("config.toml"))

    assert config.deepseek.model == "deepseek-v4-pro"


def test_invalid_deepseek_model_is_clear() -> None:
    raw_config = _minimal_raw_config()
    raw_config["deepseek"]["model"] = "deepseek-chat"

    with pytest.raises(ConfigError, match="deepseek.model"):
        parse_config(raw_config, Path("config.toml"))


def test_invalid_target_language_is_clear() -> None:
    raw_config = _minimal_raw_config()
    raw_config["app"]["target_language"] = "fr"

    with pytest.raises(ConfigError, match="target_language"):
        parse_config(raw_config, Path("config.toml"))


def test_overlay_glass_and_animation_defaults_are_optional() -> None:
    config = parse_config(_minimal_raw_config(), Path("config.toml"))

    assert config.ui.overlay_frontend == "widgets"
    assert config.overlay.glass.enabled is False
    assert config.overlay.glass.corner_radius == 28
    assert config.overlay.animation.fade_duration_ms == 160
    assert config.overlay.native_effect.effect == "none"
    assert config.streaming.enabled is False
    assert config.streaming.local_agreement_n == 2
    assert config.streaming.en.min_commit_tokens == 5
    assert config.qml_overlay.width == 900
    assert config.qml_overlay.subtitle.show_source is True
    assert config.qml_overlay.subtitle.translation_font_size == 32


def test_qml_overlay_values_are_loaded() -> None:
    raw_config = _minimal_raw_config()
    raw_config["ui"] = {"overlay_frontend": "qml"}
    raw_config["qml_overlay"] = {
        "width": 960,
        "height": 104,
        "x": 320,
        "y": 120,
        "always_on_top": False,
        "frameless": True,
        "transparent_background": True,
        "show_settings_icon": False,
        "subtitle": {
            "show_source": False,
            "show_translation": True,
            "translation_font_size": 34,
            "source_font_size": 16,
            "font_family": "Test Font",
            "translation_color": "#EEEEEE",
            "source_color": "#CCCCCC",
            "text_shadow_opacity": 0.4,
            "max_translation_lines": 3,
            "max_source_lines": 1,
        },
        "glass": {
            "enabled": True,
            "subtitle_background_opacity": 0.6,
            "card_background_opacity": 0.5,
            "corner_radius": 26,
            "card_corner_radius": 28,
            "border_opacity": 0.2,
            "highlight_opacity": 0.3,
            "shadow_opacity": 0.25,
            "shadow_radius": 24,
            "iridescence_enabled": False,
            "iridescence_opacity": 0.1,
            "iridescence_width": 1.5,
            "noise_opacity": 0.01,
        },
        "animation": {
            "enabled": False,
            "subtitle_fade_ms": 100,
            "card_open_ms": 150,
            "card_close_ms": 120,
            "popover_open_ms": 130,
            "popover_close_ms": 110,
            "slide_offset_px": 10,
            "scale_from": 0.97,
            "scale_to": 1.0,
        },
    }

    config = parse_config(raw_config, Path("config.toml"))

    assert config.ui.overlay_frontend == "qml"
    assert config.qml_overlay.width == 960
    assert config.qml_overlay.always_on_top is False
    assert config.qml_overlay.show_settings_icon is False
    assert config.qml_overlay.subtitle.font_family == "Test Font"
    assert config.qml_overlay.subtitle.show_source is False
    assert config.qml_overlay.glass.card_background_opacity == 0.5
    assert config.qml_overlay.glass.iridescence_enabled is False
    assert config.qml_overlay.animation.enabled is False


def test_invalid_overlay_frontend_is_clear() -> None:
    raw_config = _minimal_raw_config()
    raw_config["ui"] = {"overlay_frontend": "native"}

    with pytest.raises(ConfigError, match="overlay_frontend"):
        parse_config(raw_config, Path("config.toml"))


def test_overlay_glass_and_animation_values_are_loaded() -> None:
    raw_config = _minimal_raw_config()
    raw_config["overlay"]["glass"] = {
        "enabled": True,
        "corner_radius": 30,
        "background_opacity": 0.4,
        "border_opacity": 0.3,
        "highlight_opacity": 0.2,
        "shadow_opacity": 0.25,
        "shadow_blur_radius": 24,
        "noise_opacity": 0.01,
    }
    raw_config["overlay"]["animation"] = {
        "enabled": False,
        "fade_duration_ms": 100,
        "slide_offset_px": 6,
        "drag_scale": 0.99,
    }

    config = parse_config(raw_config, Path("config.toml"))

    assert config.overlay.glass.enabled is True
    assert config.overlay.glass.corner_radius == 30
    assert config.overlay.animation.enabled is False
    assert config.overlay.animation.drag_scale == 0.99


def test_streaming_values_are_loaded() -> None:
    raw_config = _minimal_raw_config()
    raw_config["streaming"] = {
        "enabled": True,
        "strategy": "local_agreement",
        "asr_tick_ms": 900,
        "rolling_window_sec": 7,
        "overlap_sec": 0.8,
        "local_agreement_n": 3,
        "min_commit_sec": 1.0,
        "max_commit_sec": 2.6,
        "max_unconfirmed_sec": 3.2,
        "enable_partial_subtitle": False,
        "enable_final_revision": True,
        "en": {
            "asr_tick_ms": 700,
            "min_commit_tokens": 4,
            "max_commit_sec": 2.2,
            "silence_end_ms": 320,
        },
        "ja": {
            "asr_tick_ms": 950,
            "min_commit_tokens": 7,
            "max_commit_sec": 3.2,
            "silence_end_ms": 430,
        },
    }

    config = parse_config(raw_config, Path("config.toml"))

    assert config.streaming.enabled is True
    assert config.streaming.asr_tick_ms == 900
    assert config.streaming.local_agreement_n == 3
    assert config.streaming.enable_partial_subtitle is False
    assert config.streaming.en.min_commit_tokens == 4
    assert config.streaming.ja.max_commit_sec == 3.2


def _minimal_raw_config() -> dict:
    return {
        "app": {
            "target_language": "zh-TW",
            "source_language": "auto",
            "mode": "balanced",
        },
        "deepseek": {
            "api_key_env": "DEEPSEEK_API_KEY",
            "model": "deepseek-v4-flash",
            "base_url": "https://api.deepseek.com",
            "timeout_seconds": 10,
        },
        "asr": {
            "backend": "faster-whisper",
            "model": "large-v3-turbo",
            "device": "cuda",
            "compute_type": "float16",
            "beam_size": 3,
        },
        "audio": {
            "sample_rate": 16000,
            "channels": 1,
            "chunk_ms": 30,
        },
        "vad": {
            "threshold": 0.5,
            "min_speech_ms": 1200,
            "max_speech_ms": 5000,
            "silence_end_ms": 700,
            "padding_ms": 400,
        },
        "overlay": {
            "show_source": True,
            "show_translation": True,
            "font_family": "Microsoft JhengHei",
            "translation_font_size": 32,
            "source_font_size": 20,
            "translation_color": "#FFFFFF",
            "source_color": "#DDDDDD",
            "background_color": "#000000",
            "background_opacity": 0.55,
            "always_on_top": True,
        },
        "storage": {
            "database_path": "data/app.sqlite3",
            "subtitle_log_path": "data/subtitle_log.jsonl",
        },
    }
