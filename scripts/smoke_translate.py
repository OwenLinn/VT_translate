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
from yt_live_translator.core.logging_config import configure_logging
from yt_live_translator.core.models import SourceLanguage, TargetLanguage
from yt_live_translator.translate.deepseek_client import (
    DeepSeekAPIError,
    DeepSeekClient,
    MissingAPIKeyError,
)
from yt_live_translator.translate.glossary_apply import (
    open_glossary_repository,
    translate_with_glossary,
)


DEFAULT_TEXT = "Hello everyone, welcome to the stream."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a DeepSeek translation smoke test.")
    parser.add_argument("--text", default=DEFAULT_TEXT, help="Text to translate.")
    parser.add_argument(
        "--target",
        choices=("zh-TW", "zh-CN"),
        default=None,
        help="Target language. Defaults to app.target_language from config.",
    )
    parser.add_argument(
        "--source-lang",
        choices=("auto", "en", "ja"),
        default=None,
        help="Source language. Defaults to app.source_language from config.",
    )
    parser.add_argument("--config", default=None, help="Optional path to config.toml.")
    parser.add_argument("--glossary-db", default=None, help="Optional SQLite glossary database path.")
    parser.add_argument("--no-glossary", action="store_true", help="Disable glossary matching.")
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    args = build_parser().parse_args(argv)

    try:
        config = load_config(args.config)
        target_language: TargetLanguage = args.target or config.app.target_language
        source_language: SourceLanguage = args.source_lang or config.app.source_language
        client = DeepSeekClient(
            config=config.deepseek,
            api_key=config.resolve_deepseek_api_key(),
        )
        repository = None if args.no_glossary else open_glossary_repository(
            config,
            args.glossary_db,
        )
        translated_text = translate_with_glossary(
            client,
            text=args.text,
            target_language=target_language,
            source_language=source_language,
            repository=repository,
        )
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2
    except MissingAPIKeyError as exc:
        print(f"Translation smoke test skipped: {exc}", file=sys.stderr)
        return 3
    except DeepSeekAPIError as exc:
        print(f"Translation smoke test failed: {exc}", file=sys.stderr)
        return 4

    print(translated_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
