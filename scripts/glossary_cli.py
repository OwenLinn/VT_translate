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

from yt_live_translator.core.config import ConfigError, load_config
from yt_live_translator.storage.db import resolve_database_path
from yt_live_translator.storage.glossary_repo import GlossaryRepository, TERM_TYPES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage manual glossary terms.")
    parser.add_argument("--config", default=None, help="Optional path to config.toml.")
    parser.add_argument("--db", default=None, help="Optional SQLite database path override.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add = subparsers.add_parser("add", help="Add a glossary term.")
    add.add_argument("--source", required=True)
    add.add_argument("--target-zh-tw", default=None)
    add.add_argument("--target-zh-cn", default=None)
    add.add_argument("--source-lang", choices=("auto", "en", "ja"), default="auto")
    add.add_argument("--term-type", choices=TERM_TYPES, default="other")
    add.add_argument("--note", default=None)
    add.add_argument("--fuzzy", action="store_true", help="Allow simple substring matching.")
    add.add_argument("--case-sensitive", action="store_true")
    add.add_argument("--disabled", action="store_true")

    list_terms = subparsers.add_parser("list", help="List glossary terms.")
    list_terms.add_argument("--all", action="store_true", help="Include disabled terms.")

    match = subparsers.add_parser("match", help="Show active terms matching text.")
    match.add_argument("--text", required=True)
    match.add_argument("--source-lang", choices=("auto", "en", "ja"), default="auto")
    match.add_argument("--target", choices=("zh-TW", "zh-CN"), default="zh-TW")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    repository = GlossaryRepository(resolve_database_path(config, args.db))

    try:
        if args.command == "add":
            entry = repository.add_term(
                source=args.source,
                target_zh_tw=args.target_zh_tw,
                target_zh_cn=args.target_zh_cn,
                source_lang=args.source_lang,
                term_type=args.term_type,
                note=args.note,
                exact_match=not args.fuzzy,
                case_sensitive=args.case_sensitive,
                enabled=not args.disabled,
            )
            print(f"Added glossary term #{entry.id}: {entry.source}")
            return 0
        if args.command == "list":
            entries = repository.list_terms(enabled_only=not args.all)
            for entry in entries:
                status = "enabled" if entry.enabled else "disabled"
                print(
                    f"#{entry.id} [{status}] {entry.source} | "
                    f"zh-TW={entry.target_zh_tw or '-'} | zh-CN={entry.target_zh_cn or '-'}"
                )
            return 0
        if args.command == "match":
            entries = repository.find_matching_terms(
                text=args.text,
                source_language=args.source_lang,
                target_language=args.target,
            )
            for entry in entries:
                print(f"#{entry.id} {entry.source} => {entry.target_for(args.target)}")
            return 0
    except ValueError as exc:
        print(f"Glossary error: {exc}", file=sys.stderr)
        return 3

    print(f"Unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
