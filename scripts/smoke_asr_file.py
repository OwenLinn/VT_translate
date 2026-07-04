from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from yt_live_translator.core.config import ConfigError, load_config
from yt_live_translator.core.logging_config import configure_logging
from yt_live_translator.core.models import SourceLanguage
from yt_live_translator.speech.asr_faster_whisper import ASRError, transcribe_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run faster-whisper ASR on a local audio file.")
    parser.add_argument("--audio", required=True, help="Path to an audio file.")
    parser.add_argument(
        "--language",
        choices=("auto", "en", "ja"),
        default=None,
        help="Source language. Defaults to app.source_language from config.",
    )
    parser.add_argument("--model", default=None, help="faster-whisper model size or local model path.")
    parser.add_argument("--device", default=None, help="Device, e.g. cuda or cpu.")
    parser.add_argument("--compute-type", default=None, help="Compute type, e.g. float16, int8.")
    parser.add_argument("--beam-size", type=int, default=None, help="Beam size.")
    parser.add_argument(
        "--no-cpu-fallback",
        action="store_true",
        help="Disable automatic CPU int8 fallback when CUDA model loading fails.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_logging(level=logging.WARNING)
    args = build_parser().parse_args(argv)

    try:
        config = load_config()
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    language: SourceLanguage = args.language or config.app.source_language
    model_size = args.model or config.asr.model
    device = args.device or config.asr.device
    compute_type = args.compute_type or config.asr.compute_type
    beam_size = args.beam_size or config.asr.beam_size

    print(
        "Running ASR: "
        f"audio={args.audio}, language={language}, model={model_size}, "
        f"device={device}, compute_type={compute_type}, beam_size={beam_size}"
    )

    try:
        result = transcribe_file(
            audio_path=args.audio,
            language=language,
            model_size=model_size,
            device=device,
            compute_type=compute_type,
            beam_size=beam_size,
            cpu_fallback=not args.no_cpu_fallback,
        )
    except (ASRError, ValueError) as exc:
        print(f"ASR smoke test failed: {exc}", file=sys.stderr)
        return 3

    if result.used_cpu_fallback:
        print("Warning: CUDA ASR failed; used CPU int8 fallback.")
    print(
        f"Detected language: {result.language}; device={result.device}; "
        f"compute_type={result.compute_type}; latency={result.latency_ms:.0f} ms"
    )
    if result.duration_seconds is not None:
        print(f"Audio duration: {result.duration_seconds:.2f}s")
    print("Segments:")
    for index, segment in enumerate(result.segments, start=1):
        print(f"  [{index}] {segment.start:.2f}-{segment.end:.2f}: {segment.text.strip()}")
    print("Transcript:")
    print(result.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
