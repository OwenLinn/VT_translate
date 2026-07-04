from __future__ import annotations

import argparse
import logging
import re
import sys
import time
from dataclasses import dataclass
from dataclasses import replace
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from yt_live_translator.core.config import ConfigError, RuntimeConfig, load_config
from yt_live_translator.core.logging_config import configure_logging
from yt_live_translator.core.models import SourceLanguage, TargetLanguage
from yt_live_translator.speech.asr_faster_whisper import (
    ASRError,
    ASRFileResult,
    ASRRuntimeDiagnostics,
    collect_runtime_diagnostics,
    transcribe_file,
)
from yt_live_translator.translate.deepseek_client import (
    DeepSeekAPIError,
    DeepSeekClient,
    MissingAPIKeyError,
)
from yt_live_translator.translate.glossary_apply import (
    apply_conservative_post_processing,
    open_glossary_repository,
    translate_with_glossary,
)


@dataclass(frozen=True)
class SmokeResult:
    audio_path: Path
    asr_provider: str
    asr_model: str
    source_language: SourceLanguage
    target_language: TargetLanguage
    translation_provider: str
    diagnostics: ASRRuntimeDiagnostics
    asr_result: ASRFileResult
    translation_text: str
    translation_latency_ms: float
    total_latency_ms: float


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run local audio -> faster-whisper ASR -> translation smoke test.",
    )
    parser.add_argument("--audio", required=True, help="Path to a local audio file.")
    parser.add_argument("--source-lang", choices=("auto", "en", "ja"), default=None)
    parser.add_argument("--target", choices=("zh-TW", "zh-CN"), default=None)
    parser.add_argument(
        "--asr-provider",
        choices=("faster_whisper", "faster-whisper"),
        default="faster_whisper",
        help="ASR provider. Only faster_whisper is supported in this smoke test.",
    )
    parser.add_argument("--asr-model", default=None, help="faster-whisper model name or local model path.")
    parser.add_argument("--device", default=None, help="ASR device, e.g. cuda or cpu.")
    parser.add_argument("--compute-type", default=None, help="ASR compute type, e.g. float16 or int8.")
    parser.add_argument("--beam-size", type=int, default=None)
    parser.add_argument("--translation", choices=("deepseek", "echo"), default="echo")
    parser.add_argument("--deepseek-timeout", type=float, default=None)
    parser.add_argument("--glossary-db", default=None, help="Optional SQLite glossary database path.")
    parser.add_argument("--no-glossary", action="store_true", help="Disable glossary matching.")
    parser.add_argument(
        "--no-cpu-fallback",
        action="store_true",
        help="Disable automatic CPU int8 fallback when CUDA fails.",
    )
    parser.add_argument(
        "--log-dir",
        default="runtime_logs/asr_model_tests",
        help="Directory for timestamped smoke-test reports.",
    )
    parser.add_argument("--no-log", action="store_true", help="Print only; do not write a report file.")
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_logging(level=logging.WARNING)
    args = build_parser().parse_args(argv)

    try:
        config = load_config()
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    source_language: SourceLanguage = args.source_lang or config.app.source_language
    target_language: TargetLanguage = args.target or config.app.target_language
    asr_model = args.asr_model or config.asr.model
    device = args.device or config.asr.device
    compute_type = args.compute_type or config.asr.compute_type
    beam_size = args.beam_size or config.asr.beam_size
    asr_provider = _normalize_asr_provider(args.asr_provider)

    if asr_provider != "faster_whisper":
        print(f"Unsupported ASR provider: {args.asr_provider}", file=sys.stderr)
        return 2

    diagnostics = collect_runtime_diagnostics(
        model_size=asr_model,
        device=device,
        compute_type=compute_type,
    )
    _print_diagnostics(diagnostics, beam_size=beam_size, source_language=source_language)
    if args.translation == "deepseek" and not config.resolve_deepseek_api_key():
        error = MissingAPIKeyError(
            f"DeepSeek API key is missing. Set {config.deepseek.api_key_env} before running deepseek mode."
        )
        error_report = _format_error_report(
            audio_path=Path(args.audio),
            asr_provider=asr_provider,
            asr_model=asr_model,
            source_language=source_language,
            target_language=target_language,
            translation_provider=args.translation,
            diagnostics=diagnostics,
            error=error,
        )
        print(error_report)
        if not args.no_log:
            log_path = _write_report(
                report=error_report,
                log_dir=Path(args.log_dir),
                model_name=asr_model,
                error=True,
            )
            print(f"Report written: {log_path}")
        return 3

    try:
        result = run_smoke(
            config=config,
            audio_path=Path(args.audio),
            asr_provider=asr_provider,
            asr_model=asr_model,
            source_language=source_language,
            target_language=target_language,
            device=device,
            compute_type=compute_type,
            beam_size=beam_size,
            translation_provider=args.translation,
            deepseek_timeout=args.deepseek_timeout,
            glossary_db=args.glossary_db,
            glossary_enabled=not args.no_glossary,
            cpu_fallback=not args.no_cpu_fallback,
            diagnostics=diagnostics,
        )
    except (ASRError, DeepSeekAPIError, MissingAPIKeyError, ValueError) as exc:
        error_report = _format_error_report(
            audio_path=Path(args.audio),
            asr_provider=asr_provider,
            asr_model=asr_model,
            source_language=source_language,
            target_language=target_language,
            translation_provider=args.translation,
            diagnostics=diagnostics,
            error=exc,
        )
        print(error_report)
        if not args.no_log:
            log_path = _write_report(
                report=error_report,
                log_dir=Path(args.log_dir),
                model_name=asr_model,
                error=True,
            )
            print(f"Report written: {log_path}")
        return 3

    report = format_report(result)
    print(report)
    if not args.no_log:
        log_path = _write_report(report=report, log_dir=Path(args.log_dir), model_name=asr_model)
        print(f"Report written: {log_path}")
    return 0


def run_smoke(
    *,
    config: RuntimeConfig,
    audio_path: Path,
    asr_provider: str,
    asr_model: str,
    source_language: SourceLanguage,
    target_language: TargetLanguage,
    device: str,
    compute_type: str,
    beam_size: int,
    translation_provider: str,
    deepseek_timeout: float | None,
    glossary_db: str | None,
    glossary_enabled: bool,
    cpu_fallback: bool,
    diagnostics: ASRRuntimeDiagnostics,
) -> SmokeResult:
    total_start = time.perf_counter()
    asr_result = transcribe_file(
        audio_path=audio_path,
        language=source_language,
        model_size=asr_model,
        device=device,
        compute_type=compute_type,
        beam_size=beam_size,
        cpu_fallback=cpu_fallback,
    )
    source_text = asr_result.text.strip()
    if not source_text:
        raise ASRError("ASR returned empty transcript")

    repository = None if not glossary_enabled else open_glossary_repository(config, glossary_db)
    translation_start = time.perf_counter()
    if translation_provider == "echo":
        matched_terms = (
            repository.find_matching_terms(
                text=source_text,
                source_language=source_language,
                target_language=target_language,
            )
            if repository is not None
            else []
        )
        translation_text = apply_conservative_post_processing(
            source_text=source_text,
            translated_text=f"[echo:{target_language}] {source_text}",
            matched_terms=matched_terms,
            target_language=target_language,
        )
    elif translation_provider == "deepseek":
        deepseek_config = config.deepseek
        if deepseek_timeout is not None:
            deepseek_config = replace(deepseek_config, timeout_seconds=deepseek_timeout)
        client = DeepSeekClient(config=deepseek_config, api_key=config.resolve_deepseek_api_key())
        translation_text = translate_with_glossary(
            client,
            text=source_text,
            source_language=source_language,
            target_language=target_language,
            repository=repository,
        )
    else:
        raise ValueError("translation must be deepseek or echo")
    translation_latency_ms = (time.perf_counter() - translation_start) * 1000
    total_latency_ms = (time.perf_counter() - total_start) * 1000

    return SmokeResult(
        audio_path=audio_path,
        asr_provider=asr_provider,
        asr_model=asr_model,
        source_language=source_language,
        target_language=target_language,
        translation_provider=translation_provider,
        diagnostics=diagnostics,
        asr_result=asr_result,
        translation_text=translation_text,
        translation_latency_ms=translation_latency_ms,
        total_latency_ms=total_latency_ms,
    )


def format_report(result: SmokeResult) -> str:
    lines = [
        "Local Audio ASR + Translation Smoke Test",
        "=======================================",
        f"Audio path: {result.audio_path}",
        f"ASR provider: {result.asr_provider}",
        f"Model: {result.asr_model}",
        f"Selected model path: {result.diagnostics.model_path}",
        f"Model path exists: {result.diagnostics.model_path_exists}",
        f"Device: {result.asr_result.device}",
        f"Requested device: {result.diagnostics.requested_device}",
        f"Compute type: {result.asr_result.compute_type}",
        f"Requested compute_type: {result.diagnostics.requested_compute_type}",
        f"Beam size: {result.asr_result.beam_size}",
        f"Source language: {result.source_language}",
        f"Detected language: {result.asr_result.language}",
        f"Target language: {result.target_language}",
        f"Translation provider: {result.translation_provider}",
        f"CTranslate2 available: {result.diagnostics.ctranslate2_available}",
        f"CTranslate2 CUDA devices: {_none_as_unknown(result.diagnostics.cuda_device_count)}",
        f"CPU fallback used: {result.asr_result.used_cpu_fallback}",
        "",
        "ASR:",
        result.asr_result.text,
        "",
        "Translation:",
        result.translation_text,
        "",
        f"ASR latency: {result.asr_result.latency_ms:.0f} ms",
        f"Translation latency: {result.translation_latency_ms:.0f} ms",
        f"Total latency: {result.total_latency_ms:.0f} ms",
    ]
    if result.asr_result.duration_seconds is not None:
        lines.insert(15, f"Audio duration: {result.asr_result.duration_seconds:.2f}s")
    return "\n".join(lines)


def _format_error_report(
    *,
    audio_path: Path,
    asr_provider: str,
    asr_model: str,
    source_language: SourceLanguage,
    target_language: TargetLanguage,
    translation_provider: str,
    diagnostics: ASRRuntimeDiagnostics,
    error: Exception,
) -> str:
    return "\n".join(
        [
            "Local Audio ASR + Translation Smoke Test",
            "=======================================",
            "Status: failed",
            f"Audio path: {audio_path}",
            f"ASR provider: {asr_provider}",
            f"Model: {asr_model}",
            f"Selected model path: {diagnostics.model_path}",
            f"Model path exists: {diagnostics.model_path_exists}",
            f"Requested device: {diagnostics.requested_device}",
            f"Requested compute_type: {diagnostics.requested_compute_type}",
            f"Source language: {source_language}",
            f"Target language: {target_language}",
            f"Translation provider: {translation_provider}",
            f"CTranslate2 available: {diagnostics.ctranslate2_available}",
            f"CTranslate2 CUDA devices: {_none_as_unknown(diagnostics.cuda_device_count)}",
            f"Error: {error}",
        ]
    )


def _print_diagnostics(
    diagnostics: ASRRuntimeDiagnostics,
    *,
    beam_size: int,
    source_language: SourceLanguage,
) -> None:
    print("ASR diagnostics:")
    print(f"  selected model path: {diagnostics.model_path}")
    print(f"  model path exists: {diagnostics.model_path_exists}")
    print(f"  device: {diagnostics.requested_device}")
    print(f"  compute_type: {diagnostics.requested_compute_type}")
    print(f"  beam_size: {beam_size}")
    print(f"  language: {source_language}")
    print(f"  ctranslate2 available: {diagnostics.ctranslate2_available}")
    if diagnostics.cuda_device_count is not None:
        print(f"  ctranslate2 cuda devices: {diagnostics.cuda_device_count}")
    if diagnostics.ctranslate2_error:
        print(f"  ctranslate2 diagnostic error: {diagnostics.ctranslate2_error}")


def _write_report(*, report: str, log_dir: Path, model_name: str, error: bool = False) -> Path:
    if not log_dir.is_absolute():
        log_dir = PROJECT_ROOT / log_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / _report_filename(model_name=model_name, error=error)
    path.write_text(report + "\n", encoding="utf-8")
    return path


def _report_filename(*, model_name: str, error: bool = False) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = _report_prefix(model_name)
    suffix = "_error" if error else ""
    return f"{prefix}_{timestamp}{suffix}.txt"


def _report_prefix(model_name: str) -> str:
    normalized = _sanitize_label(Path(model_name).name or model_name)
    if normalized == "anime_whisper_ct2_fp16":
        return "anime_whisper_ct2_fp16_test"
    if normalized == "faster_whisper_large_v3":
        return "large_v3_baseline"
    return f"{normalized}_test"


def _sanitize_label(value: str) -> str:
    label = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return label or "asr_model"


def _normalize_asr_provider(value: str) -> str:
    return value.replace("-", "_")


def _none_as_unknown(value: object) -> object:
    return "unknown" if value is None else value


if __name__ == "__main__":
    raise SystemExit(main())
