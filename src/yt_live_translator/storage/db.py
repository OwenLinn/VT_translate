"""SQLite database helpers for local application storage."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from yt_live_translator.core.config import RuntimeConfig, project_root


def resolve_database_path(runtime_config: RuntimeConfig, override: str | Path | None = None) -> Path:
    """Resolve the configured SQLite path relative to the project root."""

    raw_path = Path(override or runtime_config.storage.database_path)
    if raw_path.is_absolute():
        return raw_path
    return project_root() / raw_path


def connect_database(path: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection and ensure the parent directory exists."""

    database_path = Path(path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    """Create local storage tables when they do not exist."""

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS glossary_terms (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          source TEXT NOT NULL,
          target_zh_tw TEXT,
          target_zh_cn TEXT,
          source_lang TEXT,
          term_type TEXT,
          note TEXT,
          exact_match INTEGER DEFAULT 1,
          case_sensitive INTEGER DEFAULT 0,
          enabled INTEGER DEFAULT 1,
          created_at TEXT,
          updated_at TEXT
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_glossary_terms_enabled
        ON glossary_terms(enabled)
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS app_settings (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS glossary_candidates (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          source TEXT NOT NULL,
          source_lang TEXT NOT NULL,
          occurrences INTEGER NOT NULL,
          sample_text TEXT,
          translation_variants TEXT,
          inconsistent INTEGER DEFAULT 0,
          suggested_target_zh_tw TEXT,
          suggested_target_zh_cn TEXT,
          term_type TEXT DEFAULT 'other',
          confidence REAL DEFAULT 0,
          status TEXT DEFAULT 'pending',
          classifier TEXT DEFAULT 'heuristic',
          accepted_glossary_id INTEGER,
          created_at TEXT,
          updated_at TEXT,
          UNIQUE(source, source_lang)
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_glossary_candidates_status
        ON glossary_candidates(status)
        """
    )
    connection.commit()
