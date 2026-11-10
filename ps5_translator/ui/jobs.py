"""Run slow work (OCR, network, model loading) off the UI thread."""
from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class _Signals(QObject):
    done = Signal(object)


class _Job(QRunnable):
    def __init__(self, fn: Callable[[], Any]) -> None:
        super().__init__()
        self.fn = fn
        self.signals = _Signals()
        self.setAutoDelete(False)

    def run(self) -> None:
        try:
            outcome = (True, self.fn())
        except Exception as exc:
            outcome = (False, str(exc) or exc.__class__.__name__)
        try:
            self.signals.done.emit(outcome)
        except RuntimeError:
            pass  # the window was closed while this job was running; nobody is waiting for the result


class JobRunner(QObject):
    """A small worker pool. Jobs run in order on `threads` worker threads and
    report back on the UI thread as (ok, value_or_error_message)."""

    def __init__(self, threads: int = 1) -> None:
        super().__init__()
        self._pool = QThreadPool()
        self._pool.setMaxThreadCount(threads)
        self._jobs: set[_Job] = set()  # keep jobs alive until they report back

    def run(self, fn: Callable[[], Any], callback: Callable[[tuple[bool, Any]], None]) -> None:
        job = _Job(fn)
        self._jobs.add(job)
        job.signals.done.connect(callback)
        job.signals.done.connect(lambda _: self._jobs.discard(job))
        self._pool.start(job)

    def wait(self, ms: int = 10000) -> None:
        self._pool.waitForDone(ms)
