"""Small typed queue wrapper used by staged pipeline workers."""

from __future__ import annotations

from dataclasses import dataclass
from queue import Empty, Queue
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass
class TaskQueue(Generic[T]):
    name: str

    def __post_init__(self) -> None:
        self._queue: Queue[T] = Queue()

    def put(self, item: T) -> None:
        self._queue.put(item)

    def get(self, timeout: float | None = None) -> T | None:
        try:
            return self._queue.get(timeout=timeout)
        except Empty:
            return None

    def task_done(self) -> None:
        self._queue.task_done()

    def empty(self) -> bool:
        return self._queue.empty()

    def qsize(self) -> int:
        return self._queue.qsize()
