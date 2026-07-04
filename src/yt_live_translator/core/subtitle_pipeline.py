"""Terminal-oriented subtitle pipeline for Stage 4 smoke tests."""

from __future__ import annotations

import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal

import numpy as np

from yt_live_translator.audio.resampler import PCM16Audio, write_wav
from yt_live_translator.core.models import ASRResult, SourceLanguage, TargetLanguage, TranslationResult
from yt_live_translator.speech.asr_faster_whisper import ASRFileResult, transcribe_file
from yt_live_translator.speech.segmenter import SegmenterConfig, segment_audio
from yt_live_translator.speech.streaming_agreement import LocalAgreement, LocalAgreementConfig
from yt_live_translator.speech.vad import EnergyVAD
from yt_live_translator.translate.final_subtitle_reviser import FinalSubtitleReviser


ASRCallable = Callable[[Path], ASRFileResult]
TranslateCallable = Callable[[str, SourceLanguage, TargetLanguage], str]
PipelineOutputCallback = Callable[["PipelineOutput"], None]
StreamingPipelineEventCallback = Callable[["StreamingPipelineEvent"], None]
PipelineStopCheck = Callable[[], bool]


@dataclass(frozen=True)
class PipelineConfig:
    source_language: SourceLanguage
    target_language: TargetLanguage
    vad_threshold: float
    segmenter: SegmenterConfig
    max_segments: int | None = None


@dataclass(frozen=True)
class PipelineOutput:
    asr: ASRResult
    translation: TranslationResult


@dataclass(frozen=True)
class StreamingPipelineConfig:
    source_language: SourceLanguage
    target_language: TargetLanguage
    asr_tick_ms: int
    rolling_window_sec: float
    overlap_sec: float
    agreement: LocalAgreementConfig
    enable_final_revision: bool = True
    max_final_segments: int | None = None
    silence_end_ms: int = 450
    silence_threshold: float = 0.005


@dataclass(frozen=True)
class StreamingPipelineEvent:
    kind: Literal["partial", "final"]
    asr: ASRResult
    translation: TranslationResult


def load_audio_file_as_pcm16(
    path: str | Path,
    sample_rate: int,
    channels: int = 1,
    max_duration_seconds: float | None = None,
) -> PCM16Audio:
    """Decode a local audio file to signed 16-bit PCM using faster-whisper's PyAV path."""

    if channels != 1:
        raise ValueError("Stage 4 file decoding currently supports mono output only")
    if max_duration_seconds is not None and max_duration_seconds <= 0:
        raise ValueError("max_duration_seconds must be greater than 0")

    try:
        from faster_whisper.audio import decode_audio
    except ImportError as exc:
        raise RuntimeError("faster-whisper is required to decode audio files") from exc

    samples = decode_audio(str(path), sampling_rate=sample_rate)
    if max_duration_seconds is not None:
        max_samples = round(sample_rate * max_duration_seconds)
        samples = samples[:max_samples]
    int16_samples = np.clip(samples, -1.0, 1.0)
    int16_samples = (int16_samples * 32767.0).astype("<i2")
    return PCM16Audio(pcm=int16_samples.tobytes(), sample_rate=sample_rate, channels=channels)


def run_terminal_pipeline_on_audio(
    audio: PCM16Audio,
    config: PipelineConfig,
    asr: ASRCallable,
    translate: TranslateCallable,
    on_output: PipelineOutputCallback | None = None,
    should_stop: PipelineStopCheck | None = None,
) -> list[PipelineOutput]:
    vad = EnergyVAD(threshold=config.vad_threshold)
    segments = segment_audio(audio=audio, vad=vad, config=config.segmenter)
    if config.max_segments is not None:
        segments = segments[: config.max_segments]

    outputs: list[PipelineOutput] = []
    with tempfile.TemporaryDirectory(prefix="ytlt_segments_") as temp_dir:
        temp_root = Path(temp_dir)
        for segment in segments:
            if should_stop is not None and should_stop():
                break
            segment_start = time.perf_counter()
            segment_path = temp_root / f"segment_{segment.segment_id:04d}.wav"
            write_wav(
                segment_path,
                PCM16Audio(
                    pcm=segment.pcm,
                    sample_rate=segment.sample_rate,
                    channels=1,
                ),
            )
            asr_result = asr(segment_path)
            source_text = asr_result.text.strip()
            if not source_text:
                continue

            translated_text = translate(
                source_text,
                config.source_language,
                config.target_language,
            )
            elapsed_latency_ms = (time.perf_counter() - segment_start) * 1000
            total_latency_ms = max(elapsed_latency_ms, asr_result.latency_ms)
            asr_model = ASRResult(
                segment_id=segment.segment_id,
                source_text=source_text,
                source_language=asr_result.language,
                start_time=segment.start_time,
                end_time=segment.end_time,
                asr_latency_ms=asr_result.latency_ms,
            )
            translation_model = TranslationResult(
                segment_id=segment.segment_id,
                source_text=source_text,
                translated_text=translated_text,
                source_language=asr_result.language,
                target_language=config.target_language,
                total_latency_ms=total_latency_ms,
            )
            output = PipelineOutput(asr=asr_model, translation=translation_model)
            outputs.append(output)
            if on_output is not None:
                on_output(output)
    return outputs


def run_streaming_pipeline_on_audio(
    audio: PCM16Audio,
    config: StreamingPipelineConfig,
    asr: ASRCallable,
    translate: TranslateCallable,
    on_event: StreamingPipelineEventCallback | None = None,
    should_stop: PipelineStopCheck | None = None,
) -> list[StreamingPipelineEvent]:
    if audio.channels != 1:
        raise ValueError("Streaming pipeline currently supports mono PCM16 audio only")
    if config.asr_tick_ms <= 0:
        raise ValueError("asr_tick_ms must be greater than 0")
    if config.rolling_window_sec <= 0:
        raise ValueError("rolling_window_sec must be greater than 0")

    sample_width = 2
    total_samples = len(audio.pcm) // sample_width
    duration_sec = total_samples / audio.sample_rate
    if duration_sec <= 0:
        return []

    tick_sec = config.asr_tick_ms / 1000.0
    window_sec = config.rolling_window_sec + max(0.0, config.overlap_sec)
    agreement = LocalAgreement(config.agreement)
    reviser = FinalSubtitleReviser(translate)
    events: list[StreamingPipelineEvent] = []
    final_count = 0
    tick_index = 0

    with tempfile.TemporaryDirectory(prefix="ytlt_streaming_") as temp_dir:
        temp_root = Path(temp_dir)
        current_end_sec = min(tick_sec, duration_sec)
        while current_end_sec <= duration_sec + 0.0001:
            if should_stop is not None and should_stop():
                break
            tick_index += 1
            tick_start = time.perf_counter()
            window_start_sec = max(0.0, current_end_sec - window_sec)
            window_audio = _slice_pcm16_audio(audio, window_start_sec, current_end_sec)
            if not window_audio.pcm:
                current_end_sec += tick_sec
                continue

            window_path = temp_root / f"stream_{tick_index:04d}.wav"
            write_wav(window_path, window_audio)
            asr_result = asr(window_path)
            hypothesis = asr_result.text.strip()
            if not hypothesis:
                current_end_sec += tick_sec
                continue

            update = agreement.update(
                hypothesis,
                now_sec=current_end_sec,
                silence_final=current_end_sec >= duration_sec
                or _has_recent_silence(audio, current_end_sec, config.silence_end_ms, config.silence_threshold),
            )
            source_language = _event_source_language(config.source_language, asr_result.language)
            if update.should_translate_partial and update.partial_text and not update.should_finalize:
                translated_text = translate(update.partial_text, config.source_language, config.target_language)
                event = _streaming_event(
                    kind="partial",
                    segment_id=tick_index,
                    source_text=update.partial_text,
                    translated_text=translated_text,
                    source_language=source_language,
                    target_language=config.target_language,
                    start_time=window_start_sec,
                    end_time=current_end_sec,
                    asr_latency_ms=asr_result.latency_ms,
                    tick_start=tick_start,
                )
                events.append(event)
                if on_event is not None:
                    on_event(event)

            if update.should_finalize and update.final_text:
                final_count += 1
                translated_text = (
                    reviser.revise(
                        source_text=update.final_text,
                        source_language=config.source_language,
                        target_language=config.target_language,
                    ).translated_text
                    if config.enable_final_revision
                    else translate(update.final_text, config.source_language, config.target_language)
                )
                event = _streaming_event(
                    kind="final",
                    segment_id=final_count,
                    source_text=update.final_text,
                    translated_text=translated_text,
                    source_language=source_language,
                    target_language=config.target_language,
                    start_time=window_start_sec,
                    end_time=current_end_sec,
                    asr_latency_ms=asr_result.latency_ms,
                    tick_start=tick_start,
                )
                events.append(event)
                if on_event is not None:
                    on_event(event)
                agreement.mark_finalized()
                if config.max_final_segments is not None and final_count >= config.max_final_segments:
                    break

            current_end_sec += tick_sec
            if current_end_sec > duration_sec and current_end_sec - duration_sec < tick_sec:
                current_end_sec = duration_sec
    return events


def _slice_pcm16_audio(audio: PCM16Audio, start_sec: float, end_sec: float) -> PCM16Audio:
    sample_width = 2
    start_sample = max(0, round(start_sec * audio.sample_rate))
    end_sample = max(start_sample, round(end_sec * audio.sample_rate))
    return PCM16Audio(
        pcm=audio.pcm[start_sample * sample_width : end_sample * sample_width],
        sample_rate=audio.sample_rate,
        channels=audio.channels,
    )


def _has_recent_silence(
    audio: PCM16Audio,
    end_sec: float,
    silence_end_ms: int,
    threshold: float,
) -> bool:
    if silence_end_ms <= 0:
        return False
    silence_sec = silence_end_ms / 1000.0
    start_sec = max(0.0, end_sec - silence_sec)
    recent = _slice_pcm16_audio(audio, start_sec, end_sec)
    if not recent.pcm:
        return False
    samples = np.frombuffer(recent.pcm, dtype="<i2").astype(np.float32)
    if samples.size == 0:
        return False
    rms = float(np.sqrt(np.mean(np.square(samples / 32768.0))))
    return rms <= threshold


def _streaming_event(
    *,
    kind: Literal["partial", "final"],
    segment_id: int,
    source_text: str,
    translated_text: str,
    source_language: str,
    target_language: TargetLanguage,
    start_time: float,
    end_time: float,
    asr_latency_ms: float,
    tick_start: float,
) -> StreamingPipelineEvent:
    elapsed_latency_ms = (time.perf_counter() - tick_start) * 1000
    asr_model = ASRResult(
        segment_id=segment_id,
        source_text=source_text,
        source_language=source_language,
        start_time=start_time,
        end_time=end_time,
        asr_latency_ms=asr_latency_ms,
    )
    translation_model = TranslationResult(
        segment_id=segment_id,
        source_text=source_text,
        translated_text=translated_text,
        source_language=source_language,
        target_language=target_language,
        total_latency_ms=max(elapsed_latency_ms, asr_latency_ms),
    )
    return StreamingPipelineEvent(kind=kind, asr=asr_model, translation=translation_model)


def _event_source_language(config_language: SourceLanguage, detected_language: str) -> str:
    if detected_language:
        return detected_language
    return config_language
