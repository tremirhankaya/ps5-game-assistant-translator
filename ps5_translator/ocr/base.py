"""Common OCR types and helpers.

OCR turns the pixels of the subtitle area into text (still in English).
Engines return text fragments with their position; we group fragments into
lines, because some engines split one line into several pieces.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import cv2
import numpy as np

# Text smaller than this (in pixels) is enlarged before OCR; most OCR models
# are trained on text roughly 30-50 pixels high.
MIN_TEXT_HEIGHT = 48


@dataclass
class OcrLine:
    text: str
    box: np.ndarray  # 4 corner points (x, y) in the image given to read()
    score: float | None = None

    @property
    def height(self) -> float:
        return float(np.linalg.norm(self.box[3] - self.box[0]))

    @property
    def angle(self) -> float:
        """Slope of the line in degrees (positive = going down to the right)."""
        (x0, y0), (x1, y1) = self.box[0], self.box[1]
        return math.degrees(math.atan2(y1 - y0, x1 - x0))


@dataclass
class OcrResult:
    lines: list[OcrLine] = field(default_factory=list)
    ms: float = 0.0
    engine: str = ""

    @property
    def text(self) -> str:
        return " ".join(line.text for line in self.lines).strip()

    @property
    def score(self) -> float | None:
        scores = [line.score for line in self.lines if line.score is not None]
        return sum(scores) / len(scores) if scores and len(scores) == len(self.lines) else None

    @property
    def angle(self) -> float | None:
        if not self.lines:
            return None
        longest = max(self.lines, key=lambda l: len(l.text))
        return longest.angle


class OcrEngine:
    name = "base"
    gives_scores = False

    def recognize(self, image: np.ndarray) -> list[OcrLine]:
        """Engine-specific part: return lines or fragments in image coordinates."""
        raise NotImplementedError

    def read(self, image: np.ndarray) -> OcrResult:
        start = time.perf_counter()
        scale = upscale_factor(image)
        work = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC) if scale > 1 else image
        lines = group_lines(self.recognize(work))
        if scale > 1:
            for line in lines:
                line.box = line.box / scale
        return OcrResult(lines=lines, ms=(time.perf_counter() - start) * 1000, engine=self.name)


def upscale_factor(image: np.ndarray) -> float:
    """Enlarge small crops so letters are big enough for the OCR model."""
    h = image.shape[0]
    if h <= 0 or h >= MIN_TEXT_HEIGHT * 3:
        return 1.0
    return min(4.0, (MIN_TEXT_HEIGHT * 3) / h)


def merge_overlap(left: str, right: str) -> str:
    """Join two fragments that overlap on the image, removing the text both
    of them read. Example: 'lets' + 's get' -> 'lets get'.
    Only called for fragments whose boxes overlap, so a shared end/start is
    the same letters read twice, not a real repetition."""
    for k in range(min(len(left), len(right)), 0, -1):
        if left.endswith(right[:k]):
            return (left + right[k:]).strip()
    return f"{left} {right}".strip()


def group_lines(fragments: list[OcrLine]) -> list[OcrLine]:
    """Put fragments on the same text line together, top to bottom, left to right."""
    fragments = [f for f in fragments if f.text.strip()]
    if not fragments:
        return []
    heights = sorted(max(f.height, 1.0) for f in fragments)
    typical = heights[len(heights) // 2]

    def center_y(f: OcrLine) -> float:
        return float(f.box[:, 1].mean())

    rows: list[list[OcrLine]] = []
    for frag in sorted(fragments, key=center_y):
        if rows and abs(center_y(frag) - np.mean([center_y(f) for f in rows[-1]])) < typical * 0.6:
            rows[-1].append(frag)
        else:
            rows.append([frag])

    lines = []
    for row in rows:
        row.sort(key=lambda f: float(f.box[:, 0].min()))
        text = row[0].text.strip()
        prev_right = float(row[0].box[:, 0].max())
        for frag in row[1:]:
            overlapping = float(frag.box[:, 0].min()) < prev_right - typical * 0.2
            text = merge_overlap(text, frag.text.strip()) if overlapping else f"{text} {frag.text.strip()}"
            prev_right = max(prev_right, float(frag.box[:, 0].max()))
        points = np.concatenate([f.box for f in row]).astype(np.float32)
        box = cv2.boxPoints(cv2.minAreaRect(points))
        scores = [f.score for f in row if f.score is not None]
        lines.append(
            OcrLine(
                text=" ".join(text.split()),
                box=_order_box(box),
                score=sum(scores) / len(scores) if len(scores) == len(row) else None,
            )
        )
    return lines


def _order_box(box: np.ndarray) -> np.ndarray:
    """Corners as top-left, top-right, bottom-right, bottom-left."""
    s = box.sum(axis=1)
    d = box[:, 1] - box[:, 0]
    return np.array([box[np.argmin(s)], box[np.argmin(d)], box[np.argmax(s)], box[np.argmax(d)]], dtype=np.float32)
