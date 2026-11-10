"""Automatic calibration: let OCR find the best settings.

With a subtitle visible on screen we try several settings and keep the one
OCR reads best:
1. Tilt: OCR tells us the angle of the text line; we rotate by that much.
2. Height: in partial mode the true shape is unknown, so we try a range of
   height corrections and compare the readings.
3. Area: we fit the subtitle band around the text that was found, leaving
   room for two-line subtitles.

"Reads best" is measured by `quality`: the engine's confidence (if it gives
one) times the share of words that look like real words. Confidence is not a
guarantee of correctness, but they usually rise together.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, replace

import numpy as np

from ..ocr import OcrEngine, OcrResult
from .calibration import FULL, Calibration

HEIGHT_SCALES = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.15, 1.3, 1.5, 1.75, 2.0, 2.5]
_WORD = re.compile(r"[A-Za-z']+")


@dataclass
class Trial:
    height_scale: float
    rotation: float
    text: str
    score: float | None
    quality: float = 0.0


@dataclass
class AutoTuneReport:
    trials: list[Trial]
    best: Trial | None
    band: tuple[float, float, float, float] | None
    found_text: bool


def word_quality(text: str) -> float:
    """Share of words that look like words (not single stray letters or noise)."""
    words = _WORD.findall(text)
    if not words:
        return 0.0
    good = [w for w in words if len(w) >= 2 or w.lower() in ("a", "i")]
    return len(good) / len(words)


def quality(result: OcrResult) -> float:
    if not result.text:
        return 0.0
    confidence = result.score if result.score is not None else 1.0
    return confidence * word_quality(result.text)


def _rank(trials: list[Trial]) -> Trial | None:
    """Best trial: high quality, and among similar ones the one that read the most text."""
    readable = [t for t in trials if t.text]
    if not readable:
        return None
    most_letters = max(len(_WORD.findall(t.text)) for t in readable) or 1

    def key(t: Trial) -> float:
        return t.quality * (len(_WORD.findall(t.text)) / most_letters) ** 0.5

    return max(readable, key=key)


def _read(frame: np.ndarray, calib: Calibration, engine: OcrEngine) -> OcrResult:
    crop = calib.subtitle_crop(frame)
    return engine.read(crop) if crop is not None else OcrResult()


def fit_band(calib: Calibration, frame: np.ndarray, result: OcrResult) -> tuple[float, float, float, float]:
    """A band around the text found, with room for a line above it and some margin."""
    crop = calib.subtitle_crop(frame)
    crop_h, crop_w = crop.shape[:2]
    x0, y0, x1, y1 = calib.band
    points = np.concatenate([line.box for line in result.lines])
    line_h = float(np.median([line.height for line in result.lines]))

    def fx(u: float) -> float:
        return x0 + (u / crop_w) * (x1 - x0)

    def fy(v: float) -> float:
        return y0 + (v / crop_h) * (y1 - y0)

    top, bottom = points[:, 1].min(), points[:, 1].max()
    left, right = points[:, 0].min(), points[:, 0].max()
    new_y0 = fy(top - 1.3 * line_h)  # a subtitle may grow upward by one more line
    new_y1 = fy(bottom + 0.5 * line_h)
    # Keep the band at least as wide as before: longer subtitles will be wider.
    new_x0 = min(x0, fx(left - 2 * line_h))
    new_x1 = max(x1, fx(right + 2 * line_h))
    clamp = lambda v: min(max(v, 0.0), 1.0)  # noqa: E731
    return (clamp(new_x0), clamp(new_y0), clamp(new_x1), clamp(new_y1))


def auto_calibrate(frame: np.ndarray, calib: Calibration, engine: OcrEngine) -> AutoTuneReport:
    if not calib.has_screen:
        raise ValueError("Önce ekranın köşelerini seç.")
    work = replace(calib, band=calib.band or (0.0, 0.0, 1.0, 1.0))
    trials: list[Trial] = []

    def attempt(height_scale: float, rotation: float) -> tuple[Trial, OcrResult]:
        candidate = replace(work, height_scale=height_scale, rotation=rotation)
        result = _read(frame, candidate, engine)
        trial = Trial(height_scale, rotation, result.text, result.score, quality(result))
        trials.append(trial)
        return trial, result

    # 1. Measure the tilt with the current settings.
    _, first = attempt(work.height_scale, work.rotation)
    rotation = work.rotation + (first.angle or 0.0)

    # 2. Try height corrections (only needed when the screen shape is unknown).
    scales = [work.height_scale] if work.mode == FULL else HEIGHT_SCALES
    for scale in scales:
        attempt(scale, rotation)
    best = _rank(trials)
    if best is None:
        return AutoTuneReport(trials, None, None, found_text=False)

    # 3. Fine-tune the tilt once more at the best height.
    _, check = attempt(best.height_scale, best.rotation)
    if check.angle and abs(check.angle) > 0.3:
        attempt(best.height_scale, best.rotation + check.angle)
    best = _rank(trials)

    # 4. Fit the subtitle band around the text, and keep it only if reading stays as good.
    tuned = replace(work, height_scale=best.height_scale, rotation=best.rotation)
    result = _read(frame, tuned, engine)
    band = work.band
    if result.lines:
        fitted = replace(tuned, band=fit_band(tuned, frame, result))
        refit = _read(frame, fitted, engine)
        if quality(refit) >= quality(result) * 0.95:
            band = fitted.band
    return AutoTuneReport(trials, best, band, found_text=True)
