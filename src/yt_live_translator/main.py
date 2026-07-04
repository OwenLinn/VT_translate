"""Command-line entry point for the Stage 0 scaffold."""

from __future__ import annotations

import argparse

from yt_live_translator.core.config import ConfigError, load_config
from yt_live_translator.core.models import SourceLanguage, TargetLanguage
from yt_live_translator import __version__
from yt_live_translator.ui.electron_overlay_bridge import run_electron_overlay_live
from yt_live_translator.ui.electron_overlay_app import run_electron_overlay
from yt_live_translator.ui.overlay_pipeline_app import OverlayPipelineOptions, run_overlay_pipeline_app
from yt_live_translator.ui.overlay_window import OverlayError, run_overlay_test, style_from_config
from yt_live_translator.ui.qml_overlay.qml_overlay_app import (
    run_qml_overlay_test,
    run_qml_overlay_tuning,
)
from yt_live_translator.ui.settings_window import run_settings_window


SCAFFOLD_MESSAGE = "YouTube Live Translator Overlay - scaffold OK"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yt-live-translator",
        description="YouTube Live Translator Overlay scaffold entry point.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--overlay-test",
        action="store_true",
        help="Show a basic draggable subtitle overlay with test text.",
    )
    parser.add_argument(
        "--overlay-test-seconds",
        type=float,
        default=None,
        help="Close overlay test automatically after N seconds.",
    )
    parser.add_argument(
        "--style",
        choices=("classic", "glass"),
        default=None,
        help="Overlay visual style for --overlay-test.",
    )
    parser.add_argument(
        "--overlay-pipeline-test",
        action="store_true",
        help="Run the Stage 6 overlay pipeline smoke app.",
    )
    parser.add_argument(
        "--qml-overlay-test",
        action="store_true",
        help="Show the Phase 1 QML Liquid Glass overlay frontend with placeholder data.",
    )
    parser.add_argument(
        "--qml-overlay-test-seconds",
        type=float,
        default=None,
        help="Close the QML overlay test automatically after N seconds.",
    )
    parser.add_argument(
        "--qml-overlay-tuning",
        action="store_true",
        help="Show the QML overlay with Phase 2 visual tuning controls.",
    )
    parser.add_argument(
        "--qml-overlay-tuning-seconds",
        type=float,
        default=None,
        help="Close QML overlay tuning automatically after N seconds.",
    )
    parser.add_argument(
        "--electron-overlay-test",
        action="store_true",
        help="Launch the Electron overlay Phase 2 mock frontend.",
    )
    parser.add_argument(
        "--electron-overlay-tuning",
        action="store_true",
        help="Launch the Electron overlay Phase 2 tuning frontend.",
    )
    parser.add_argument(
        "--electron-overlay-live",
        action="store_true",
        help="Launch the Electron overlay connected to the real Python subtitle pipeline.",
    )
    parser.add_argument("--audio-file", default=None, help="Local audio file for overlay pipeline test.")
    parser.add_argument("--loopback-seconds", type=float, default=None, help="Capture live system audio for N seconds.")
    parser.add_argument(
        "--continuous-loopback",
        action="store_true",
        help="Continuously capture short loopback chunks until stopped.",
    )
    parser.add_argument(
        "--loopback-chunk-seconds",
        type=float,
        default=6.0,
        help="Seconds per live loopback chunk in continuous mode.",
    )
    parser.add_argument(
        "--max-loopback-chunks",
        type=int,
        default=None,
        help="Maximum chunks in continuous mode. Omit for unlimited.",
    )
    parser.add_argument("--max-audio-seconds", type=float, default=None)
    parser.add_argument("--source-lang", choices=("auto", "en", "ja"), default=None)
    parser.add_argument("--target", choices=("zh-TW", "zh-CN"), default=None)
    parser.add_argument("--translation", choices=("deepseek", "echo"), default="deepseek")
    parser.add_argument(
        "--streaming-strategy",
        choices=("fixed_segments", "local_agreement"),
        default=None,
        help="Use local_agreement for low-latency streaming subtitles.",
    )
    parser.add_argument("--deepseek-timeout", type=float, default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--device", default=None)
    parser.add_argument("--compute-type", default=None)
    parser.add_argument("--beam-size", type=int, default=None)
    parser.add_argument("--max-segments", type=int, default=2, help="Use 0 for no limit.")
    parser.add_argument("--vad-threshold", type=float, default=0.005)
    parser.add_argument("--min-speech-ms", type=int, default=None)
    parser.add_argument("--max-speech-ms", type=int, default=None)
    parser.add_argument("--silence-end-ms", type=int, default=None)
    parser.add_argument("--padding-ms", type=int, default=None)
    parser.add_argument("--close-on-finish", action="store_true")
    parser.add_argument("--auto-close-seconds", type=float, default=None)
    parser.add_argument("--overlay-result-log", default=None)
    parser.add_argument("--glossary-db", default=None, help="Optional SQLite glossary database path.")
    parser.add_argument("--no-glossary", action="store_true", help="Disable glossary matching.")
    parser.add_argument("--settings-test", action="store_true", help="Show the Stage 8 settings window.")
    parser.add_argument("--settings-test-seconds", type=float, default=None)
    parser.add_argument("--settings-db", default=None, help="Optional SQLite settings database path.")
    parser.add_argument("--subtitle-log", default=None, help="Optional JSONL subtitle log path.")
    parser.add_argument("--no-subtitle-log", action="store_true", help="Disable subtitle log writing.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.overlay_test:
        try:
            config = load_config()
            return run_overlay_test(
                style_from_config(config.overlay),
                close_after_seconds=args.overlay_test_seconds,
                style_mode=args.style,
            )
        except (ConfigError, OverlayError, ValueError) as exc:
            print(f"Overlay test failed: {exc}")
            return 2
    if args.overlay_pipeline_test:
        try:
            config = load_config()
            if args.audio_file is None and args.loopback_seconds is None and not args.continuous_loopback:
                parser.error(
                    "--overlay-pipeline-test requires --audio-file, --loopback-seconds, "
                    "or --continuous-loopback"
                )
            options = OverlayPipelineOptions(
                audio_file=args.audio_file,
                loopback_seconds=args.loopback_seconds,
                max_audio_seconds=args.max_audio_seconds,
                source_language=_source_language(args.source_lang or config.app.source_language),
                target_language=_target_language(args.target or config.app.target_language),
                translation_mode=args.translation,
                deepseek_timeout=args.deepseek_timeout,
                model_size=args.model or config.asr.model,
                device=args.device or config.asr.device,
                compute_type=args.compute_type or config.asr.compute_type,
                beam_size=args.beam_size or config.asr.beam_size,
                max_segments=None if args.max_segments == 0 else args.max_segments,
                vad_threshold=args.vad_threshold,
                min_speech_ms=args.min_speech_ms or config.vad.min_speech_ms,
                max_speech_ms=args.max_speech_ms or config.vad.max_speech_ms,
                silence_end_ms=args.silence_end_ms or config.vad.silence_end_ms,
                padding_ms=args.padding_ms or config.vad.padding_ms,
                close_on_finish=args.close_on_finish,
                auto_close_seconds=args.auto_close_seconds,
                result_log=args.overlay_result_log,
                glossary_db=args.glossary_db,
                glossary_enabled=not args.no_glossary,
                subtitle_log_path=args.subtitle_log,
                subtitle_log_enabled=not args.no_subtitle_log,
                continuous_loopback=args.continuous_loopback,
                loopback_chunk_seconds=args.loopback_chunk_seconds,
                max_loopback_chunks=args.max_loopback_chunks,
                streaming_strategy=args.streaming_strategy
                or (config.streaming.strategy if config.streaming.enabled else "fixed_segments"),
            )
            return run_overlay_pipeline_app(config, options)
        except (ConfigError, OverlayError, ValueError) as exc:
            print(f"Overlay pipeline test failed: {exc}")
            return 2
    if args.qml_overlay_test:
        try:
            config = load_config()
            return run_qml_overlay_test(config, close_after_seconds=args.qml_overlay_test_seconds)
        except (ConfigError, OverlayError, ValueError) as exc:
            print(f"QML overlay test failed: {exc}")
            return 2
    if args.qml_overlay_tuning:
        try:
            config = load_config()
            return run_qml_overlay_tuning(config, close_after_seconds=args.qml_overlay_tuning_seconds)
        except (ConfigError, OverlayError, ValueError) as exc:
            print(f"QML overlay tuning failed: {exc}")
            return 2
    if args.electron_overlay_test:
        try:
            load_config()
            return run_electron_overlay("mock")
        except (ConfigError, OverlayError, ValueError) as exc:
            print(f"Electron overlay test failed: {exc}")
            return 2
    if args.electron_overlay_tuning:
        try:
            load_config()
            return run_electron_overlay("tuning")
        except (ConfigError, OverlayError, ValueError) as exc:
            print(f"Electron overlay tuning failed: {exc}")
            return 2
    if args.electron_overlay_live:
        try:
            config = load_config()
            if args.audio_file is None and args.loopback_seconds is None and not args.continuous_loopback:
                parser.error(
                    "--electron-overlay-live requires --audio-file, --loopback-seconds, "
                    "or --continuous-loopback"
                )
            options = OverlayPipelineOptions(
                audio_file=args.audio_file,
                loopback_seconds=args.loopback_seconds,
                max_audio_seconds=args.max_audio_seconds,
                source_language=_source_language(args.source_lang or config.app.source_language),
                target_language=_target_language(args.target or config.app.target_language),
                translation_mode=args.translation,
                deepseek_timeout=args.deepseek_timeout,
                model_size=args.model or config.asr.model,
                device=args.device or config.asr.device,
                compute_type=args.compute_type or config.asr.compute_type,
                beam_size=args.beam_size or config.asr.beam_size,
                max_segments=None if args.max_segments == 0 else args.max_segments,
                vad_threshold=args.vad_threshold,
                min_speech_ms=args.min_speech_ms or config.vad.min_speech_ms,
                max_speech_ms=args.max_speech_ms or config.vad.max_speech_ms,
                silence_end_ms=args.silence_end_ms or config.vad.silence_end_ms,
                padding_ms=args.padding_ms or config.vad.padding_ms,
                close_on_finish=args.close_on_finish,
                auto_close_seconds=args.auto_close_seconds,
                result_log=args.overlay_result_log,
                glossary_db=args.glossary_db,
                glossary_enabled=not args.no_glossary,
                subtitle_log_path=args.subtitle_log,
                subtitle_log_enabled=not args.no_subtitle_log,
                continuous_loopback=args.continuous_loopback,
                loopback_chunk_seconds=args.loopback_chunk_seconds,
                max_loopback_chunks=args.max_loopback_chunks,
                streaming_strategy=args.streaming_strategy
                or (config.streaming.strategy if config.streaming.enabled else "fixed_segments"),
            )
            return run_electron_overlay_live(config, options)
        except (ConfigError, OverlayError, ValueError) as exc:
            print(f"Electron overlay live failed: {exc}")
            return 2
    if args.settings_test:
        try:
            config = load_config()
            return run_settings_window(
                config,
                database_path=args.settings_db,
                close_after_seconds=args.settings_test_seconds,
            )
        except (ConfigError, OverlayError, ValueError) as exc:
            print(f"Settings test failed: {exc}")
            return 2
    print(SCAFFOLD_MESSAGE)
    return 0


def _source_language(value: str) -> SourceLanguage:
    if value not in ("auto", "en", "ja"):
        raise ValueError("source language must be auto, en, or ja")
    return value


def _target_language(value: str) -> TargetLanguage:
    if value not in ("zh-TW", "zh-CN"):
        raise ValueError("target language must be zh-TW or zh-CN")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
