from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from yt_live_translator.speech.asr_faster_whisper import ASRFileResult, ASRRuntimeDiagnostics, ASRSegmentText


_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "smoke_audio_translate_file.py"
_SPEC = importlib.util.spec_from_file_location("smoke_audio_translate_file", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules["smoke_audio_translate_file"] = _MODULE
_SPEC.loader.exec_module(_MODULE)


def test_report_prefixes_for_requested_models() -> None:
    assert _MODULE._report_prefix("models/anime-whisper-ct2-fp16") == "anime_whisper_ct2_fp16_test"
    assert _MODULE._report_prefix("models/faster-whisper-large-v3") == "large_v3_baseline"


def test_format_report_includes_asr_translation_and_latency(tmp_path: Path) -> None:
    result = _MODULE.SmokeResult(
        audio_path=Path("sample.mp3"),
        asr_provider="faster_whisper",
        asr_model="models/anime-whisper-ct2-fp16",
        source_language="ja",
        target_language="zh-TW",
        translation_provider="echo",
        diagnostics=ASRRuntimeDiagnostics(
            model_size="models/anime-whisper-ct2-fp16",
            model_path=tmp_path / "models" / "anime-whisper-ct2-fp16",
            model_path_exists=True,
            requested_device="cuda",
            requested_compute_type="float16",
            ctranslate2_available=True,
            cuda_device_count=1,
            cuda_available=True,
        ),
        asr_result=ASRFileResult(
            audio_path=Path("sample.mp3"),
            text="こんにちは",
            language="ja",
            segments=[ASRSegmentText(start=0.0, end=1.0, text="こんにちは")],
            model_size="models/anime-whisper-ct2-fp16",
            device="cuda",
            compute_type="float16",
            beam_size=3,
            duration_seconds=1.0,
            latency_ms=123.0,
            used_cpu_fallback=False,
        ),
        translation_text="[echo:zh-TW] こんにちは",
        translation_latency_ms=4.0,
        total_latency_ms=130.0,
    )

    report = _MODULE.format_report(result)

    assert "Model: models/anime-whisper-ct2-fp16" in report
    assert "ASR:\nこんにちは" in report
    assert "Translation:\n[echo:zh-TW] こんにちは" in report
    assert "ASR latency: 123 ms" in report
    assert "Translation latency: 4 ms" in report
    assert "CPU fallback used: False" in report
