"""Streaming Translation Worker v1 — hardened with backpressure.

Provides a background worker that decouples ASR event production from
DeepSeek (or other provider) translation, so ASR ticks are not blocked
by network/API latency.

Hardening + Backpressure v1 adds:
- Live lag metrics (queue_wait_ms, display_lag_ms, queue_depth)
- Final queue bounded (drop oldest on overflow)
- Pre-translate age check (drop stale before API call)
- Post-translate display_lag check (drop if falling behind)
- Fallback (source==translated) guard: no emit for non-echo
- Partial always superseded by latest
- Enhanced per-event stats logging
"""

from __future__ import annotations

import queue
import re
import threading
import time
from dataclasses import dataclass
from typing import Callable, Literal


@dataclass
class StreamingTranslationTask:
    task_id: int
    generation: int
    kind: Literal["partial", "final"]
    segment_id: int
    source_text: str
    source_language: str
    target_language: str
    asr_latency_ms: float
    start_time: float
    end_time: float
    created_at_monotonic: float


@dataclass
class StreamingTranslationResult:
    task_id: int
    generation: int
    kind: Literal["partial", "final"]
    segment_id: int
    source_text: str
    translated_text: str
    source_language: str
    target_language: str
    asr_latency_ms: float
    translation_latency_ms: float
    total_latency_ms: float
    queue_wait_ms: float
    display_lag_ms: float
    start_time: float
    end_time: float
    stale: bool = False
    error: str | None = None


_JA_TRANSLATION_ALLOW_SHORT = frozenset(
    ("はい", "いや", "え？", "え?", "ありがとう", "あはは", "ふふっ", "うん", "ええ", "そう", "はい。")
)


def _normalize_japanese(text: str) -> str:
    result: list[str] = []
    for ch in text:
        cp = ord(ch)
        if (
            0x4E00 <= cp <= 0x9FFF
            or 0x3040 <= cp <= 0x309F
            or 0x30A0 <= cp <= 0x30FF
            or 0x0020 <= cp <= 0x007E
        ):
            result.append(ch)
    return "".join(result)


def _is_too_short_for_translation(text: str, source_language: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if stripped in _JA_TRANSLATION_ALLOW_SHORT:
        return False
    if source_language in ("ja", "auto"):
        norm = _normalize_japanese(stripped)
        if len(norm) < 5:
            return True
    else:
        words = stripped.split()
        if len(words) < 3 and len(stripped) < 10:
            return True
    return False


_SIMPLIFIED_TO_TRADITIONAL = {
    "这": "這",
    "边": "邊",
    "转": "轉",
    "场": "場",
    "么": "麼",
}

_RE_LI_SIMPLIFIED = re.compile(r"里(?![面邊頭])")


def _post_process_zh_tw(text: str) -> str:
    if not text:
        return text
    result = text
    for simp, trad in _SIMPLIFIED_TO_TRADITIONAL.items():
        result = result.replace(simp, trad)
    result = _RE_LI_SIMPLIFIED.sub("裡", result)
    return result


class StreamingTranslationWorker:
    def __init__(
        self,
        *,
        translate: Callable[[str, str, str], str],
        on_result: Callable[[StreamingTranslationResult], None],
        source_language: str,
        target_language: str,
        session_started_monotonic: float,
        partial_timeout_seconds: float = 4.0,
        final_timeout_seconds: float = 6.0,
        max_final_queue: int = 2,
        max_task_age_ms: float = 6000.0,
        max_display_lag_ms: float = 10000.0,
        update_status: Callable[[str], None] | None = None,
        append_log: Callable[[str], None] | None = None,
    ) -> None:
        self._translate = translate
        self._on_result = on_result
        self._source_language = source_language
        self._target_language = target_language
        self._session_started = session_started_monotonic
        self._partial_timeout = partial_timeout_seconds
        self._final_timeout = final_timeout_seconds
        self._max_final_queue = max_final_queue
        self._max_task_age_ms = max_task_age_ms
        self._max_display_lag_ms = max_display_lag_ms
        self._update_status = update_status
        self._append_log = append_log

        self._final_queue: queue.Queue[StreamingTranslationTask] = queue.Queue()
        self._final_queue_depth = 0
        self._final_queue_lock = threading.Lock()

        self._partial_lock = threading.Lock()
        self._latest_partial_task: StreamingTranslationTask | None = None
        self._partial_generation: int = 0

        self._task_counter: int = 0
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        self._last_emitted_translation: str = ""

        self._stats: dict[str, int] = {
            "partial_submitted": 0,
            "partial_replaced": 0,
            "partial_emitted": 0,
            "partial_dropped_stale": 0,
            "partial_dropped_empty": 0,
            "partial_dropped_timeout": 0,
            "partial_dropped_short": 0,
            "partial_dropped_age": 0,
            "final_submitted": 0,
            "final_emitted": 0,
            "final_dropped_empty": 0,
            "final_dropped_timeout": 0,
            "final_dropped_short": 0,
            "final_dropped_age": 0,
            "final_dropped_overflow": 0,
            "final_dropped_lag": 0,
            "empty_fallback_count": 0,
            "duplicate_skipped": 0,
            "timeout_count": 0,
            "fallback_dropped": 0,
        }

    @property
    def stats(self) -> dict[str, int]:
        return dict(self._stats)

    @property
    def queue_depth(self) -> int:
        with self._final_queue_lock:
            return self._final_queue_depth + (1 if self._latest_partial_task is not None else 0)

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, name="streaming-translation-worker", daemon=True
        )
        self._thread.start()
        self._log(
            f"[translation-worker] started "
            f"max_final_q={self._max_final_queue} "
            f"max_age_ms={self._max_task_age_ms:.0f} "
            f"max_lag_ms={self._max_display_lag_ms:.0f}"
        )

    def submit_partial(
        self,
        *,
        segment_id: int,
        source_text: str,
        asr_latency_ms: float,
        start_time: float,
        end_time: float,
    ) -> None:
        if _is_too_short_for_translation(source_text, self._source_language):
            self._stats["partial_dropped_short"] += 1
            self._log(
                f'[translation-worker] drop short partial seg={segment_id} text="{source_text[:40]}"'
            )
            return

        with self._partial_lock:
            self._partial_generation += 1
            gen = self._partial_generation
            self._stats["partial_submitted"] += 1
            if self._latest_partial_task is not None:
                self._stats["partial_replaced"] += 1
                self._log(
                    "[translation-worker] replace pending partial "
                    f"old_seg={self._latest_partial_task.segment_id} new_seg={segment_id} gen={gen}"
                )
            self._task_counter += 1
            task = StreamingTranslationTask(
                task_id=self._task_counter,
                generation=gen,
                kind="partial",
                segment_id=segment_id,
                source_text=source_text,
                source_language=self._source_language,
                target_language=self._target_language,
                asr_latency_ms=asr_latency_ms,
                start_time=start_time,
                end_time=end_time,
                created_at_monotonic=time.monotonic(),
            )
            self._latest_partial_task = task
        self._log(
            f'[translation-worker] submit partial seg={segment_id} gen={gen} '
            f'chars={len(source_text)} qd={self.queue_depth}'
        )

    def submit_final(
        self,
        *,
        segment_id: int,
        source_text: str,
        asr_latency_ms: float,
        start_time: float,
        end_time: float,
    ) -> None:
        if _is_too_short_for_translation(source_text, self._source_language):
            self._stats["final_dropped_short"] += 1
            self._log(
                f'[translation-worker] drop short final seg={segment_id} text="{source_text[:40]}"'
            )
            return

        self._task_counter += 1
        task = StreamingTranslationTask(
            task_id=self._task_counter,
            generation=0,
            kind="final",
            segment_id=segment_id,
            source_text=source_text,
            source_language=self._source_language,
            target_language=self._target_language,
            asr_latency_ms=asr_latency_ms,
            start_time=start_time,
            end_time=end_time,
            created_at_monotonic=time.monotonic(),
        )

        with self._final_queue_lock:
            if self._final_queue_depth >= self._max_final_queue:
                self._stats["final_dropped_overflow"] += 1
                try:
                    self._final_queue.get_nowait()
                except queue.Empty:
                    pass
                self._final_queue_depth -= 1
                self._log(
                    f"[translation-worker] drop oldest final due queue overflow "
                    f"new_seg={segment_id} max={self._max_final_queue}"
                )
            self._final_queue.put(task)
            self._final_queue_depth += 1

        self._stats["final_submitted"] += 1
        self._log(
            f'[translation-worker] submit final seg={segment_id} '
            f'chars={len(source_text)} qd={self.queue_depth}'
        )

    def stop(self, *, drain_final: bool = True) -> None:
        self._stop_event.set()
        if drain_final:
            self._final_queue.put(_sentinel_task())
        if self._thread is not None:
            self._thread.join(timeout=15.0)
            self._thread = None
        self._log(
            f"[translation-worker] stopped "
            f"final_emitted={self._stats['final_emitted']} "
            f"partial_emitted={self._stats['partial_emitted']} "
            f"stale={self._stats['partial_dropped_stale']} "
            f"empty={self._stats['partial_dropped_empty'] + self._stats['final_dropped_empty']} "
            f"timeout={self._stats['timeout_count']} "
            f"dup={self._stats['duplicate_skipped']} "
            f"short={self._stats['partial_dropped_short'] + self._stats['final_dropped_short']} "
            f"age={self._stats['partial_dropped_age'] + self._stats['final_dropped_age']} "
            f"overflow={self._stats['final_dropped_overflow']} "
            f"lag={self._stats['final_dropped_lag']} "
            f"fb_drop={self._stats['fallback_dropped']}"
        )

    def _now_monotonic_ms(self) -> float:
        return (time.monotonic() - self._session_started) * 1000.0

    def _task_age_ms(self, task: StreamingTranslationTask) -> float:
        return (time.monotonic() - task.created_at_monotonic) * 1000.0

    def _display_lag_ms(self, end_time: float) -> float:
        return self._now_monotonic_ms() - end_time * 1000.0

    def _run(self) -> None:
        while not self._stop_event.is_set():
            task: StreamingTranslationTask | None = None

            try:
                task = self._final_queue.get(timeout=0.1)
            except queue.Empty:
                pass

            if task is not None:
                if task is _sentinel_task():
                    break
                with self._final_queue_lock:
                    self._final_queue_depth -= 1
                self._process_task(task)
                continue

            partial = self._take_partial()
            if partial is not None:
                self._process_task(partial)

    def _take_partial(self) -> StreamingTranslationTask | None:
        with self._partial_lock:
            task = self._latest_partial_task
            self._latest_partial_task = None
            return task

    def _process_task(self, task: StreamingTranslationTask) -> None:
        queue_wait_ms = self._task_age_ms(task)

        if queue_wait_ms > self._max_task_age_ms:
            if task.kind == "partial":
                self._stats["partial_dropped_age"] += 1
            else:
                self._stats["final_dropped_age"] += 1
            self._log(
                f"[translation-worker] drop stale {task.kind} before translate "
                f"seg={task.segment_id} age_ms={queue_wait_ms:.0f}"
            )
            return

        timeout = self._partial_timeout if task.kind == "partial" else self._final_timeout

        result_container: list[tuple[str, float]] = []
        error_container: list[str] = []

        def _translate_inner() -> None:
            try:
                translated = self._translate(
                    task.source_text,
                    task.source_language,
                    task.target_language,
                )
                result_container.append((translated, 0.0))
            except Exception as exc:
                error_container.append(str(exc))

        translate_thread = threading.Thread(target=_translate_inner, daemon=True)
        t0 = time.monotonic()
        translate_thread.start()
        translate_thread.join(timeout=timeout)

        translation_call_ms = (time.monotonic() - t0) * 1000.0

        if translate_thread.is_alive():
            self._stats["timeout_count"] += 1
            if task.kind == "partial":
                self._stats["partial_dropped_timeout"] += 1
            else:
                self._stats["final_dropped_timeout"] += 1
                self._stats["fallback_dropped"] += 1
            self._log(
                f"[translation-worker] timeout {task.kind} seg={task.segment_id} "
                f"call_ms={translation_call_ms:.0f} q_wait={queue_wait_ms:.0f}"
            )
            return

        if error_container:
            self._log(
                f"[translation-worker] error {task.kind} seg={task.segment_id} "
                f"err={error_container[0][:80]}"
            )
            if task.kind == "final":
                self._stats["final_dropped_empty"] += 1
            return

        translated = result_container[0][0]
        translation_call_ms = (time.monotonic() - t0) * 1000.0
        translated = (translated or "").strip()

        if not translated:
            if task.kind == "partial":
                self._stats["partial_dropped_empty"] += 1
                self._log(
                    f"[translation-worker] empty translation dropped "
                    f"partial seg={task.segment_id}"
                )
            else:
                self._stats["final_dropped_empty"] += 1
                self._log(
                    f"[translation-worker] empty translation dropped "
                    f"final seg={task.segment_id}"
                )
            return

        if self._target_language == "zh-TW":
            translated = _post_process_zh_tw(translated)

        untranslated = _is_untranslated(task.source_text, translated, self._source_language, self._target_language)

        if untranslated:
            if task.kind == "partial":
                self._stats["fallback_dropped"] += 1
                self._log(
                    f"[translation-worker] drop untranslated fallback partial "
                    f"seg={task.segment_id}"
                )
                return

            self._log(
                f"[translation-worker] retry untranslated final "
                f"seg={task.segment_id} src=\"{task.source_text[:40]}\" "
                f"tr=\"{translated[:40]}\""
            )
            translated = self._translate_retry(task)
            if translated and self._target_language == "zh-TW":
                translated = _post_process_zh_tw(translated)
            untranslated = _is_untranslated(
                task.source_text, translated, self._source_language, self._target_language
            )
            if untranslated:
                self._stats["fallback_dropped"] += 1
                self._log(
                    f"[translation-worker] drop untranslated fallback final "
                    f"seg={task.segment_id} retry_failed"
                )
                return

        total_latency_ms = task.asr_latency_ms + translation_call_ms

        if task.kind == "partial":
            with self._partial_lock:
                if task.generation != self._partial_generation:
                    self._stats["partial_dropped_stale"] += 1
                    self._log(
                        f"[translation-worker] drop stale partial result "
                        f"seg={task.segment_id} gen={task.generation} "
                        f"latest={self._partial_generation}"
                    )
                    return
            self._stats["partial_emitted"] += 1
        else:
            display_lag = self._display_lag_ms(task.end_time)
            if display_lag > self._max_display_lag_ms:
                self._stats["final_dropped_lag"] += 1
                self._log(
                    f"[translation-worker] drop final result (display lag) "
                    f"seg={task.segment_id} display_lag_ms={display_lag:.0f}"
                )
                return
            self._stats["final_emitted"] += 1

        if self._is_duplicate_translation(translated):
            self._stats["duplicate_skipped"] += 1
            self._log(
                f"[translation-worker] duplicate translation skipped "
                f'seg={task.segment_id} tr="{translated[:40]}"'
            )
            return
        self._last_emitted_translation = translated

        display_lag = self._display_lag_ms(task.end_time)
        result = StreamingTranslationResult(
            task_id=task.task_id,
            generation=task.generation,
            kind=task.kind,
            segment_id=task.segment_id,
            source_text=task.source_text,
            translated_text=translated,
            source_language=task.source_language,
            target_language=task.target_language,
            asr_latency_ms=task.asr_latency_ms,
            translation_latency_ms=translation_call_ms,
            total_latency_ms=total_latency_ms,
            queue_wait_ms=queue_wait_ms,
            display_lag_ms=display_lag,
            start_time=task.start_time,
            end_time=task.end_time,
        )
        self._log(
            f"[translation-worker] done {task.kind} seg={task.segment_id} "
            f"q_wait={queue_wait_ms:.0f}ms "
            f"tr_call={translation_call_ms:.0f}ms "
            f"total_lat={total_latency_ms:.0f}ms "
            f"display_lag={display_lag:.0f}ms "
            f"qd={self.queue_depth}"
        )
        self._on_result(result)

    def _translate_retry(self, task: StreamingTranslationTask) -> str:
        try:
            translated = self._translate(
                task.source_text,
                task.source_language,
                task.target_language,
            )
            return (translated or "").strip()
        except Exception as exc:
            self._log(
                f"[translation-worker] retry failed seg={task.segment_id} "
                f"err={str(exc)[:80]}"
            )
            return ""

    def _is_duplicate_translation(self, translated: str) -> bool:
        if not translated or not self._last_emitted_translation:
            return False
        return translated == self._last_emitted_translation

    def _log(self, message: str) -> None:
        if self._append_log:
            self._append_log(message)


_SENTINEL = object()


def _sentinel_task() -> StreamingTranslationTask:
    return StreamingTranslationTask(
        task_id=-1,
        generation=-1,
        kind="final",
        segment_id=-1,
        source_text="",
        source_language="",
        target_language="",
        asr_latency_ms=0,
        start_time=0,
        end_time=0,
        created_at_monotonic=0,
    )


def _japanese_kana_ratio(text: str) -> float:
    if not text:
        return 0.0
    kana_count = 0
    total = 0
    for ch in text:
        cp = ord(ch)
        if cp <= 0x0020:
            continue
        total += 1
        if 0x3040 <= cp <= 0x30FF:
            kana_count += 1
    if total == 0:
        return 0.0
    return kana_count / total


def _is_untranslated(
    source_text: str,
    translated_text: str,
    source_language: str,
    target_language: str,
) -> bool:
    if target_language == source_language:
        return False
    if not translated_text:
        return True
    src = source_text.strip()
    tr = translated_text.strip()
    if src == tr:
        return True

    if source_language in ("ja", "auto"):
        src_norm = _normalize_japanese(src)
        tr_norm = _normalize_japanese(tr)
        if len(tr_norm) >= 4 and len(src_norm) >= 4 and tr_norm == src_norm:
            return True
        kana_ratio = _japanese_kana_ratio(tr)
        if kana_ratio > 0.5 and "zh" in target_language:
            return True

    return False
