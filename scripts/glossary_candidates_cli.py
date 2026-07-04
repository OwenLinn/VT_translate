from __future__ import annotations

import argparse
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

from yt_live_translator.core.config import ConfigError, load_config
from yt_live_translator.storage.db import resolve_database_path
from yt_live_translator.storage.glossary_candidate_repo import GlossaryCandidateRepository
from yt_live_translator.storage.glossary_repo import GlossaryRepository
from yt_live_translator.storage.subtitle_log_repo import SubtitleLogRepository, resolve_subtitle_log_path
from yt_live_translator.translate.deepseek_client import DeepSeekAPIError, MissingAPIKeyError
from yt_live_translator.translate.glossary_candidates import (
    DeepSeekCandidateClassifier,
    classify_with_ai,
    extract_glossary_candidates,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract and manage glossary candidates.")
    parser.add_argument("--config", default=None)
    parser.add_argument("--db", default=None, help="Optional SQLite database path override.")
    parser.add_argument("--log", default=None, help="Optional subtitle JSONL path override.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract = subparsers.add_parser("extract", help="Extract candidates from subtitle history.")
    extract.add_argument("--min-occurrences", type=int, default=2)
    extract.add_argument("--limit", type=int, default=30)

    list_candidates = subparsers.add_parser("list", help="List saved candidates.")
    list_candidates.add_argument("--status", choices=("pending", "accepted", "ignored", "all"), default="pending")

    classify_ai = subparsers.add_parser("classify-ai", help="Classify pending candidates with DeepSeek.")
    classify_ai.add_argument("--limit", type=int, default=20)
    classify_ai.add_argument("--deepseek-timeout", type=float, default=None)

    accept = subparsers.add_parser("accept", help="Accept a candidate into the manual glossary.")
    accept.add_argument("--id", type=int, required=True)
    accept.add_argument("--target-zh-tw", default=None)
    accept.add_argument("--target-zh-cn", default=None)

    ignore = subparsers.add_parser("ignore", help="Ignore a candidate.")
    ignore.add_argument("--id", type=int, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    database_path = resolve_database_path(config, args.db)
    candidate_repo = GlossaryCandidateRepository(database_path)
    glossary_repo = GlossaryRepository(database_path)

    try:
        if args.command == "extract":
            subtitle_repo = SubtitleLogRepository(resolve_subtitle_log_path(config, args.log))
            candidates = extract_glossary_candidates(
                subtitle_repo.list_entries(),
                glossary_repository=glossary_repo,
                min_occurrences=args.min_occurrences,
                limit=args.limit,
            )
            saved = candidate_repo.upsert_many(candidates)
            _print_candidates(saved)
            return 0
        if args.command == "list":
            status = None if args.status == "all" else args.status
            _print_candidates(candidate_repo.list_candidates(status=status))
            return 0
        if args.command == "classify-ai":
            pending = candidate_repo.list_candidates(status="pending")[: args.limit]
            deepseek_config = config.deepseek
            if args.deepseek_timeout is not None:
                deepseek_config = replace(deepseek_config, timeout_seconds=args.deepseek_timeout)
            classified = classify_with_ai(
                pending,
                DeepSeekCandidateClassifier(
                    config=deepseek_config,
                    api_key=config.resolve_deepseek_api_key(),
                ),
            )
            saved = candidate_repo.upsert_many(classified)
            _print_candidates(saved)
            return 0
        if args.command == "accept":
            candidate = candidate_repo.accept_candidate(
                args.id,
                glossary_repo,
                target_zh_tw=args.target_zh_tw,
                target_zh_cn=args.target_zh_cn,
            )
            print(f"Accepted candidate #{candidate.id}: {candidate.source}")
            return 0
        if args.command == "ignore":
            candidate = candidate_repo.ignore_candidate(args.id)
            print(f"Ignored candidate #{candidate.id}: {candidate.source}")
            return 0
    except (ValueError, KeyError) as exc:
        print(f"Candidate error: {exc}", file=sys.stderr)
        return 3
    except MissingAPIKeyError as exc:
        print(f"AI classification skipped: {exc}", file=sys.stderr)
        return 4
    except DeepSeekAPIError as exc:
        print(f"AI classification failed: {exc}", file=sys.stderr)
        return 5
    return 2


def _print_candidates(candidates) -> None:
    for candidate in candidates:
        flags = []
        if candidate.inconsistent:
            flags.append("inconsistent")
        flag_text = f" {'/'.join(flags)}" if flags else ""
        print(
            f"#{candidate.id} [{candidate.status}] {candidate.source} "
            f"({candidate.source_lang}, {candidate.term_type}, "
            f"count={candidate.occurrences}, confidence={candidate.confidence:.2f}{flag_text}) "
            f"zh-TW={candidate.suggested_target_zh_tw or '-'} "
            f"zh-CN={candidate.suggested_target_zh_cn or '-'}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
