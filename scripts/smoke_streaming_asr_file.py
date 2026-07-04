"""ASR-only streaming smoke test using a local audio file.

Simulates true streaming ASR by:
1. Reading a local audio file into PCM16Audio.
2. Slicing it into small frames (--capture-frame-ms, default 250 ms).
3. Feeding each frame into StreamingAsrSession.
4. Printing ASR partial / final events as they are produced.
5. Reporting stats at the end.

Usage::

    python scripts\\smoke_streaming_asr_file.py ^
      --audio "C:\\Users\\Owen\\Desktop\\test_miko_audio.mp3" ^
      --model models\\anime-whisper-ct2-fp16 ^
      --source-lang ja ^
      --device cuda ^
      --compute-type float16 ^
      --beam-size 3 ^
      --asr-window-seconds 6 ^
      --capture-frame-ms 250 ^
      --asr-tick-ms 1000 ^
      --no-cpu-fallback
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from yt_live_translator.core.streaming_asr_session import StreamingAsrEvent, StreamingAsrSession
from yt_live_translator.core.subtitle_pipeline import load_audio_file_as_pcm16
from yt_live_translator.speech.asr_faster_whisper import FasterWhisperTranscriber


def _slice_pcm16(audio_bytes: bytes, sample_rate: int, channels: int, start_sec: float, end_sec: float) -> bytes:
    bytes_per_second = sample_rate * channels * 2
    start_byte = int(start_sec * bytes_per_second)
    end_byte = int(end_sec * bytes_per_second)
    return audio_bytes[start_byte:end_byte]


def main() -> int:
    parser = argparse.ArgumentParser(description="Streaming ASR file smoke test")
    parser.add_argument("--audio", required=True, help="Path to local audio file")
    parser.add_argument("--model", default="models/faster-whisper-large-v3")
    parser.add_argument("--source-lang", default="ja", choices=["auto", "en", "ja"])
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--compute-type", default="float16")
    parser.add_argument("--beam-size", type=int, default=3)
    parser.add_argument("--asr-window-seconds", type=float, default=6.0)
    parser.add_argument("--capture-frame-ms", type=int, default=250)
    parser.add_argument("--asr-tick-ms", type=int, default=1000)
    parser.add_argument("--no-cpu-fallback", action="store_true")
    parser.add_argument("--max-audio-seconds", type=float, default=None)
    parser.add_argument("--temp-dir", default="work")
    parser.add_argument("--debug-log", default=None)
    parser.add_argument("--no-dedupe", action="store_true")
    parser.add_argument("--no-output-cleanup", action="store_true", help="Disable overlap trimming for debug.")
    args = parser.parse_args()

    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"Error: audio file not found: {audio_path}")
        return 1

    print(f"[smoke] loading audio: {audio_path}")
    audio = load_audio_file_as_pcm16(
        str(audio_path),
        sample_rate=16000,
        channels=1,
        max_duration_seconds=args.max_audio_seconds,
    )
    total_duration = audio.duration_seconds
    print(f"[smoke] audio loaded: {total_duration:.1f}s, {audio.frame_count} frames")

    print(f"[smoke] loading ASR model: {args.model}")
    transcriber = FasterWhisperTranscriber(
        language=args.source_lang,
        model_size=args.model,
        device=args.device,
        compute_type=args.compute_type,
        beam_size=args.beam_size,
        cpu_fallback=not args.no_cpu_fallback,
    )
    t0 = _now_ms()
    transcriber.ensure_model_loaded()
    load_ms = _now_ms() - t0
    print(
        f"[smoke] model loaded in {load_ms:.0f} ms "
        f"device={transcriber.effective_device} "
        f"compute={transcriber.effective_compute_type} "
        f"cpu_fallback={transcriber.used_cpu_fallback}"
    )

    from yt_live_translator.speech.streaming_agreement import LocalAgreementConfig

    agreement_config = LocalAgreementConfig(
        source_language=args.source_lang,
        agreement_n=2,
        min_commit_sec=1.2,
        max_commit_sec=3.0,
        max_unconfirmed_sec=4.0,
        min_commit_tokens=8 if args.source_lang == "ja" else 5,
        enable_partial_subtitle=True,
        enable_final_revision=False,
    )

    session = StreamingAsrSession(
        transcriber=transcriber,
        source_language=args.source_lang,
        sample_rate=16000,
        channels=1,
        asr_window_seconds=args.asr_window_seconds,
        asr_tick_ms=args.asr_tick_ms,
        capture_frame_ms=args.capture_frame_ms,
        agreement_config=agreement_config,
        beam_size=args.beam_size,
        temp_dir=Path(args.temp_dir),
        enable_output_cleanup=not args.no_output_cleanup,
    )

    frame_sec = args.capture_frame_ms / 1000.0
    total_events: list[StreamingAsrEvent] = []
    cursor_sec = 0.0

    while cursor_sec < total_duration:
        next_cursor = min(cursor_sec + frame_sec, total_duration)
        chunk_pcm = _slice_pcm16(audio.pcm, 16000, 1, cursor_sec, next_cursor)

        from yt_live_translator.audio.resampler import PCM16Audio

        frame = PCM16Audio(pcm=chunk_pcm, sample_rate=16000, channels=1)
        events = session.push_audio(frame, absolute_start_sec=cursor_sec)
        for event in events:
            total_events.append(event)
            _print_event(event)
        cursor_sec = next_cursor

    flush_events = session.flush()
    for event in flush_events:
        total_events.append(event)
        _print_event(event)

    stats = session.stats
    latencies = stats["asr_latencies_ms"]
    print()
    print("=" * 60)
    print("Session stats")
    print("=" * 60)
    print(f"  ASR tick count       : {stats['tick_count']}")
    print(f"  ASR skip count       : {stats['skip_count']}")
    if latencies:
        print(f"  ASR avg latency (ms) : {sum(latencies) / len(latencies):.0f}")
        print(f"  ASR max latency (ms) : {max(latencies):.0f}")
    else:
        print("  ASR avg latency (ms) : N/A")
        print("  ASR max latency (ms) : N/A")
    print(f"  Dedupe count         : {stats['dedupe_count']}")
    print(f"  Partial event count  : {stats['partial_count']}")
    print(f"  Final event count    : {stats['final_count']}")
    print(f"  Total events         : {len(total_events)}")

    return 0


def _now_ms() -> float:
    import time
    return time.perf_counter() * 1000.0


def _print_event(event: StreamingAsrEvent) -> None:
    tag = "partial" if event.is_partial else "FINAL  "
    parts = [
        f"[t={event.end_time:06.2f}s][{tag}]",
        f"seg={event.segment_id} tick={event.tick_index}",
        f"lat={event.asr_latency_ms:.0f}ms",
    ]
    if event.overlap_chars > 0:
        parts.append(f"overlap={event.overlap_chars}")
    if event.raw_source_text and event.raw_source_text != event.source_text:
        parts.append(f'raw="{event.raw_source_text[:60]}"')
        parts.append(f'clean="{event.source_text}"')
    else:
        parts.append(f'"{event.source_text}"')
    print(" ".join(parts))


if __name__ == "__main__":
    sys.exit(main())
