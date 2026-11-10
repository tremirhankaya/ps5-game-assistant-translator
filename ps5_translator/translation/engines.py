"""Translation engines.

Every engine implements the same small interface: translate(text) -> str.
The app uses DeepL (see deepl_engine.py). The rest of the app only talks to
this interface, so another engine could be added later without touching
anything else.
"""
from __future__ import annotations

import time


class Engine:
    """Base class for all translation engines."""

    name = "base"
    needs_internet = False

    def __init__(self, source: str = "en", target: str = "tr") -> None:
        self.source = source
        self.target = target

    def translate(self, text: str) -> str:
        raise NotImplementedError


class EchoEngine(Engine):
    """Does not translate. Used by the tests and for trying the UI without a DeepL key."""

    name = "Echo (test)"

    def __init__(self, source: str = "en", target: str = "tr", delay: float = 0.0) -> None:
        super().__init__(source, target)
        self.delay = delay

    def translate(self, text: str) -> str:
        if self.delay:
            time.sleep(self.delay)
        return f"[{self.target}] {text}"
