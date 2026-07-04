# Glossary Design

## Purpose

The glossary prevents incorrect translations of names, game terms, characters,
abilities, items, and places.

## Data Fields

Each term should include:

- source
- target_zh_tw
- target_zh_cn
- source_lang
- term_type
- note
- exact_match
- case_sensitive
- enabled
- created_at
- updated_at

## SQLite Table

```sql
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
);
```

## Term Types

- person
- game
- character
- ability
- item
- place
- organization
- technical
- slang
- other

## Application Strategy

Use two layers:

1. Prompt injection: include matched active glossary terms in translation request.
2. Conservative post-processing: only force replace terms when the match is clear.

## Important Rule

Manual glossary entries always have higher priority than AI suggestions.
