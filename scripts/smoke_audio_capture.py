from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from yt_live_translator.audio.resampler import write_wav
from yt_live_translator.audio.wasapi_capture import (
    AudioCaptureError,
    capture_loopback,
    list_loopback_devices,
)
from yt_live_translator.core.config import ConfigError, load_config
from yt_live_translator.core.logging_config import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capture Windows system audio with WASAPI loopback.")
    parser.add_argument("--seconds", type=float, default=10.0, help="Capture duration in seconds.")
    parser.add_argument("--output", default="test_capture.wav", help="Output WAV path.")
    parser.add_argument("--device-index", type=int, default=None, help="Optional loopback device index.")
    parser.add_argument("--sample-rate", type=int, default=None, help="Target WAV sample rate.")
    parser.add_argument("--channels", type=int, default=None, help="Target WAV channel count.")
    parser.add_argument("--chunk-ms", type=int, default=None, help="Capture chunk size in milliseconds.")
    parser.add_argument("--list-devices", action="store_true", help="List loopback devices and exit.")
    parser.add_argument(
        "--source-hint",
        default=None,
        help="Optional note printed before capture, such as a local audio file to play manually.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    args = build_parser().parse_args(argv)

    try:
        devices = list_loopback_devices()
    except AudioCaptureError as exc:
        print(f"Audio capture error: {exc}", file=sys.stderr)
        return 2

    if not devices:
        print("Audio capture error: no WASAPI loopback devices were found", file=sys.stderr)
        return 2

    print("Detected WASAPI loopback devices:")
    for device in devices:
        default_marker = " (default)" if device.is_default else ""
        print(
            f"  [{device.index}] {device.name}{default_marker} "
            f"{device.channels}ch @ {device.sample_rate} Hz"
        )

    if args.list_devices:
        return 0

    try:
        config = load_config()
        target_sample_rate = args.sample_rate or config.audio.sample_rate
        target_channels = args.channels or config.audio.channels
        chunk_ms = args.chunk_ms or config.audio.chunk_ms
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 3

    if args.source_hint:
        print(f"Before capture, play this audio source manually if desired: {args.source_hint}")

    print(
        f"Capturing {args.seconds:g}s to {args.output} "
        f"as {target_channels}ch @ {target_sample_rate} Hz..."
    )

    try:
        result = capture_loopback(
            seconds=args.seconds,
            target_sample_rate=target_sample_rate,
            target_channels=target_channels,
            chunk_ms=chunk_ms,
            device_index=args.device_index,
        )
        write_wav(args.output, result.audio)
    except (AudioCaptureError, ValueError) as exc:
        print(f"Audio capture error: {exc}", file=sys.stderr)
        return 4

    print(
        f"Captured from [{result.device.index}] {result.device.name}: "
        f"{result.audio.duration_seconds:.2f}s written to {args.output}"
    )
    if result.silence_fallback_frames:
        print(
            "Warning: no loopback frames were available for part of the capture; "
            f"filled {result.silence_fallback_frames} native frames with silence."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
