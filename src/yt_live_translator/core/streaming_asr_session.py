"""True Streaming ASR v1 -- persistent ring buffer + persistent LocalAgreement.

This module provides a continuous ASR session that:
- Maintains a persistent PCM ring buffer (~7 seconds).
- Maintains a persistent LocalAgreement across the entire live session.
- Runs ASR ticks every ``asr_tick_ms`` over a rolling ``asr_window_seconds`` window.
- Skips ticks when the previous ASR call is still running.
- Applies deduplication on final and partial outputs.
- Uses absolute time offsets so events span the whole session.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal

from yt_live_translator.audio.resampler import PCM16Audio
from yt_live_translator.core.models import SourceLanguage
from yt_live_translator.speech.asr_faster_whisper import ASRFileResult, FasterWhisperTranscriber
from yt_live_translator.speech.streaming_agreement import (
    AgreementUpdate,
    LocalAgreement,
    LocalAgreementConfig,
)


@dataclass
class StreamingAsrEvent:
    """Lightweight ASR-only event emitted by StreamingAsrSession."""

    kind: Literal["partial", "final"]
    source_text: str
    raw_source_text: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    is_partial: bool = False
    asr_latency_ms: float = 0.0
    tick_index: int = 0
    segment_id: int = 0
    overlap_chars: int = 0
    skipped: bool = False
    skipped_reason: str = ""

    @property
    def cleaned_text(self) -> str:
        return self.source_text


@dataclass
class StreamingAsrConfig:
    """Configuration for the StreamingAsrSession."""

    source_language: SourceLanguage = "auto"
    asr_window_seconds: float = 6.0
    asr_tick_ms: int = 1000
    capture_frame_ms: int = 250
    beam_size: int = 3
    agreement_n: int = 2
    overlap_margin_seconds: float = 1.0


def _audio_path_for_tick(temp_dir: Path, tick_index: int) -> Path:
    return temp_dir / f"streaming_asr_{tick_index:06d}.wav"


class StreamingAsrSession:
    """Persistent streaming ASR with ring buffer and single LocalAgreement.

    Usage::

        session = StreamingAsrSession(transcriber=..., source_language="ja", ...)
        for frame in stream_loopback_frames(...):
            events = session.push_audio(frame, absolute_start_sec=...)
            for event in events:
                print(event.source_text)
        final_events = session.flush()
    """

    def __init__(
        self,
        *,
        transcriber: FasterWhisperTranscriber,
        source_language: SourceLanguage = "auto",
        sample_rate: int = 16000,
        channels: int = 1,
        asr_window_seconds: float = 6.0,
        asr_tick_ms: int = 1000,
        capture_frame_ms: int = 250,
        agreement_config: LocalAgreementConfig | None = None,
        beam_size: int = 3,
        temp_dir: Path | None = None,
        enable_output_cleanup: bool = True,
    ) -> None:
        self._transcriber = transcriber
        self._sample_rate = sample_rate
        self._channels = channels
        self._asr_window_seconds = asr_window_seconds
        self._asr_tick_ms = asr_tick_ms
        self._capture_frame_ms = capture_frame_ms
        self._beam_size = beam_size
        self._enable_output_cleanup = enable_output_cleanup

        self._ring_buffer: deque[tuple[bytes, float]] = deque()
        self._absolute_end_sec: float = 0.0
        self._ring_duration_sec: float = asr_window_seconds + 1.0
        self._bytes_per_second: int = sample_rate * channels * 2

        self._agreement = LocalAgreement(
            config=agreement_config or self._default_agreement_config(source_language)
        )

        self._temp_dir = temp_dir or Path("work")
        self._temp_dir.mkdir(parents=True, exist_ok=True)

        self._tick_index: int = 0
        self._last_tick_end_sec: float = 0.0
        self._asr_running: bool = False
        self._segment_id_counter: int = 0

        self._recent_final_texts: deque[str] = deque(maxlen=8)
        self._recent_partial_texts: deque[str] = deque(maxlen=8)
        self._last_emitted_source_text: str = ""

        self._source_language = source_language

        self._stats: dict[str, Any] = {
            "tick_count": 0,
            "asr_latencies_ms": [],
            "dedupe_count": 0,
            "partial_count": 0,
            "final_count": 0,
            "skip_count": 0,
            "overlap_trim_count": 0,
        }

    def _default_agreement_config(self, source_language: SourceLanguage) -> LocalAgreementConfig:
        return LocalAgreementConfig(
            source_language=source_language,
            agreement_n=2,
            min_commit_sec=1.2,
            max_commit_sec=3.0,
            max_unconfirmed_sec=4.0,
            min_commit_tokens=8 if source_language == "ja" else 5,
            enable_partial_subtitle=True,
            enable_final_revision=False,
        )

    @property
    def stats(self) -> dict[str, Any]:
        return dict(self._stats)

    @property
    def absolute_end_sec(self) -> float:
        return self._absolute_end_sec

    def push_audio(
        self,
        audio: PCM16Audio,
        *,
        absolute_start_sec: float | None = None,
    ) -> list[StreamingAsrEvent]:
        """Push a small PCM chunk into the ring buffer.

        If this push crosses an ASR tick boundary, run an ASR tick.
        Returns any StreamingAsrEvent produced during this push.
        """
        if absolute_start_sec is not None:
            chunk_end = absolute_start_sec + audio.duration_seconds
        else:
            chunk_end = self._absolute_end_sec + audio.duration_seconds

        self._ring_buffer.append((audio.pcm, chunk_end))
        self._absolute_end_sec = chunk_end
        self._trim_ring_buffer()

        events: list[StreamingAsrEvent] = []
        tick_sec = self._asr_tick_ms / 1000.0

        while self._absolute_end_sec >= self._last_tick_end_sec + tick_sec:
            target_tick_end = self._last_tick_end_sec + tick_sec
            if target_tick_end > self._absolute_end_sec:
                break

            if self._asr_running:
                self._stats["skip_count"] += 1
                self._last_tick_end_sec = target_tick_end
                continue

            tick_events = self._run_asr_tick(target_tick_end)
            events.extend(tick_events)
            self._last_tick_end_sec = target_tick_end

        return events

    def flush(self) -> list[StreamingAsrEvent]:
        """Force finalization of any remaining uncommitted text."""
        events: list[StreamingAsrEvent] = []

        if self._asr_running:
            return events

        window_audio = self._extract_window(self._absolute_end_sec)
        if window_audio is None or window_audio.frame_count == 0:
            return events

        asr_result = self._transcribe_window(window_audio, self._tick_index)
        self._tick_index += 1

        if asr_result and asr_result.text.strip():
            hypothesis = asr_result.text.strip()
            latency_ms = asr_result.latency_ms
            update = self._agreement.update(
                hypothesis,
                now_sec=self._absolute_end_sec,
                silence_final=True,
            )
            event = self._process_update(update, self._absolute_end_sec, latency_ms, force_final=True)
            if event:
                events.append(event)

        return events

    def reset(self) -> None:
        """Reset all session state."""
        self._ring_buffer.clear()
        self._absolute_end_sec = 0.0
        self._tick_index = 0
        self._last_tick_end_sec = 0.0
        self._asr_running = False
        self._segment_id_counter = 0
        self._recent_final_texts.clear()
        self._recent_partial_texts.clear()
        self._last_emitted_source_text = ""
        self._agreement = LocalAgreement(
            config=self._default_agreement_config(
                self._agreement.config.source_language
            )
        )
        self._stats = {
            "tick_count": 0,
            "asr_latencies_ms": [],
            "dedupe_count": 0,
            "partial_count": 0,
            "final_count": 0,
            "skip_count": 0,
            "overlap_trim_count": 0,
        }

    def _trim_ring_buffer(self) -> None:
        max_duration = self._ring_duration_sec
        while self._ring_buffer:
            _, end_sec = self._ring_buffer[0]
            if self._absolute_end_sec - end_sec > max_duration:
                self._ring_buffer.popleft()
            else:
                break

    def _extract_window(self, window_end_sec: float) -> PCM16Audio | None:
        window_start_sec = max(0.0, window_end_sec - self._asr_window_seconds)
        frames: list[bytes] = []
        earliest_sec: float | None = None
        latest_sec: float = window_end_sec

        for pcm, end_sec in self._ring_buffer:
            start_sec = end_sec - (len(pcm) / self._bytes_per_second)
            if end_sec <= window_start_sec:
                continue
            if start_sec >= window_end_sec:
                break

            chunk_frames = pcm
            if start_sec < window_start_sec:
                trim_start_samples = int((window_start_sec - start_sec) * self._sample_rate)
                trim_start_bytes = trim_start_samples * self._channels * 2
                chunk_frames = chunk_frames[trim_start_bytes:]
            if end_sec > window_end_sec:
                trim_end_samples = int((end_sec - window_end_sec) * self._sample_rate)
                trim_end_bytes = trim_end_samples * self._channels * 2
                chunk_frames = chunk_frames[: len(chunk_frames) - trim_end_bytes]

            if chunk_frames:
                if earliest_sec is None:
                    earliest_sec = max(start_sec, window_start_sec)
                frames.append(chunk_frames)

        if not frames:
            return None

        return PCM16Audio(
            pcm=b"".join(frames),
            sample_rate=self._sample_rate,
            channels=self._channels,
        )

    def _run_asr_tick(self, tick_end_sec: float) -> list[StreamingAsrEvent]:
        self._asr_running = True
        try:
            window_audio = self._extract_window(tick_end_sec)
            if window_audio is None or window_audio.frame_count == 0:
                return []

            asr_result = self._transcribe_window(window_audio, self._tick_index)
            self._stats["tick_count"] += 1
            self._tick_index += 1

            if asr_result is None or not asr_result.text.strip():
                return []

            hypothesis = asr_result.text.strip()
            latency_ms = asr_result.latency_ms
            self._stats["asr_latencies_ms"].append(latency_ms)

            update = self._agreement.update(
                hypothesis,
                now_sec=tick_end_sec,
            )

            event = self._process_update(update, tick_end_sec, latency_ms)
            return [event] if event else []
        finally:
            self._asr_running = False

    def _transcribe_window(
        self, window_audio: PCM16Audio, tick_index: int
    ) -> ASRFileResult | None:
        from yt_live_translator.audio.resampler import write_wav

        audio_path = _audio_path_for_tick(self._temp_dir, tick_index)
        write_wav(audio_path, window_audio)

        try:
            result = self._transcriber.transcribe(audio_path)
            return result
        finally:
            try:
                audio_path.unlink(missing_ok=True)
            except OSError:
                pass

    def _process_update(
        self,
        update: AgreementUpdate,
        tick_end_sec: float,
        asr_latency_ms: float,
        force_final: bool = False,
    ) -> StreamingAsrEvent | None:
        should_final = force_final or update.should_finalize
        should_partial = not should_final and update.should_translate_partial

        raw_text = ""
        if should_final and update.final_text:
            raw_text = update.final_text.strip()
        elif should_partial and update.partial_text:
            raw_text = update.partial_text.strip()

        if not raw_text:
            return None

        if should_final:
            return self._emit_final(raw_text, tick_end_sec, asr_latency_ms)

        return self._emit_partial(raw_text, tick_end_sec, asr_latency_ms)

    def _emit_final(
        self, raw_text: str, tick_end_sec: float, asr_latency_ms: float
    ) -> StreamingAsrEvent | None:
        if self._is_duplicate_final(raw_text):
            self._stats["dedupe_count"] += 1
            self._agreement.mark_finalized()
            return None

        cleaned, overlap = self._clean_overlap(raw_text)
        if not cleaned or len(cleaned) < 3:
            self._stats["dedupe_count"] += 1
            self._agreement.mark_finalized()
            return None

        self._recent_final_texts.append(cleaned)
        self._recent_partial_texts.append(cleaned)
        self._last_emitted_source_text = cleaned
        self._segment_id_counter += 1
        self._stats["final_count"] += 1
        if overlap > 0:
            self._stats["overlap_trim_count"] += 1
        self._agreement.mark_finalized()

        return StreamingAsrEvent(
            kind="final",
            source_text=cleaned,
            raw_source_text=raw_text,
            start_time=max(0.0, tick_end_sec - self._asr_window_seconds),
            end_time=tick_end_sec,
            is_partial=False,
            asr_latency_ms=asr_latency_ms,
            tick_index=self._tick_index,
            segment_id=self._segment_id_counter,
            overlap_chars=overlap,
        )

    def _emit_partial(
        self, raw_text: str, tick_end_sec: float, asr_latency_ms: float
    ) -> StreamingAsrEvent | None:
        if self._is_redundant_partial(raw_text):
            return None

        cleaned, overlap = self._clean_overlap(raw_text)
        if not cleaned:
            return None
        if len(cleaned) < 3 and overlap > 0:
            return None

        self._last_emitted_source_text = cleaned
        self._stats["partial_count"] += 1
        if overlap > 0:
            self._stats["overlap_trim_count"] += 1

        return StreamingAsrEvent(
            kind="partial",
            source_text=cleaned,
            raw_source_text=raw_text,
            start_time=max(0.0, tick_end_sec - self._asr_window_seconds),
            end_time=tick_end_sec,
            is_partial=True,
            asr_latency_ms=asr_latency_ms,
            tick_index=self._tick_index,
            segment_id=self._segment_id_counter + 1,
            overlap_chars=overlap,
        )

    def _clean_overlap(self, new_text: str) -> tuple[str, int]:
        if not self._enable_output_cleanup:
            return new_text, 0
        if not self._last_emitted_source_text:
            return new_text, 0
        return _trim_overlap(self._last_emitted_source_text, new_text, self._source_language)

    def _is_duplicate_final(self, text: str) -> bool:
        if text in self._recent_final_texts:
            return True
        if self._enable_output_cleanup and self._last_emitted_source_text:
            cleaned, _ = self._clean_overlap(text)
            if cleaned in self._recent_final_texts:
                return True
        return False

    def _is_redundant_partial(self, text: str) -> bool:
        if not self._last_emitted_source_text:
            return False
        if text == self._last_emitted_source_text:
            return True
        if text in self._last_emitted_source_text and len(text) <= len(self._last_emitted_source_text):
            return True
        if self._enable_output_cleanup:
            cleaned, overlap = self._clean_overlap(text)
            if overlap > 0 and (not cleaned or len(cleaned) < 3):
                return True
        return False


def _is_japanese_context(text: str, source_language: str) -> bool:
    if source_language == "ja":
        return True
    if source_language == "auto":
        for ch in text:
            cp = ord(ch)
            if 0x3040 <= cp <= 0x30FF or 0x4E00 <= cp <= 0x9FFF:
                return True
    return False


def _trim_overlap(last_text: str, new_text: str, source_language: str) -> tuple[str, int]:
    """Trim overlapping prefix from new_text based on suffix of last_text.

    For Japanese: character-level overlap detection, min 4 chars.
    For English: word-level overlap, min 3 words.

    Returns (cleaned_text, overlap_size).
    """
    if not last_text or not new_text:
        return new_text, 0

    is_ja = _is_japanese_context(last_text, source_language) or _is_japanese_context(new_text, source_language)

    if is_ja:
        return _trim_char_overlap(last_text, new_text, min_overlap=4)
    else:
        return _trim_word_overlap(last_text, new_text, min_overlap=3)


def _trim_char_overlap(last_text: str, new_text: str, min_overlap: int = 4) -> tuple[str, int]:
    """Find max character-level overlap: suffix of last_text matches prefix of new_text."""
    max_possible = min(len(last_text), len(new_text))
    best_overlap = 0

    for n in range(min_overlap, max_possible + 1):
        if last_text[-n:] == new_text[:n]:
            best_overlap = n

    if best_overlap >= min_overlap:
        cleaned = new_text[best_overlap:]
        return cleaned, best_overlap

    return new_text, 0


def _trim_word_overlap(last_text: str, new_text: str, min_overlap: int = 3) -> tuple[str, int]:
    """Find word-level overlap."""
    last_words = last_text.split()
    new_words = new_text.split()

    max_possible = min(len(last_words), len(new_words))
    best_overlap = 0

    for n in range(min_overlap, max_possible + 1):
        if last_words[-n:] == new_words[:n]:
            best_overlap = n

    if best_overlap >= min_overlap:
        cleaned = " ".join(new_words[best_overlap:])
        return cleaned, best_overlap

    return new_text, 0
