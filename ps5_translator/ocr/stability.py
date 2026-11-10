"""Decide when an OCR reading is a finished subtitle worth translating.

The camera reads the subtitle area several times per second. Readings differ
slightly from frame to frame (camera noise), and some games type subtitles
letter by letter. We only pass a text on when it was read (almost) the same
way in consecutive readings, and only once per subtitle.

Fast path: a reading that OCR is very sure about and that ends like a finished
sentence is passed on at once, without waiting for a second reading. If a later
reading turns out different, it is simply sent as a new line.
"""
from __future__ import annotations

from difflib import SequenceMatcher


SENTENCE_END = ".?!…\"'”’"
FAST_SCORE = 0.95


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
        self._first_seen: float | None = None
        self.sent_first_seen: float | None = None  # when the line just sent was first read
        self.sent_fast = False

    def reset(self) -> None:
        self._candidate, self._count, self._last_sent, self._empty = "", 0, "", 0

    def feed(self, text: str, score: float | None = None, when: float | None = None) -> str | None:
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
            self._first_seen = when
        self._candidate = text

        if self._last_sent and similar(text, self._last_sent, self.threshold):
            return None  # still the subtitle we already sent
        fast = self._count == 1 and score is not None and score >= FAST_SCORE and text[-1] in SENTENCE_END
        if self._count < self.needed and not fast:
            return None
        self._last_sent = text
        self.sent_first_seen = self._first_seen
        self.sent_fast = fast
        return text
