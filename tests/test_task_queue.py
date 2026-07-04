from __future__ import annotations

from yt_live_translator.core.task_queue import TaskQueue


def test_task_queue_returns_none_on_timeout() -> None:
    queue: TaskQueue[int] = TaskQueue(name="test")

    assert queue.get(timeout=0.001) is None


def test_task_queue_round_trip() -> None:
    queue: TaskQueue[str] = TaskQueue(name="test")

    queue.put("item")

    assert queue.qsize() == 1
    assert queue.get(timeout=0.001) == "item"
    queue.task_done()
    assert queue.empty()
