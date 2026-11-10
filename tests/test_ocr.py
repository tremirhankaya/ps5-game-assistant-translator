import numpy as np
import pytest

from ps5_translator.ocr import OcrEngine, OcrLine, group_lines, merge_overlap
from ps5_translator.ocr.base import upscale_factor


def frag(text, x0, y0, x1, y1, score=0.9):
    box = np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], dtype=np.float32)
    return OcrLine(text=text, box=box, score=score)


def test_overlapping_fragments_do_not_repeat_letters():
    # Real RapidOCR output on a test image: "Alright," + "lets" + "s get outta here."
    lines = group_lines([
        frag("Alright,", 0, 0, 160, 40),
        frag("lets", 170, 0, 250, 40),
        frag("s get outta here.", 235, 0, 560, 40),
    ])
    assert [l.text for l in lines] == ["Alright, lets get outta here."]


def test_two_subtitle_lines_are_kept_in_order():
    lines = group_lines([
        frag("or what?", 300, 62, 450, 100),
        frag("Franklin.", 200, 0, 380, 40),
        frag("You comin", 100, 60, 290, 100),
    ])
    assert [l.text for l in lines] == ["Franklin.", "You comin or what?"]


def test_merge_overlap_keeps_normal_words():
    assert merge_overlap("Wait a", "a minute") == "Wait a minute"
    assert merge_overlap("Hello", "there") == "Hello there"


def test_line_angle_is_measured():
    box = np.array([(0, 0), (100, 10), (100, 40), (0, 30)], dtype=np.float32)
    assert OcrLine("x", box).angle == pytest.approx(5.71, abs=0.05)


def test_small_crops_are_enlarged_and_boxes_mapped_back():
    seen = {}

    class Fake(OcrEngine):
        name = "fake"

        def recognize(self, image):
            seen["shape"] = image.shape
            h, w = image.shape[:2]
            return [frag("Hi", 0, 0, w, h)]

    result = Fake().read(np.zeros((40, 400, 3), np.uint8))
    assert seen["shape"][0] > 40  # enlarged for the engine
    assert result.lines[0].box[:, 1].max() == pytest.approx(40, abs=0.5)  # but reported in original pixels
    assert upscale_factor(np.zeros((500, 10, 3))) == 1.0


def test_result_score_only_when_every_line_has_one():
    from ps5_translator.ocr import OcrResult

    assert OcrResult([frag("a", 0, 0, 1, 1, 0.8), frag("b", 0, 5, 1, 6, 0.6)]).score == pytest.approx(0.7)
    assert OcrResult([frag("a", 0, 0, 1, 1, None)]).score is None


def test_text_at_the_border_is_flagged_as_possibly_cut_off():
    class Edge(OcrEngine):
        def __init__(self, x1):
            self.x1 = x1

        def recognize(self, image):
            return [frag("I can see tha", 100, 50, self.x1, 150)]

    image = np.zeros((200, 1000, 3), np.uint8)
    assert Edge(998).read(image).touches_edge
    assert not Edge(800).read(image).touches_edge
