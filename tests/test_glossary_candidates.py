from __future__ import annotations

import json

from yt_live_translator.core.config import DeepSeekConfig
from yt_live_translator.storage.glossary_candidate_repo import (
    GlossaryCandidate,
    GlossaryCandidateRepository,
)
from yt_live_translator.storage.glossary_repo import GlossaryRepository
from yt_live_translator.storage.subtitle_log_repo import SubtitleLogEntry
from yt_live_translator.translate.glossary_candidates import (
    DeepSeekCandidateClassifier,
    extract_glossary_candidates,
)


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_extract_candidates_from_subtitle_history() -> None:
    entries = [
        _entry("Miko fights Radahn", "Miko translation A"),
        _entry("Miko meets Radahn", "Miko translation B"),
        _entry("chat says hello", "ignored"),
    ]

    candidates = extract_glossary_candidates(entries, min_occurrences=2)

    sources = {candidate.source for candidate in candidates}
    assert "Miko" in sources
    assert "Radahn" in sources
    miko = next(candidate for candidate in candidates if candidate.source == "Miko")
    assert miko.occurrences == 2
    assert miko.inconsistent is True
    assert miko.term_type == "person"


def test_existing_glossary_terms_are_not_suggested(tmp_path) -> None:
    glossary = GlossaryRepository(tmp_path / "app.sqlite3")
    glossary.add_term(source="Miko", target_zh_tw="MikoTW", source_lang="en")

    candidates = extract_glossary_candidates(
        [_entry("Miko fights Radahn"), _entry("Miko meets Radahn")],
        glossary_repository=glossary,
        min_occurrences=2,
    )

    assert "Miko" not in {candidate.source for candidate in candidates}
    assert "Radahn" in {candidate.source for candidate in candidates}


def test_candidate_repo_accepts_and_ignores(tmp_path) -> None:
    db_path = tmp_path / "app.sqlite3"
    candidate_repo = GlossaryCandidateRepository(db_path)
    glossary_repo = GlossaryRepository(db_path)
    candidate = candidate_repo.upsert_candidate(
        GlossaryCandidate(
            source="Miko",
            source_lang="en",
            occurrences=3,
            suggested_target_zh_tw="MikoTW",
            term_type="person",
            confidence=0.8,
        )
    )

    accepted = candidate_repo.accept_candidate(candidate.id, glossary_repo)

    assert accepted.status == "accepted"
    assert glossary_repo.list_terms()[0].source == "Miko"
    ignored = candidate_repo.upsert_candidate(
        GlossaryCandidate(source="Radahn", source_lang="en", occurrences=2)
    )
    candidate_repo.ignore_candidate(ignored.id)
    rerun = candidate_repo.upsert_candidate(
        GlossaryCandidate(source="Radahn", source_lang="en", occurrences=5)
    )
    assert rerun.status == "ignored"
    assert rerun.occurrences == 2


def test_deepseek_candidate_classifier_parses_json() -> None:
    def fake_opener(request, timeout):
        return FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "items": [
                                        {
                                            "source": "Miko",
                                            "term_type": "person",
                                            "target_zh_tw": "MikoTW",
                                            "target_zh_cn": "MikoCN",
                                            "confidence": 0.91,
                                        }
                                    ]
                                }
                            )
                        }
                    }
                ]
            }
        )

    classifier = DeepSeekCandidateClassifier(
        config=DeepSeekConfig(
            api_key_env="DEEPSEEK_API_KEY",
            model="deepseek-v4-flash",
            base_url="https://api.deepseek.com",
            timeout_seconds=10,
        ),
        api_key="test-key",
        opener=fake_opener,
    )

    [classified] = classifier.classify(
        [GlossaryCandidate(source="Miko", source_lang="en", occurrences=2)]
    )

    assert classified.term_type == "person"
    assert classified.suggested_target_zh_tw == "MikoTW"
    assert classified.confidence == 0.91


def _entry(source: str, translation: str = "translation") -> SubtitleLogEntry:
    return SubtitleLogEntry(
        segment_id=1,
        source_text=source,
        translated_text=translation,
        source_language="en",
        target_language="zh-TW",
        latency_ms=1.0,
        created_at="2026-07-01T00:00:00+00:00",
    )
