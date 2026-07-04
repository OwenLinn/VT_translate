from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import replace
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from yt_live_translator.audio.wasapi_capture import AudioCaptureError, capture_loopback
from yt_live_translator.core.config import ConfigError, load_config
from yt_live_translator.core.logging_config import configure_logging
from yt_live_translator.core.models import SourceLanguage, TargetLanguage
from yt_live_translator.core.subtitle_pipeline import (
    PipelineConfig,
    StreamingPipelineConfig,
    load_audio_file_as_pcm16,
    run_terminal_pipeline_on_audio,
    run_streaming_pipeline_on_audio,
)
from yt_live_translator.speech.asr_faster_whisper import ASRError, FasterWhisperTranscriber
from yt_live_translator.speech.segmenter import SegmenterConfig
from yt_live_translator.speech.streaming_agreement import LocalAgreementConfig
from yt_live_translator.storage.subtitle_log_repo import (
    SubtitleLogRepository,
    resolve_subtitle_log_path,
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Stage 4 terminal subtitle pipeline.")
    source = parser.add_mutually_exclusive_group(required=False)
    source.add_argument("--audio-file", help="Local audio file to process, including mp3 or wav.")
    source.add_argument("--loopback-seconds", type=float, help="Capture system output for N seconds.")
    parser.add_argument(
        "--streaming-strategy",
        choices=("fixed_segments", "local_agreement"),
        default=None,
        help="Use local_agreement for low-latency rolling-window streaming.",
    )
    parser.add_argument("--source-lang", choices=("auto", "en", "ja"), default=None)
    parser.add_argument("--target", choices=("zh-TW", "zh-CN"), default=None)
    parser.add_argument("--translation", choices=("deepseek", "echo"), default="deepseek")
    parser.add_argument("--deepseek-timeout", type=float, default=None)
    parser.add_argument(
        "--max-audio-seconds",
        type=float,
        default=None,
        help="Limit local audio-file decoding to the first N seconds, e.g. 180 for stability tests.",
    )
    parser.add_argument("--model", default=None, help="faster-whisper model size or local model path.")
    parser.add_argument("--device", default=None)
    parser.add_argument("--compute-type", default=None)
    parser.add_argument("--beam-size", type=int, default=None)
    parser.add_argument("--vad-threshold", type=float, default=0.01)
    parser.add_argument("--max-segments", type=int, default=2, help="Maximum segments to process. Use 0 for no limit.")
    parser.add_argument("--min-speech-ms", type=int, default=None)
    parser.add_argument("--max-speech-ms", type=int, default=None)
    parser.add_argument("--silence-end-ms", type=int, default=None)
    parser.add_argument("--padding-ms", type=int, default=None)
    parser.add_argument("--glossary-db", default=None, help="Optional SQLite glossary database path.")
    parser.add_argument("--no-glossary", action="store_true", help="Disable glossary matching.")
    parser.add_argument("--subtitle-log", default=None, help="Optional JSONL subtitle log path.")
    parser.add_argument("--no-subtitle-log", action="store_true", help="Disable subtitle log writing.")
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
    streaming_strategy = args.streaming_strategy or (
        config.streaming.strategy if config.streaming.enabled else "fixed_segments"
    )
    model_size = args.model or config.asr.model
    device = args.device or config.asr.device
    compute_type = args.compute_type or config.asr.compute_type
    beam_size = args.beam_size or config.asr.beam_size
    repository = None if args.no_glossary else open_glossary_repository(config, args.glossary_db)
    subtitle_log = None if args.no_subtitle_log else SubtitleLogRepository(
        resolve_subtitle_log_path(config, args.subtitle_log)
    )

    if args.audio_file is None and args.loopback_seconds is None:
        if streaming_strategy != "local_agreement":
            print("Audio source error: provide --audio-file or --loopback-seconds", file=sys.stderr)
            return 3
        args.loopback_seconds = max(
            config.streaming.rolling_window_sec,
            _language_streaming_config(config, source_language).max_commit_sec + config.streaming.overlap_sec,
        )

    try:
        if args.audio_file:
            print(f"Loading audio file: {args.audio_file}")
            audio = load_audio_file_as_pcm16(
                args.audio_file,
                sample_rate=config.audio.sample_rate,
                channels=config.audio.channels,
                max_duration_seconds=args.max_audio_seconds,
            )
        else:
            print(f"Capturing loopback audio for {args.loopback_seconds:g}s...")
            capture = capture_loopback(
                seconds=args.loopback_seconds,
                target_sample_rate=config.audio.sample_rate,
                target_channels=config.audio.channels,
                chunk_ms=config.audio.chunk_ms,
            )
            audio = capture.audio
    except (AudioCaptureError, RuntimeError, ValueError) as exc:
        print(f"Audio source error: {exc}", file=sys.stderr)
        return 3

    transcriber = FasterWhisperTranscriber(
            language=source_language,
            model_size=model_size,
            device=device,
            compute_type=compute_type,
            beam_size=beam_size,
    )

    def asr(segment_path: Path):
        return transcriber.transcribe(segment_path)

    if args.translation == "echo":
        def translate(text: str, source: SourceLanguage, target: TargetLanguage) -> str:
            translated = f"[echo:{target}] {text}"
            matched_terms = (
                repository.find_matching_terms(
                    text=text,
                    source_language=source,
                    target_language=target,
                )
                if repository is not None
                else []
            )
            return apply_conservative_post_processing(
                source_text=text,
                translated_text=translated,
                matched_terms=matched_terms,
                target_language=target,
            )
    else:
        deepseek_config = config.deepseek
        if args.deepseek_timeout is not None:
            deepseek_config = replace(deepseek_config, timeout_seconds=args.deepseek_timeout)
        client = DeepSeekClient(
            config=deepseek_config,
            api_key=config.resolve_deepseek_api_key(),
        )

        def translate(text: str, source: SourceLanguage, target: TargetLanguage) -> str:
            return translate_with_glossary(
                client,
                text=text,
                source_language=source,
                target_language=target,
                repository=repository,
            )

    try:
        if streaming_strategy == "local_agreement":
            events = run_streaming_pipeline_on_audio(
                audio=audio,
                config=_build_streaming_pipeline_config(
                    runtime_config=config,
                    source_language=source_language,
                    target_language=target_language,
                    max_segments=None if args.max_segments == 0 else args.max_segments,
                ),
                asr=asr,
                translate=translate,
                on_event=lambda event: _print_streaming_event(event, subtitle_log),
            )
            if not events:
                print("No streaming subtitle events were produced. Try a louder source or longer input.")
                return 5
            return 0
        outputs = run_terminal_pipeline_on_audio(
            audio=audio,
            config=PipelineConfig(
                source_language=source_language,
                target_language=target_language,
                vad_threshold=args.vad_threshold,
                segmenter=SegmenterConfig(
                    frame_ms=config.audio.chunk_ms,
                    min_speech_ms=args.min_speech_ms or config.vad.min_speech_ms,
                    max_speech_ms=args.max_speech_ms or config.vad.max_speech_ms,
                    silence_end_ms=args.silence_end_ms or config.vad.silence_end_ms,
                    padding_ms=args.padding_ms or config.vad.padding_ms,
                ),
                max_segments=None if args.max_segments == 0 else args.max_segments,
            ),
            asr=asr,
            translate=translate,
        )
    except (ASRError, DeepSeekAPIError, MissingAPIKeyError, ValueError) as exc:
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 4

    if not outputs:
        print("No speech segments were produced. Try lowering --vad-threshold or using a louder source.")
        return 5

    for output in outputs:
        if subtitle_log is not None:
            subtitle_log.append_translation(
                output.translation,
                start_time=output.asr.start_time,
                end_time=output.asr.end_time,
            )
        print(f"[Segment {output.asr.segment_id}]")
        print(f"Time: {output.asr.start_time:.2f}-{output.asr.end_time:.2f}s")
        print(f"Source: {output.asr.source_text}")
        print(f"Translation: {output.translation.translated_text}")
        print(f"Latency: {output.translation.total_latency_ms:.0f} ms")
        print("")
    return 0


def _build_streaming_pipeline_config(
    *,
    runtime_config,
    source_language: SourceLanguage,
    target_language: TargetLanguage,
    max_segments: int | None,
) -> StreamingPipelineConfig:
    language_config = _language_streaming_config(runtime_config, source_language)
    return StreamingPipelineConfig(
        source_language=source_language,
        target_language=target_language,
        asr_tick_ms=language_config.asr_tick_ms or runtime_config.streaming.asr_tick_ms,
        rolling_window_sec=runtime_config.streaming.rolling_window_sec,
        overlap_sec=runtime_config.streaming.overlap_sec,
        agreement=LocalAgreementConfig(
            source_language=source_language,
            agreement_n=runtime_config.streaming.local_agreement_n,
            min_commit_sec=runtime_config.streaming.min_commit_sec,
            max_commit_sec=language_config.max_commit_sec,
            max_unconfirmed_sec=runtime_config.streaming.max_unconfirmed_sec,
            min_commit_tokens=language_config.min_commit_tokens,
            enable_partial_subtitle=runtime_config.streaming.enable_partial_subtitle,
        ),
        enable_final_revision=runtime_config.streaming.enable_final_revision,
        max_final_segments=max_segments,
        silence_end_ms=language_config.silence_end_ms,
        silence_threshold=min(runtime_config.vad.threshold, 0.01),
    )


def _language_streaming_config(runtime_config, source_language: SourceLanguage):
    return runtime_config.streaming.ja if source_language == "ja" else runtime_config.streaming.en


def _print_streaming_event(event, subtitle_log: SubtitleLogRepository | None) -> None:
    if event.kind == "final" and subtitle_log is not None:
        subtitle_log.append_translation(
            event.translation,
            start_time=event.asr.start_time,
            end_time=event.asr.end_time,
        )
    print(f"[{event.kind.upper()}]")
    print(f"source: {event.asr.source_text}")
    print(f"translation: {event.translation.translated_text}")
    print(f"latency: {event.translation.total_latency_ms:.0f} ms")
    print("")


if __name__ == "__main__":
    raise SystemExit(main())
