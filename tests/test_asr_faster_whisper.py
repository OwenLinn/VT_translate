from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from yt_live_translator.speech.asr_faster_whisper import ASRError, FasterWhisperTranscriber, transcribe_file


@dataclass(frozen=True)
class FakeSegment:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class FakeInfo:
    language: str
    duration: float


class FakeWhisperModel:
    def __init__(self, model_size: str, device: str, compute_type: str) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.transcribe_calls = []

    def transcribe(self, audio_path: str, language: str | None, beam_size: int):
        self.transcribe_calls.append(
            {
                "audio_path": audio_path,
                "language": language,
                "beam_size": beam_size,
            }
        )
        return (
            [
                FakeSegment(start=0.0, end=1.0, text=" hello"),
                FakeSegment(start=1.0, end=2.0, text=" world "),
            ],
            FakeInfo(language=language or "en", duration=2.0),
        )


class FailingTranscribeModel(FakeWhisperModel):
    def transcribe(self, audio_path: str, language: str | None, beam_size: int):
        raise RuntimeError("CUDA runtime unavailable")


def test_transcribe_file_passes_language_and_model_options(tmp_path: Path) -> None:
    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"fake wav")
    models = []

    def factory(model_size: str, device: str, compute_type: str):
        model = FakeWhisperModel(model_size, device, compute_type)
        models.append(model)
        return model

    result = transcribe_file(
        audio_path=audio_path,
        language="ja",
        model_size="tiny",
        device="cpu",
        compute_type="int8",
        beam_size=5,
        model_factory=factory,
    )

    assert result.text == "hello world"
    assert result.language == "ja"
    assert result.model_size == "tiny"
    assert result.device == "cpu"
    assert result.compute_type == "int8"
    assert result.beam_size == 5
    assert result.duration_seconds == 2.0
    assert models[0].transcribe_calls[0]["language"] == "ja"
    assert models[0].transcribe_calls[0]["beam_size"] == 5


def test_auto_language_passes_none_to_faster_whisper(tmp_path: Path) -> None:
    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"fake wav")
    models = []

    def factory(model_size: str, device: str, compute_type: str):
        model = FakeWhisperModel(model_size, device, compute_type)
        models.append(model)
        return model

    result = transcribe_file(
        audio_path=audio_path,
        language="auto",
        model_factory=factory,
    )

    assert result.language == "en"
    assert models[0].transcribe_calls[0]["language"] is None


def test_cuda_failure_falls_back_to_cpu_int8(tmp_path: Path) -> None:
    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"fake wav")
    calls = []

    def factory(model_size: str, device: str, compute_type: str):
        calls.append((model_size, device, compute_type))
        if device == "cuda":
            raise RuntimeError("CUDA unavailable")
        return FakeWhisperModel(model_size, device, compute_type)

    result = transcribe_file(
        audio_path=audio_path,
        language="en",
        model_size="tiny",
        device="cuda",
        compute_type="float16",
        model_factory=factory,
    )

    assert calls == [("tiny", "cuda", "float16"), ("tiny", "cpu", "int8")]
    assert result.device == "cpu"
    assert result.compute_type == "int8"
    assert result.used_cpu_fallback is True


def test_cuda_transcribe_failure_falls_back_to_cpu_int8(tmp_path: Path) -> None:
    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"fake wav")
    calls = []

    def factory(model_size: str, device: str, compute_type: str):
        calls.append((model_size, device, compute_type))
        if device == "cuda":
            return FailingTranscribeModel(model_size, device, compute_type)
        return FakeWhisperModel(model_size, device, compute_type)

    result = transcribe_file(
        audio_path=audio_path,
        language="en",
        model_size="tiny",
        device="cuda",
        compute_type="float16",
        model_factory=factory,
    )

    assert calls == [("tiny", "cuda", "float16"), ("tiny", "cpu", "int8")]
    assert result.device == "cpu"
    assert result.compute_type == "int8"
    assert result.used_cpu_fallback is True


def test_cuda_failure_without_fallback_is_clear(tmp_path: Path) -> None:
    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"fake wav")

    def factory(model_size: str, device: str, compute_type: str):
        raise RuntimeError("CUDA unavailable")

    with pytest.raises(ASRError, match="Failed to load faster-whisper model"):
        transcribe_file(
            audio_path=audio_path,
            device="cuda",
            compute_type="float16",
            cpu_fallback=False,
            model_factory=factory,
        )


def test_reusable_transcriber_loads_model_once_for_multiple_files(tmp_path: Path) -> None:
    first = tmp_path / "first.wav"
    second = tmp_path / "second.wav"
    first.write_bytes(b"fake wav")
    second.write_bytes(b"fake wav")
    calls = []

    def factory(model_size: str, device: str, compute_type: str):
        calls.append((model_size, device, compute_type))
        return FakeWhisperModel(model_size, device, compute_type)

    transcriber = FasterWhisperTranscriber(
        language="en",
        model_size="tiny",
        device="cpu",
        compute_type="int8",
        beam_size=1,
        model_factory=factory,
    )

    assert transcriber.transcribe(first).text == "hello world"
    assert transcriber.transcribe(second).text == "hello world"
    assert calls == [("tiny", "cpu", "int8")]


def test_reusable_transcriber_reports_cpu_fallback_device(tmp_path: Path) -> None:
    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"fake wav")

    def factory(model_size: str, device: str, compute_type: str):
        if device == "cuda":
            raise RuntimeError("CUDA unavailable")
        return FakeWhisperModel(model_size, device, compute_type)

    transcriber = FasterWhisperTranscriber(
        language="en",
        model_size="tiny",
        device="cuda",
        compute_type="float16",
        model_factory=factory,
    )

    result = transcriber.transcribe(audio_path)

    assert result.device == "cpu"
    assert result.compute_type == "int8"
    assert result.used_cpu_fallback is True
    assert transcriber.effective_device == "cpu"


def test_missing_audio_file_is_clear(tmp_path: Path) -> None:
    with pytest.raises(ASRError, match="Audio file not found"):
        transcribe_file(tmp_path / "missing.wav", model_factory=FakeWhisperModel)
