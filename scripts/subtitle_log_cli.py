from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from yt_live_translator.core.config import ConfigError, load_config
from yt_live_translator.storage.subtitle_log_repo import (
    SubtitleLogEntry,
    SubtitleLogRepository,
    resolve_subtitle_log_path,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage subtitle history logs.")
    parser.add_argument("--config", default=None)
    parser.add_argument("--log", default=None, help="Optional JSONL subtitle log path.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    append = subparsers.add_parser("append", help="Append a subtitle entry.")
    append.add_argument("--segment-id", type=int, default=1)
    append.add_argument("--source", required=True)
    append.add_argument("--translation", required=True)
    append.add_argument("--source-lang", default="auto")
    append.add_argument("--target", choices=("zh-TW", "zh-CN"), default="zh-TW")
    append.add_argument("--latency-ms", type=float, default=0.0)
    append.add_argument("--start", type=float, default=None)
    append.add_argument("--end", type=float, default=None)

    subparsers.add_parser("list", help="List subtitle log entries.")

    export_txt = subparsers.add_parser("export-txt", help="Export subtitle log as text.")
    export_txt.add_argument("--output", required=True)

    export_srt = subparsers.add_parser("export-srt", help="Export subtitle log as SRT.")
    export_srt.add_argument("--output", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    repository = SubtitleLogRepository(resolve_subtitle_log_path(config, args.log))
    if args.command == "append":
        repository.append(
            SubtitleLogEntry(
                segment_id=args.segment_id,
                source_text=args.source,
                translated_text=args.translation,
                source_language=args.source_lang,
                target_language=args.target,
                latency_ms=args.latency_ms,
                start_time=args.start,
                end_time=args.end,
                created_at=datetime.now(UTC).isoformat(timespec="seconds"),
            )
        )
        print(f"Appended subtitle segment #{args.segment_id}")
        return 0
    if args.command == "list":
        for entry in repository.list_entries():
            print(f"#{entry.segment_id} {entry.source_text} => {entry.translated_text}")
        return 0
    if args.command == "export-txt":
        print(repository.export_txt(args.output))
        return 0
    if args.command == "export-srt":
        print(repository.export_srt(args.output))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
