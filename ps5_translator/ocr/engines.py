"""OCR engine.

RapidOCR: PaddleOCR models running on the CPU through onnxruntime. Reports a
confidence score per line, which automatic calibration uses. onnxruntime
currently supports Python up to 3.13.
"""
from __future__ import annotations

import numpy as np

from .base import OcrEngine, OcrLine

class OcrUnavailable(RuntimeError):
    pass


class RapidOcrEngine(OcrEngine):
    name = "RapidOCR"
    gives_scores = True

    def __init__(self) -> None:
        try:
            from rapidocr import RapidOCR
        except ImportError as exc:
            raise OcrUnavailable(
                "RapidOCR kurulu değil. setup.bat dosyasını çalıştır (Python 3.13 gerekir)."
            ) from exc
        # By default the detector enlarges the image until its short side is 736 px.
        # A subtitle band is short and very wide, so it became huge and one read took
        # seconds. 256 px keeps small or blurry text readable and is several times faster.
        # The band is already upright, so the "is the text upside down" check is skipped.
        self._engine = RapidOCR(
            params={"Det.limit_type": "min", "Det.limit_side_len": 256, "Global.use_cls": False}
        )

    def recognize(self, image: np.ndarray) -> list[OcrLine]:
        out = self._engine(image)
        if out.txts is None:
            return []
        return [
            OcrLine(text=text, box=np.array(box, dtype=np.float32), score=float(score))
            for text, box, score in zip(out.txts, out.boxes, out.scores)
        ]
