from __future__ import annotations

from yt_live_translator.speech.streaming_agreement import LocalAgreement, LocalAgreementConfig


def test_common_prefix_yields_confirmed_delta_after_two_hypotheses() -> None:
    agreement = LocalAgreement(
        LocalAgreementConfig(source_language="en", min_commit_tokens=2, max_commit_sec=10)
    )

    first = agreement.update("Hello stream friends today", now_sec=0.0)
    second = agreement.update("Hello stream friends tomorrow", now_sec=0.5)

    assert first.confirmed_delta == ""
    assert second.confirmed_delta == "Hello stream friends"
    assert second.unconfirmed_tail == "tomorrow"


def test_tail_rewrite_is_not_committed_until_stable() -> None:
    agreement = LocalAgreement(
        LocalAgreementConfig(source_language="en", min_commit_tokens=4, max_commit_sec=10)
    )

    agreement.update("we are going left", now_sec=0.0)
    update = agreement.update("we are going right", now_sec=0.5)

    assert update.confirmed_delta == ""
    assert update.unconfirmed_tail == "we are going right"


def test_english_prefix_matches_words_and_ignores_case() -> None:
    agreement = LocalAgreement(
        LocalAgreementConfig(source_language="en", min_commit_tokens=2, max_commit_sec=10)
    )

    agreement.update("Hello WORLD streamer", now_sec=0.0)
    update = agreement.update("hello world stage", now_sec=0.5)

    assert update.confirmed_delta == "hello world"
    assert update.unconfirmed_tail == "stage"


def test_japanese_prefix_uses_character_prefix() -> None:
    agreement = LocalAgreement(
        LocalAgreementConfig(source_language="ja", min_commit_tokens=4, max_commit_sec=10)
    )

    agreement.update("今日は楽しい配信です", now_sec=0.0)
    update = agreement.update("今日は楽しいゲームです", now_sec=0.5)

    assert update.confirmed_delta == "今日は楽しい"
    assert update.unconfirmed_tail == "ゲームです"


def test_auto_language_uses_character_prefix_for_japanese_text() -> None:
    agreement = LocalAgreement(
        LocalAgreementConfig(source_language="auto", min_commit_tokens=4, max_commit_sec=10)
    )

    agreement.update("今日は楽しい配信です", now_sec=0.0)
    update = agreement.update("今日は楽しいゲームです", now_sec=0.5)

    assert update.confirmed_delta == "今日は楽しい"
    assert update.unconfirmed_tail == "ゲームです"


def test_punctuation_triggers_final() -> None:
    agreement = LocalAgreement(
        LocalAgreementConfig(source_language="en", min_commit_tokens=2, max_commit_sec=10)
    )

    agreement.update("hello world.", now_sec=0.0)
    update = agreement.update("hello world.", now_sec=0.5)

    assert update.should_finalize is True
    assert update.final_text == "hello world."


def test_timeout_triggers_final() -> None:
    agreement = LocalAgreement(
        LocalAgreementConfig(source_language="en", min_commit_tokens=20, max_commit_sec=2.0)
    )

    agreement.update("this sentence keeps going", now_sec=0.0)
    update = agreement.update("this sentence keeps going", now_sec=2.1)

    assert update.should_finalize is True
    assert update.final_text == "this sentence keeps going"


def test_does_not_resubmit_confirmed_text() -> None:
    agreement = LocalAgreement(
        LocalAgreementConfig(source_language="en", min_commit_tokens=2, max_commit_sec=10)
    )

    agreement.update("hello stream today", now_sec=0.0)
    first = agreement.update("hello stream tomorrow", now_sec=0.5)
    second = agreement.update("hello stream tomorrow friends", now_sec=1.0)

    assert first.confirmed_delta == "hello stream"
    assert second.confirmed_delta == ""
    assert second.unconfirmed_tail == "tomorrow friends"
