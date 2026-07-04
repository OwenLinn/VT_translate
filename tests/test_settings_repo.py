from __future__ import annotations

import pytest

from yt_live_translator.core.config import load_config
from yt_live_translator.storage.settings_repo import SettingsRepository, SettingsSnapshot


def test_settings_repository_saves_and_loads_values(tmp_path) -> None:
    config = load_config()
    repository = SettingsRepository(tmp_path / "settings.sqlite3")

    repository.save(
        SettingsSnapshot(
            target_language="zh-CN",
            source_language="ja",
            translation_font_size=40,
            source_font_size=18,
            translation_color="#AAFF00",
            source_color="#CCCCCC",
            background_opacity=0.7,
            asr_model="large-v3-turbo",
            asr_device="cuda",
            asr_compute_type="float16",
            asr_beam_size=2,
            deepseek_model="deepseek-v4-pro",
        )
    )

    loaded = SettingsRepository(tmp_path / "settings.sqlite3").load(config)

    assert loaded.target_language == "zh-CN"
    assert loaded.source_language == "ja"
    assert loaded.translation_font_size == 40
    assert loaded.deepseek_model == "deepseek-v4-pro"


def test_settings_repository_rejects_invalid_color(tmp_path) -> None:
    repository = SettingsRepository(tmp_path / "settings.sqlite3")

    with pytest.raises(ValueError, match="translation_color"):
        repository.save(
            SettingsSnapshot(
                target_language="zh-TW",
                source_language="auto",
                translation_font_size=32,
                source_font_size=20,
                translation_color="white",
                source_color="#CCCCCC",
                background_opacity=0.55,
                asr_model="tiny",
                asr_device="cpu",
                asr_compute_type="int8",
                asr_beam_size=1,
                deepseek_model="deepseek-v4-flash",
            )
        )
