"""faster-whisper ASR wrapper for file-based smoke tests."""

from __future__ import annotations

import time
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Callable

from yt_live_translator.core.models import SourceLanguage


class ASRError(RuntimeError):
    """Raised when ASR cannot run or returns unusable output."""


@dataclass(frozen=True)
class ASRSegmentText:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class ASRFileResult:
    audio_path: Path
    text: str
    language: str
    segments: list[ASRSegmentText]
    model_size: str
    device: str
    compute_type: str
    beam_size: int
    duration_seconds: float | None
    latency_ms: float
    used_cpu_fallback: bool = False


ModelFactory = Callable[..., Any]


class FasterWhisperTranscriber:
    """Reusable faster-whisper model wrapper for repeated segment/tick ASR."""

    def __init__(
        self,
        *,
        language: SourceLanguage = "auto",
        model_size: str = "large-v3-turbo",
        device: str = "cuda",
        compute_type: str = "float16",
        beam_size: int = 3,
        cpu_fallback: bool = True,
        model_factory: ModelFactory | None = None,
    ) -> None:
        _validate_options(language=language, beam_size=beam_size)
        self.language = language
        self.model_size = model_size
        self.requested_device = device
        self.requested_compute_type = compute_type
        self.beam_size = beam_size
        self.cpu_fallback = cpu_fallback
        self._factory = model_factory
        self._model: Any | None = None
        self._effective_device = device
        self._effective_compute_type = compute_type
        self._used_cpu_fallback = False

    @property
    def effective_device(self) -> str:
        return self._effective_device

    @property
    def effective_compute_type(self) -> str:
        return self._effective_compute_type

    @property
    def used_cpu_fallback(self) -> bool:
        return self._used_cpu_fallback

    def ensure_model_loaded(self) -> None:
        if self._model is not None:
            return
        factory = self._factory or _load_whisper_model_factory()
        self._factory = factory
        try:
            self._model = factory(
                self.model_size,
                device=self.requested_device,
                compute_type=self.requested_compute_type,
            )
            self._effective_device = self.requested_device
            self._effective_compute_type = self.requested_compute_type
        except Exception as exc:
            if not self.cpu_fallback or self.requested_device == "cpu":
                raise ASRError(_model_load_error_message(self.requested_device, self.requested_compute_type, exc)) from exc
            self._load_cpu_fallback()

    def transcribe(self, audio_path: str | Path) -> ASRFileResult:
        path = _audio_path(audio_path)
        start_time = time.perf_counter()
        self.ensure_model_loaded()
        language_arg = None if self.language == "auto" else self.language
        try:
            segments, info = _transcribe_with_model(self._model, path, language_arg, self.beam_size)
        except Exception as exc:
            if not self.cpu_fallback or self._effective_device == "cpu":
                raise ASRError(f"faster-whisper transcription failed: {exc}") from exc
            self._load_cpu_fallback()
            try:
                segments, info = _transcribe_with_model(self._model, path, language_arg, self.beam_size)
            except Exception as fallback_exc:
                raise ASRError(f"faster-whisper CPU fallback transcription failed: {fallback_exc}") from fallback_exc

        text = " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()
        latency_ms = (time.perf_counter() - start_time) * 1000
        detected_language = str(getattr(info, "language", self.language if self.language != "auto" else "unknown"))
        duration = getattr(info, "duration", None)
        duration_seconds = float(duration) if isinstance(duration, int | float) else None
        return ASRFileResult(
            audio_path=path,
            text=text,
            language=detected_language,
            segments=segments,
            model_size=self.model_size,
            device=self._effective_device,
            compute_type=self._effective_compute_type,
            beam_size=self.beam_size,
            duration_seconds=duration_seconds,
            latency_ms=latency_ms,
            used_cpu_fallback=self._used_cpu_fallback,
        )

    def _load_cpu_fallback(self) -> None:
        self._model = self._factory(self.model_size, device="cpu", compute_type="int8")
        self._effective_device = "cpu"
        self._effective_compute_type = "int8"
        self._used_cpu_fallback = True


def transcribe_file(
    audio_path: str | Path,
    language: SourceLanguage = "auto",
    model_size: str = "large-v3-turbo",
    device: str = "cuda",
    compute_type: str = "float16",
    beam_size: int = 3,
    cpu_fallback: bool = True,
    model_factory: ModelFactory | None = None,
) -> ASRFileResult:
    """Transcribe an audio file with faster-whisper."""

    return FasterWhisperTranscriber(
        language=language,
        model_size=model_size,
        device=device,
        compute_type=compute_type,
        beam_size=beam_size,
        cpu_fallback=cpu_fallback,
        model_factory=model_factory,
    ).transcribe(audio_path)


def _validate_options(*, language: SourceLanguage, beam_size: int) -> None:
    if language not in ("auto", "en", "ja"):
        raise ValueError("language must be auto, en, or ja")
    if beam_size <= 0:
        raise ValueError("beam_size must be greater than 0")


def _audio_path(audio_path: str | Path) -> Path:
    path = Path(audio_path)
    if not path.exists():
        raise ASRError(f"Audio file not found: {path}")
    return path


def _load_whisper_model_factory() -> ModelFactory:
    try:
        faster_whisper = import_module("faster_whisper")
    except ImportError as exc:
        raise ASRError(
            "faster-whisper is required for ASR. Install it with: pip install faster-whisper"
        ) from exc
    return faster_whisper.WhisperModel


def _transcribe_with_model(
    model: Any,
    path: Path,
    language_arg: str | None,
    beam_size: int,
) -> tuple[list[ASRSegmentText], Any]:
    raw_segments, info = model.transcribe(
        str(path),
        language=language_arg,
        beam_size=beam_size,
    )
    return [_segment_from_raw(segment) for segment in raw_segments], info


def _segment_from_raw(segment: Any) -> ASRSegmentText:
    return ASRSegmentText(
        start=float(getattr(segment, "start", 0.0)),
        end=float(getattr(segment, "end", 0.0)),
        text=str(getattr(segment, "text", "")),
    )


def _model_load_error_message(device: str, compute_type: str, exc: Exception) -> str:
    return (
        "Failed to load faster-whisper model "
        f"with device={device}, compute_type={compute_type}: {exc}"
    )
