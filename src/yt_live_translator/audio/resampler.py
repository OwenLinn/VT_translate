"""Small PCM helpers for Stage 2 audio capture smoke tests."""

from __future__ import annotations

import wave
from array import array
from dataclasses import dataclass
from pathlib import Path


SAMPLE_WIDTH_BYTES = 2


@dataclass(frozen=True)
class PCM16Audio:
    pcm: bytes
    sample_rate: int
    channels: int

    @property
    def frame_count(self) -> int:
        if self.channels <= 0:
            return 0
        return len(self.pcm) // (SAMPLE_WIDTH_BYTES * self.channels)

    @property
    def duration_seconds(self) -> float:
        if self.sample_rate <= 0:
            return 0.0
        return self.frame_count / self.sample_rate


def convert_pcm16(
    pcm: bytes,
    source_sample_rate: int,
    source_channels: int,
    target_sample_rate: int,
    target_channels: int,
) -> PCM16Audio:
    """Convert little-endian signed 16-bit PCM to the requested rate/channels."""

    _validate_audio_shape(source_sample_rate, source_channels)
    _validate_audio_shape(target_sample_rate, target_channels)

    samples = array("h")
    samples.frombytes(pcm)
    if not _is_little_endian():
        samples.byteswap()

    source_frames = _split_channels(samples, source_channels)
    mono_samples = _downmix_to_mono(source_frames)
    resampled = _resample_linear(mono_samples, source_sample_rate, target_sample_rate)
    output_samples = _expand_channels(resampled, target_channels)

    if not _is_little_endian():
        output_samples.byteswap()

    return PCM16Audio(
        pcm=output_samples.tobytes(),
        sample_rate=target_sample_rate,
        channels=target_channels,
    )


def write_wav(path: str | Path, audio: PCM16Audio) -> None:
    """Write signed 16-bit PCM audio to a WAV file."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(audio.channels)
        wav_file.setsampwidth(SAMPLE_WIDTH_BYTES)
        wav_file.setframerate(audio.sample_rate)
        wav_file.writeframes(audio.pcm)


def _validate_audio_shape(sample_rate: int, channels: int) -> None:
    if sample_rate <= 0:
        raise ValueError("sample_rate must be greater than 0")
    if channels <= 0:
        raise ValueError("channels must be greater than 0")


def _is_little_endian() -> bool:
    return array("h", [1]).tobytes() == b"\x01\x00"


def _split_channels(samples: array, channels: int) -> list[tuple[int, ...]]:
    frame_count = len(samples) // channels
    frames = []
    for frame_index in range(frame_count):
        start = frame_index * channels
        frames.append(tuple(samples[start : start + channels]))
    return frames


def _downmix_to_mono(frames: list[tuple[int, ...]]) -> array:
    mono = array("h")
    for frame in frames:
        mono.append(int(sum(frame) / len(frame)))
    return mono


def _resample_linear(samples: array, source_rate: int, target_rate: int) -> array:
    if source_rate == target_rate:
        return array("h", samples)

    source_count = len(samples)
    if source_count == 0:
        return array("h")
    if source_count == 1:
        return array("h", [samples[0]])

    target_count = max(1, round(source_count * target_rate / source_rate))
    if target_count == 1:
        return array("h", [samples[0]])

    output = array("h")
    scale = (source_count - 1) / (target_count - 1)
    for output_index in range(target_count):
        source_position = output_index * scale
        left_index = int(source_position)
        right_index = min(left_index + 1, source_count - 1)
        fraction = source_position - left_index
        interpolated = samples[left_index] * (1.0 - fraction) + samples[right_index] * fraction
        output.append(_clamp_int16(round(interpolated)))
    return output


def _expand_channels(samples: array, channels: int) -> array:
    if channels == 1:
        return array("h", samples)

    output = array("h")
    for sample in samples:
        output.extend([sample] * channels)
    return output


def _clamp_int16(value: int) -> int:
    return max(-32768, min(32767, value))
