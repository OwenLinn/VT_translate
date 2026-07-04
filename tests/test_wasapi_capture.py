from __future__ import annotations

from array import array

import pytest

from yt_live_translator.audio import wasapi_capture


class FakeStream:
    def __init__(self) -> None:
        self.read_calls: list[int] = []
        self.closed = False

    def read(self, frames: int, exception_on_overflow: bool = False) -> bytes:
        self.read_calls.append(frames)
        samples = array("h")
        for _ in range(frames):
            samples.extend([1000, -1000])
        return samples.tobytes()

    def stop_stream(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True


class FakePyAudio:
    def __init__(self) -> None:
        self.stream = FakeStream()
        self.open_kwargs = None
        self.terminated = False
        self.default_device = {
            "index": 10,
            "name": "Fake Speakers [Loopback]",
            "maxInputChannels": 2,
            "defaultSampleRate": 1000.0,
            "isLoopbackDevice": True,
        }

    def get_default_wasapi_loopback(self):
        return self.default_device

    def get_loopback_device_info_generator(self):
        return iter([self.default_device])

    def get_device_info_by_index(self, index: int):
        assert index == 10
        return self.default_device

    def open(self, **kwargs):
        self.open_kwargs = kwargs
        return self.stream

    def terminate(self) -> None:
        self.terminated = True


class FakePyAudioModule:
    paInt16 = object()

    def __init__(self) -> None:
        self.instance = FakePyAudio()

    def PyAudio(self):
        return self.instance


def test_list_loopback_devices_uses_default_marker(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_module = FakePyAudioModule()
    monkeypatch.setattr(wasapi_capture, "_load_pyaudiowpatch", lambda: fake_module)

    devices = wasapi_capture.list_loopback_devices()

    assert len(devices) == 1
    assert devices[0].index == 10
    assert devices[0].is_default is True
    assert fake_module.instance.terminated is True


def test_capture_loopback_returns_target_format(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_module = FakePyAudioModule()
    monkeypatch.setattr(wasapi_capture, "_load_pyaudiowpatch", lambda: fake_module)

    result = wasapi_capture.capture_loopback(
        seconds=0.1,
        target_sample_rate=100,
        target_channels=1,
        chunk_ms=30,
    )

    assert result.device.index == 10
    assert result.native_sample_rate == 1000
    assert result.native_channels == 2
    assert result.captured_frames == 100
    assert result.silence_fallback_frames == 0
    assert result.audio.sample_rate == 100
    assert result.audio.channels == 1
    assert result.audio.frame_count == 10
    assert fake_module.instance.open_kwargs["input_device_index"] == 10
    assert fake_module.instance.stream.closed is True


def test_capture_loopback_fills_silence_when_no_frames_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_module = FakePyAudioModule()
    monkeypatch.setattr(wasapi_capture, "_load_pyaudiowpatch", lambda: fake_module)
    monkeypatch.setattr(wasapi_capture, "_read_stream_with_timeout", lambda *args, **kwargs: None)

    result = wasapi_capture.capture_loopback(
        seconds=0.01,
        target_sample_rate=100,
        target_channels=1,
        chunk_ms=10,
    )

    assert result.captured_frames == 0
    assert result.silence_fallback_frames == 10
    assert result.audio.frame_count == 1
