"""Subtitle history storage and export helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from yt_live_translator.core.config import RuntimeConfig, project_root
from yt_live_translator.core.models import TranslationResult


@dataclass(frozen=True)
class SubtitleLogEntry:
    segment_id: int
    source_text: str
    translated_text: str
    source_language: str
    target_language: str
    latency_ms: float
    created_at: str
    start_time: float | None = None
    end_time: float | None = None


class SubtitleLogRepository:
    def __init__(self, log_path: str | Path) -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: SubtitleLogEntry) -> None:
        with self.log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

    def append_translation(
        self,
        translation: TranslationResult,
        *,
        start_time: float | None = None,
        end_time: float | None = None,
    ) -> SubtitleLogEntry:
        entry = SubtitleLogEntry(
            segment_id=translation.segment_id,
            source_text=translation.source_text,
            translated_text=translation.translated_text,
            source_language=translation.source_language,
            target_language=translation.target_language,
            latency_ms=translation.total_latency_ms,
            start_time=start_time,
            end_time=end_time,
            created_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )
        self.append(entry)
        return entry

    def list_entries(self) -> list[SubtitleLogEntry]:
        if not self.log_path.exists():
            return []
        entries = []
        with self.log_path.open("r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                entries.append(SubtitleLogEntry(**json.loads(line)))
        return entries

    def export_txt(self, output_path: str | Path) -> Path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        for entry in self.list_entries():
            lines.append(f"[{entry.segment_id}] {entry.source_text}")
            lines.append(entry.translated_text)
            lines.append("")
        output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        return output

    def export_srt(self, output_path: str | Path) -> Path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        blocks = []
        for index, entry in enumerate(self.list_entries(), start=1):
            start = entry.start_time if entry.start_time is not None else float(index - 1) * 3.0
            end = entry.end_time if entry.end_time is not None else start + 3.0
            blocks.append(
                "\n".join(
                    [
                        str(index),
                        f"{_srt_time(start)} --> {_srt_time(end)}",
                        entry.translated_text,
                    ]
                )
            )
        output.write_text("\n\n".join(blocks) + ("\n" if blocks else ""), encoding="utf-8")
        return output


def resolve_subtitle_log_path(runtime_config: RuntimeConfig, override: str | Path | None = None) -> Path:
    raw_path = Path(override or runtime_config.storage.subtitle_log_path)
    if raw_path.is_absolute():
        return raw_path
    return project_root() / raw_path


def _srt_time(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
