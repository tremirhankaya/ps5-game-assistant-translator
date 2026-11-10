"""Decide when an OCR reading is a finished subtitle worth translating.

The camera reads the subtitle area several times per second. Readings differ
slightly from frame to frame (camera noise), and some games type subtitles
letter by letter. We only pass a text on when it was read (almost) the same
way in consecutive readings, and only once per subtitle.
"""
from __future__ import annotations

from difflib import SequenceMatcher


def similar(a: str, b: str, threshold: float = 0.9) -> bool:
    if a == b:
        return True
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() >= threshold


class StabilityFilter:
    def __init__(self, needed: int = 2, threshold: float = 0.9, forget_after_empty: int = 3) -> None:
        self.needed = needed
        self.threshold = threshold
        self.forget_after_empty = forget_after_empty
        self._candidate = ""
        self._count = 0
        self._last_sent = ""
        self._empty = 0

    def reset(self) -> None:
        self._candidate, self._count, self._last_sent, self._empty = "", 0, "", 0

    def feed(self, text: str) -> str | None:
        """Give one OCR reading. Returns the text when it is ready to translate."""
        text = " ".join(text.split())
        if sum(ch.isalpha() for ch in text) < 2:
            self._candidate, self._count = "", 0
            self._empty += 1
            if self._empty >= self.forget_after_empty:
                self._last_sent = ""  # subtitle is gone; the same line may appear again later
            return None
        self._empty = 0

        if self._candidate and similar(text, self._candidate, self.threshold):
            self._count += 1
        else:
            self._count = 1
        self._candidate = text

        if self._count < self.needed:
            return None
        if self._last_sent and similar(text, self._last_sent, self.threshold):
            return None  # still the subtitle we already sent
        self._last_sent = text
        return text
