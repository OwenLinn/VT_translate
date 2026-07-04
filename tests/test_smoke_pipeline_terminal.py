from __future__ import annotations

import importlib.util
from pathlib import Path

from yt_live_translator.core.models import ASRResult, TranslationResult
from yt_live_translator.core.subtitle_pipeline import StreamingPipelineEvent


_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "smoke_pipeline_terminal.py"
_SPEC = importlib.util.spec_from_file_location("smoke_pipeline_terminal", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
_print_streaming_event = _MODULE._print_streaming_event


def test_print_streaming_event_outputs_partial_and_final_blocks(capsys) -> None:
    partial = _event("partial", "hello stream", "[echo] hello stream")
    final = _event("final", "hello stream today.", "[echo] hello stream today.")

    _print_streaming_event(partial, subtitle_log=None)
    _print_streaming_event(final, subtitle_log=None)

    output = capsys.readouterr().out
    assert "[PARTIAL]" in output
    assert "[FINAL]" in output
    assert "source: hello stream" in output
    assert "translation: [echo] hello stream today." in output
    assert "latency:" in output


def _event(kind: str, source_text: str, translated_text: str) -> StreamingPipelineEvent:
    return StreamingPipelineEvent(
        kind=kind,
        asr=ASRResult(
            segment_id=1,
            source_text=source_text,
            source_language="en",
            start_time=0.0,
            end_time=1.0,
            asr_latency_ms=12.0,
        ),
        translation=TranslationResult(
            segment_id=1,
            source_text=source_text,
            translated_text=translated_text,
            source_language="en",
            target_language="zh-TW",
            total_latency_ms=42.0,
        ),
    )
