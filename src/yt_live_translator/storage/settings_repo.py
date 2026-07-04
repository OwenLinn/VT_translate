"""Persist user-editable runtime settings in SQLite."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from yt_live_translator.core.config import DEEPSEEK_MODELS, RuntimeConfig
from yt_live_translator.core.models import SourceLanguage, TargetLanguage
from yt_live_translator.storage.db import connect_database, initialize_database


@dataclass(frozen=True)
class SettingsSnapshot:
    target_language: TargetLanguage
    source_language: SourceLanguage
    translation_font_size: int
    source_font_size: int
    translation_color: str
    source_color: str
    background_opacity: float
    asr_model: str
    asr_device: str
    asr_compute_type: str
    asr_beam_size: int
    deepseek_model: str


class SettingsRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        with connect_database(self.database_path) as connection:
            initialize_database(connection)

    def load(self, runtime_config: RuntimeConfig) -> SettingsSnapshot:
        snapshot = snapshot_from_runtime_config(runtime_config)
        values = self._read_all()
        for key, value in values.items():
            snapshot = _apply_value(snapshot, key, value)
        return snapshot

    def save(self, snapshot: SettingsSnapshot) -> None:
        _validate_snapshot(snapshot)
        now = datetime.now(UTC).isoformat(timespec="seconds")
        payload = asdict(snapshot)
        with connect_database(self.database_path) as connection:
            initialize_database(connection)
            connection.executemany(
                """
                INSERT INTO app_settings(key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                  value = excluded.value,
                  updated_at = excluded.updated_at
                """,
                [(key, json.dumps(value), now) for key, value in payload.items()],
            )
            connection.commit()

    def _read_all(self) -> dict[str, Any]:
        with connect_database(self.database_path) as connection:
            initialize_database(connection)
            rows = connection.execute("SELECT key, value FROM app_settings").fetchall()
        values = {}
        for row in rows:
            values[row["key"]] = json.loads(row["value"])
        return values


def snapshot_from_runtime_config(runtime_config: RuntimeConfig) -> SettingsSnapshot:
    return SettingsSnapshot(
        target_language=runtime_config.app.target_language,
        source_language=runtime_config.app.source_language,
        translation_font_size=runtime_config.overlay.translation_font_size,
        source_font_size=runtime_config.overlay.source_font_size,
        translation_color=runtime_config.overlay.translation_color,
        source_color=runtime_config.overlay.source_color,
        background_opacity=runtime_config.overlay.background_opacity,
        asr_model=runtime_config.asr.model,
        asr_device=runtime_config.asr.device,
        asr_compute_type=runtime_config.asr.compute_type,
        asr_beam_size=runtime_config.asr.beam_size,
        deepseek_model=runtime_config.deepseek.model,
    )


def _apply_value(snapshot: SettingsSnapshot, key: str, value: Any) -> SettingsSnapshot:
    if key not in SettingsSnapshot.__dataclass_fields__:
        return snapshot
    candidate = replace(snapshot, **{key: value})
    _validate_snapshot(candidate)
    return candidate


def _validate_snapshot(snapshot: SettingsSnapshot) -> None:
    if snapshot.target_language not in ("zh-TW", "zh-CN"):
        raise ValueError("target_language must be zh-TW or zh-CN")
    if snapshot.source_language not in ("auto", "en", "ja"):
        raise ValueError("source_language must be auto, en, or ja")
    if snapshot.translation_font_size < 8 or snapshot.translation_font_size > 96:
        raise ValueError("translation_font_size must be between 8 and 96")
    if snapshot.source_font_size < 8 or snapshot.source_font_size > 72:
        raise ValueError("source_font_size must be between 8 and 72")
    if not _is_hex_color(snapshot.translation_color):
        raise ValueError("translation_color must be a #RRGGBB color")
    if not _is_hex_color(snapshot.source_color):
        raise ValueError("source_color must be a #RRGGBB color")
    if snapshot.background_opacity < 0.0 or snapshot.background_opacity > 1.0:
        raise ValueError("background_opacity must be between 0 and 1")
    if snapshot.asr_beam_size < 1 or snapshot.asr_beam_size > 10:
        raise ValueError("asr_beam_size must be between 1 and 10")
    if snapshot.deepseek_model not in DEEPSEEK_MODELS:
        raise ValueError("deepseek_model must be deepseek-v4-flash or deepseek-v4-pro")


def _is_hex_color(value: str) -> bool:
    if len(value) != 7 or not value.startswith("#"):
        return False
    try:
        int(value[1:], 16)
    except ValueError:
        return False
    return True
