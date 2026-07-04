"""Small-frame WASAPI loopback streaming generator.

Provides a generator that yields short PCM16Audio frames (~250 ms) from the
system audio output, suitable for feeding into ``StreamingAsrSession.push_audio``.
"""

from __future__ import annotations

import time
from typing import Callable, Iterator

import pyaudiowpatch as pyaudio

from yt_live_translator.audio.resampler import PCM16Audio, convert_pcm16
from yt_live_translator.audio.wasapi_capture import list_loopback_devices


def _default_loopback_device_index() -> int | None:
    devices = list_loopback_devices()
    for device in devices:
        if device.is_default:
            return device.index
    return devices[0].index if devices else None


def stream_loopback_frames(
    *,
    frame_ms: int = 250,
    sample_rate: int = 16000,
    channels: int = 1,
    device_index: int | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> Iterator[PCM16Audio]:
    """Yield small PCM16Audio frames from the default WASAPI loopback device.

    Each yielded frame has the requested ``sample_rate`` and ``channels``.
    The generator continues until ``should_stop`` returns ``True`` or the
    stream is closed.

    Parameters
    ----------
    frame_ms:
        Duration of each yielded frame in milliseconds (default 250).
    sample_rate:
        Target sample rate (default 16000).
    channels:
        Target channel count (default 1, mono).
    device_index:
        PyAudio device index. If ``None``, uses the default loopback device.
    should_stop:
        Optional callable; when it returns ``True`` the generator stops.
    """
    if device_index is None:
        device_index = _default_loopback_device_index()
        if device_index is None:
            raise RuntimeError("No WASAPI loopback device found")

    audio = pyaudio.PyAudio()
    try:
        device_info = audio.get_device_info_by_index(device_index)
        native_rate = int(device_info["defaultSampleRate"])
        native_channels = int(device_info["maxInputChannels"])
        frames_per_buffer = max(1, round(native_rate * frame_ms / 1000))
        target_frames = round(sample_rate * frame_ms / 1000)

        stream = audio.open(
            format=pyaudio.paInt16,
            channels=native_channels,
            rate=native_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=frames_per_buffer,
        )
        try:
            while should_stop is None or not should_stop():
                try:
                    raw = stream.read(frames_per_buffer, exception_on_overflow=False)
                except OSError:
                    break
                converted = convert_pcm16(
                    bytes(raw),
                    source_sample_rate=native_rate,
                    source_channels=native_channels,
                    target_sample_rate=sample_rate,
                    target_channels=channels,
                )
                if converted.frame_count >= target_frames:
                    yield converted
        finally:
            stream.stop_stream()
            stream.close()
    finally:
        audio.terminate()
