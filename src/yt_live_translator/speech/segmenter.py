"""PCM speech segmentation for terminal pipeline smoke tests."""

from __future__ import annotations

from dataclasses import dataclass

from yt_live_translator.audio.resampler import PCM16Audio, SAMPLE_WIDTH_BYTES
from yt_live_translator.core.models import SpeechSegment
from yt_live_translator.speech.vad import EnergyVAD


@dataclass(frozen=True)
class SegmenterConfig:
    frame_ms: int = 30
    min_speech_ms: int = 1200
    max_speech_ms: int = 5000
    silence_end_ms: int = 700
    padding_ms: int = 400


def segment_audio(audio: PCM16Audio, vad: EnergyVAD, config: SegmenterConfig) -> list[SpeechSegment]:
    if audio.channels != 1:
        raise ValueError("segment_audio expects mono PCM16 audio")
    if config.frame_ms <= 0:
        raise ValueError("frame_ms must be greater than 0")

    frame_samples = max(1, round(audio.sample_rate * config.frame_ms / 1000))
    frame_bytes = frame_samples * SAMPLE_WIDTH_BYTES
    min_speech_frames = max(1, round(config.min_speech_ms / config.frame_ms))
    max_speech_frames = max(1, round(config.max_speech_ms / config.frame_ms))
    silence_end_frames = max(1, round(config.silence_end_ms / config.frame_ms))
    padding_frames = max(0, round(config.padding_ms / config.frame_ms))

    frames = _split_frames(audio.pcm, frame_bytes)
    segments: list[SpeechSegment] = []
    active_start: int | None = None
    active_end = 0
    silence_count = 0

    for frame_index, frame in enumerate(frames):
        is_speech = vad.analyze(frame).is_speech
        if is_speech:
            if active_start is None:
                active_start = max(0, frame_index - padding_frames)
            active_end = frame_index + 1
            silence_count = 0
        elif active_start is not None:
            silence_count += 1
            if silence_count <= padding_frames:
                active_end = frame_index + 1

        if active_start is None:
            continue

        active_frame_count = frame_index - active_start + 1
        should_close = silence_count >= silence_end_frames or active_frame_count >= max_speech_frames
        if should_close:
            _append_segment_if_long_enough(
                segments=segments,
                frames=frames,
                start_frame=active_start,
                end_frame=active_end,
                min_speech_frames=min_speech_frames,
                sample_rate=audio.sample_rate,
                frame_samples=frame_samples,
            )
            active_start = None
            active_end = 0
            silence_count = 0

    if active_start is not None:
        _append_segment_if_long_enough(
            segments=segments,
            frames=frames,
            start_frame=active_start,
            end_frame=active_end,
            min_speech_frames=min_speech_frames,
            sample_rate=audio.sample_rate,
            frame_samples=frame_samples,
        )

    return segments


def _split_frames(pcm: bytes, frame_bytes: int) -> list[bytes]:
    return [pcm[index : index + frame_bytes] for index in range(0, len(pcm), frame_bytes)]


def _append_segment_if_long_enough(
    segments: list[SpeechSegment],
    frames: list[bytes],
    start_frame: int,
    end_frame: int,
    min_speech_frames: int,
    sample_rate: int,
    frame_samples: int,
) -> None:
    if end_frame <= start_frame:
        return
    if end_frame - start_frame < min_speech_frames:
        return

    pcm = b"".join(frames[start_frame:end_frame])
    start_time = start_frame * frame_samples / sample_rate
    end_time = start_time + (end_frame - start_frame) * frame_samples / sample_rate
    segments.append(
        SpeechSegment(
            segment_id=len(segments) + 1,
            audio_path=None,
            pcm=pcm,
            sample_rate=sample_rate,
            start_time=start_time,
            end_time=end_time,
        )
    )
