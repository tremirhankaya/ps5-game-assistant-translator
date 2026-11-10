"""Translation engines.

Every engine implements the same small interface: translate(text) -> str.
The rest of the app only talks to this interface, so engines can be swapped
(Google today, a local model later) without touching anything else.
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


class GoogleEngine(Engine):
    """Google Translate through the deep-translator package.

    Free and needs no API key, but it is not an official API: too many
    requests in a short time can get the IP temporarily blocked.
    """

    name = "Google (deneysel)"
    needs_internet = True

    def __init__(self, source: str = "en", target: str = "tr") -> None:
        super().__init__(source, target)
        from deep_translator import GoogleTranslator

        self._client = GoogleTranslator(source=source, target=target)

    def translate(self, text: str) -> str:
        return self._client.translate(text)


class EchoEngine(Engine):
    """Does not translate. Used for tests and for trying the UI offline."""

    name = "Echo (test)"

    def __init__(self, source: str = "en", target: str = "tr", delay: float = 0.0) -> None:
        super().__init__(source, target)
        self.delay = delay

    def translate(self, text: str) -> str:
        if self.delay:
            time.sleep(self.delay)
        return f"[{self.target}] {text}"


def available_engines() -> list[type[Engine]]:
    from .deepl_engine import DeepLEngine
    from .local import Gemma4Engine, HyMT2Engine

    return [DeepLEngine, GoogleEngine, HyMT2Engine, Gemma4Engine, EchoEngine]
