"""Translation pipeline: normalize -> skip repeats -> cache -> engine.

Each step records an Event. The UI turns events into short explanations
so the user can follow what the app is doing and why.
"""
from __future__ import annotations

import re
import time
from collections import OrderedDict
from dataclasses import dataclass, field

from .engines import Engine

_WHITESPACE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Join subtitle lines into one sentence and clean up spacing."""
    text = text.replace("-\n", "")  # word split across two lines
    return _WHITESPACE.sub(" ", text).strip()


@dataclass
class Event:
    """Something the pipeline did. `code` selects the explanation text."""

    code: str
    detail: dict = field(default_factory=dict)


@dataclass
class Result:
    source: str
    translated: str = ""
    ms: float = 0.0
    from_cache: bool = False
    skipped: bool = False
    error: str | None = None
    events: list[Event] = field(default_factory=list)


class TranslationPipeline:
    def __init__(self, engine: Engine, cache_size: int = 500) -> None:
        self.engine = engine
        self._cache: OrderedDict[str, str] = OrderedDict()
        self._cache_size = cache_size
        self._last: str | None = None

    def set_engine(self, engine: Engine) -> None:
        self.engine = engine
        self._cache.clear()
        self._last = None

    def process(self, raw: str) -> Result | None:
        text = normalize(raw)
        if not text:
            return None

        result = Result(source=text)
        if text != raw:
            result.events.append(Event("normalized", {"before": raw, "after": text}))

        if text == self._last:
            result.skipped = True
            result.events.append(Event("repeat_skipped"))
            return result
        self._last = text

        start = time.perf_counter()
        cached = self._cache.get(text)
        if cached is not None:
            self._cache.move_to_end(text)
            result.translated = cached
            result.from_cache = True
            result.ms = (time.perf_counter() - start) * 1000
            result.events.append(Event("cache_hit", {"ms": result.ms}))
            return result

        result.events.append(Event("engine_call", {"engine": self.engine.name}))
        try:
            translated = self.engine.translate(text)
        except Exception as exc:  # network errors, blocked IP, etc.
            result.error = str(exc) or exc.__class__.__name__
            result.events.append(Event("engine_error", {"engine": self.engine.name, "error": result.error}))
            self._last = None  # allow a retry of the same line
            return result

        result.ms = (time.perf_counter() - start) * 1000
        result.translated = translated
        result.events.append(Event("translated", {"engine": self.engine.name, "ms": result.ms}))

        self._cache[text] = translated
        if len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)
        return result
