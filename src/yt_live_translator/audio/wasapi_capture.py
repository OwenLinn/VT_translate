"""Windows WASAPI loopback capture using PyAudioWPatch."""

from __future__ import annotations

import time
from dataclasses import dataclass
from queue import Queue
from threading import Thread
from typing import Any

from yt_live_translator.audio.resampler import PCM16Audio, convert_pcm16


class AudioCaptureError(RuntimeError):
    """Raised when loopback capture cannot start or complete."""


@dataclass(frozen=True)
class LoopbackDevice:
    index: int
    name: str
    channels: int
    sample_rate: int
    is_default: bool = False


@dataclass(frozen=True)
class CaptureResult:
    device: LoopbackDevice
    native_sample_rate: int
    native_channels: int
    captured_frames: int
    silence_fallback_frames: int
    elapsed_seconds: float
    audio: PCM16Audio


def list_loopback_devices() -> list[LoopbackDevice]:
    """Return available WASAPI loopback capture devices."""

    pyaudio_module = _load_pyaudiowpatch()
    audio = pyaudio_module.PyAudio()
    try:
        default_index = _device_index(audio.get_default_wasapi_loopback())
        return [
            _device_from_info(device_info, is_default=_device_index(device_info) == default_index)
            for device_info in audio.get_loopback_device_info_generator()
        ]
    finally:
        audio.terminate()


def capture_loopback(
    seconds: float,
    target_sample_rate: int,
    target_channels: int,
    chunk_ms: int,
    device_index: int | None = None,
) -> CaptureResult:
    """Capture system output audio and return target-format signed 16-bit PCM."""

    if seconds <= 0:
        raise ValueError("seconds must be greater than 0")
    if chunk_ms <= 0:
        raise ValueError("chunk_ms must be greater than 0")

    pyaudio_module = _load_pyaudiowpatch()
    audio = pyaudio_module.PyAudio()
    stream = None
    try:
        device_info = _select_loopback_device(audio, device_index)
        device = _device_from_info(device_info, is_default=device_index is None)
        native_sample_rate = device.sample_rate
        native_channels = device.channels
        frames_per_buffer = max(1, round(native_sample_rate * chunk_ms / 1000))
        target_native_frames = max(1, round(native_sample_rate * seconds))
        captured_native_frames = 0
        chunks: list[bytes] = []

        stream = audio.open(
            format=pyaudio_module.paInt16,
            channels=native_channels,
            rate=native_sample_rate,
            input=True,
            input_device_index=device.index,
            frames_per_buffer=frames_per_buffer,
        )

        start = time.perf_counter()
        while captured_native_frames < target_native_frames:
            frames_to_read = min(
                frames_per_buffer,
                target_native_frames - captured_native_frames,
            )
            data = _read_stream_with_timeout(
                stream,
                frames_to_read,
                timeout_seconds=max(1.0, chunk_ms / 1000 * 4),
            )
            if data is None:
                break
            chunks.append(data)
            captured_native_frames += frames_to_read
        elapsed_seconds = time.perf_counter() - start
        silence_fallback_frames = max(0, target_native_frames - captured_native_frames)
        if silence_fallback_frames:
            chunks.append(b"\x00" * silence_fallback_frames * native_channels * 2)

        converted_audio = convert_pcm16(
            pcm=b"".join(chunks),
            source_sample_rate=native_sample_rate,
            source_channels=native_channels,
            target_sample_rate=target_sample_rate,
            target_channels=target_channels,
        )
        return CaptureResult(
            device=device,
            native_sample_rate=native_sample_rate,
            native_channels=native_channels,
            captured_frames=captured_native_frames,
            silence_fallback_frames=silence_fallback_frames,
            elapsed_seconds=elapsed_seconds,
            audio=converted_audio,
        )
    except OSError as exc:
        raise AudioCaptureError(f"Failed to capture WASAPI loopback audio: {exc}") from exc
    finally:
        if stream is not None:
            stream.stop_stream()
            stream.close()
        audio.terminate()


def _load_pyaudiowpatch():
    try:
        import pyaudiowpatch
    except ImportError as exc:
        raise AudioCaptureError(
            "PyAudioWPatch is required for WASAPI loopback capture. "
            "Install it with: pip install pyaudiowpatch"
        ) from exc
    return pyaudiowpatch


def _read_stream_with_timeout(stream: Any, frames_to_read: int, timeout_seconds: float) -> bytes | None:
    result_queue: Queue[bytes | BaseException] = Queue(maxsize=1)

    def read_stream() -> None:
        try:
            result_queue.put(stream.read(frames_to_read, exception_on_overflow=False))
        except BaseException as exc:
            result_queue.put(exc)

    thread = Thread(target=read_stream, daemon=True)
    thread.start()
    thread.join(timeout_seconds)
    if thread.is_alive():
        return None

    result = result_queue.get()
    if isinstance(result, BaseException):
        raise result
    return result


def _select_loopback_device(audio: Any, device_index: int | None) -> dict[str, Any]:
    if device_index is None:
        return audio.get_default_wasapi_loopback()

    device_info = audio.get_device_info_by_index(device_index)
    if device_info.get("isLoopbackDevice"):
        return device_info

    try:
        return audio.get_wasapi_loopback_analogue_by_dict(device_info)
    except OSError as exc:
        raise AudioCaptureError(
            f"Device index {device_index} is not a WASAPI loopback device and no loopback analogue was found"
        ) from exc


def _device_from_info(device_info: dict[str, Any], is_default: bool) -> LoopbackDevice:
    channels = int(device_info.get("maxInputChannels") or device_info.get("maxOutputChannels") or 1)
    return LoopbackDevice(
        index=_device_index(device_info),
        name=str(device_info.get("name", "Unknown loopback device")),
        channels=max(1, channels),
        sample_rate=round(float(device_info.get("defaultSampleRate") or 44100)),
        is_default=is_default,
    )


def _device_index(device_info: dict[str, Any]) -> int:
    return int(device_info["index"])
