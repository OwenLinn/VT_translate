"""Final subtitle rewrite helper."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from yt_live_translator.core.models import SourceLanguage, TargetLanguage


TranslateCallable = Callable[[str, SourceLanguage, TargetLanguage], str]


@dataclass(frozen=True)
class FinalSubtitleRevision:
    source_text: str
    translated_text: str
    latency_ms: float


class FinalSubtitleReviser:
    """Translate the full finalized sentence again instead of reusing deltas."""

    def __init__(self, translate: TranslateCallable) -> None:
        self._translate = translate

    def revise(
        self,
        *,
        source_text: str,
        source_language: SourceLanguage,
        target_language: TargetLanguage,
    ) -> FinalSubtitleRevision:
        start_time = time.perf_counter()
        translated_text = self._translate(source_text, source_language, target_language)
        return FinalSubtitleRevision(
            source_text=source_text,
            translated_text=translated_text,
            latency_ms=(time.perf_counter() - start_time) * 1000,
        )
