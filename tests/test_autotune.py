import numpy as np
import pytest

from ps5_translator.ocr import OcrEngine, OcrLine
from ps5_translator.vision import Calibration
from ps5_translator.vision.autotune import auto_calibrate, quality, word_quality
from ps5_translator.ocr import OcrResult


def make_calibration(mode="partial"):
    calib = Calibration(mode=mode)
    for p in [(0.1, 0.3), (0.9, 0.3), (0.9, 0.7), (0.1, 0.7)]:
        calib.screen.add_point(*p)
    calib.band = (0.0, 0.0, 1.0, 1.0)
    return calib


class AspectEngine(OcrEngine):
    """Fake OCR that reads best when the crop has a 4:1 shape and reports a
    2-degree tilt until the crop is rotated."""

    name = "fake"
    gives_scores = True

    def __init__(self):
        self.calls = 0

    def recognize(self, image):
        self.calls += 1
        h, w = image.shape[:2]
        score = max(0.0, 1.0 - abs(w / h - 4.0) / 4.0)
        box = np.array([(w * 0.2, h * 0.4), (w * 0.8, h * 0.4), (w * 0.8, h * 0.6), (w * 0.2, h * 0.6)], np.float32)
        return [OcrLine("Where is the key?", box, score)]


def test_word_quality_penalises_noise():
    assert word_quality("Where is the key?") == 1.0
    assert word_quality("Wait minte Frankin Wa r ng hre?") < 1.0
    assert word_quality("") == 0.0


def test_quality_uses_engine_score_when_available():
    box = np.zeros((4, 2), np.float32)
    assert quality(OcrResult([OcrLine("Hello there", box, 0.5)])) == pytest.approx(0.5)
    assert quality(OcrResult([OcrLine("Hello there", box, None)])) == pytest.approx(1.0)


def test_picks_height_that_reads_best():
    frame = np.zeros((1000, 1000, 3), np.uint8)
    calib = make_calibration()
    # Natural flat size here is 800 x 400 (2:1); the fake engine likes 4:1, so 0.5 should win.
    report = auto_calibrate(frame, calib, AspectEngine())
    assert report.found_text
    assert report.best.height_scale == pytest.approx(0.5)


def test_full_mode_does_not_search_heights():
    engine = AspectEngine()
    report = auto_calibrate(np.zeros((1000, 1000, 3), np.uint8), make_calibration("full"), engine)
    assert {t.height_scale for t in report.trials} == {1.0}


def test_no_text_is_reported():
    class Blind(OcrEngine):
        def recognize(self, image):
            return []

    report = auto_calibrate(np.zeros((500, 500, 3), np.uint8), make_calibration(), Blind())
    assert not report.found_text and report.best is None


def test_band_is_fitted_around_text_with_room_above():
    report = auto_calibrate(np.zeros((1000, 1000, 3), np.uint8), make_calibration(), AspectEngine())
    x0, y0, x1, y1 = report.band
    # Text sits at 40%-60% of the band height; the new band starts above it and ends just below.
    assert 0.0 <= y0 < 0.4 and 0.6 < y1 <= 1.0
    assert x0 == 0.0 and x1 == 1.0  # never narrower than before


def test_rotation_is_saved():
    calib = Calibration(rotation=3.5)
    assert Calibration.from_dict(calib.to_dict()).rotation == 3.5
