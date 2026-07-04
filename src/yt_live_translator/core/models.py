"""Shared data models for the translation pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


TargetLanguage = Literal["zh-TW", "zh-CN"]
SourceLanguage = Literal["auto", "en", "ja"]


@dataclass(frozen=True)
class AudioFrame:
    pcm: bytes
    sample_rate: int
    channels: int
    timestamp: float


@dataclass(frozen=True)
class SpeechSegment:
    segment_id: int
    audio_path: str | None
    pcm: bytes
    sample_rate: int
    start_time: float
    end_time: float


@dataclass(frozen=True)
class ASRResult:
    segment_id: int
    source_text: str
    source_language: str
    start_time: float
    end_time: float
    asr_latency_ms: float


@dataclass(frozen=True)
class TranslationResult:
    segment_id: int
    source_text: str
    translated_text: str
    source_language: str
    target_language: TargetLanguage
    total_latency_ms: float
