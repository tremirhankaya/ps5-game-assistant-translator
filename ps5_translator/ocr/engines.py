"""OCR engines.

Windows OCR: built into Windows 10/11, no model download, fast. Needs the
English OCR language pack. Does not report how sure it is (no score).

RapidOCR: PaddleOCR models running on the CPU through onnxruntime. Reports a
confidence score per line, which automatic calibration uses. onnxruntime
currently supports Python up to 3.13.
"""
from __future__ import annotations

import asyncio

import cv2
import numpy as np

from .base import OcrEngine, OcrLine

ENGLISH_PACK_COMMAND = 'Add-WindowsCapability -Online -Name "Language.OCR~~~en-US~0.0.1.0"'


class OcrUnavailable(RuntimeError):
    pass


class WindowsOcrEngine(OcrEngine):
    name = "Windows OCR"
    gives_scores = False

    def __init__(self, language: str = "en") -> None:
        try:
            from winrt.windows.globalization import Language
            from winrt.windows.media.ocr import OcrEngine as WinOcr
        except ImportError as exc:
            raise OcrUnavailable("Windows OCR paketleri kurulu değil: pip install -r requirements.txt") from exc
        lang = Language(language)
        if not WinOcr.is_language_supported(lang):
            raise OcrUnavailable(
                "Windows'ta İngilizce OCR dil paketi kurulu değil. PowerShell'i yönetici olarak açıp şunu çalıştır: "
                + ENGLISH_PACK_COMMAND
            )
        self._engine = WinOcr.try_create_from_language(lang)

    def recognize(self, image: np.ndarray) -> list[OcrLine]:
        from winrt.windows.graphics.imaging import BitmapPixelFormat, SoftwareBitmap
        from winrt.windows.storage.streams import DataWriter

        rgba = cv2.cvtColor(image, cv2.COLOR_BGR2RGBA)
        h, w = rgba.shape[:2]
        writer = DataWriter()
        writer.write_bytes(rgba.tobytes())
        bitmap = SoftwareBitmap.create_copy_from_buffer(writer.detach_buffer(), BitmapPixelFormat.RGBA8, w, h)

        async def run():
            return await self._engine.recognize_async(bitmap)

        result = asyncio.run(run())
        lines = []
        for line in result.lines:
            rects = [word.bounding_rect for word in line.words]
            if not rects:
                continue
            x0 = min(r.x for r in rects)
            y0 = min(r.y for r in rects)
            x1 = max(r.x + r.width for r in rects)
            y1 = max(r.y + r.height for r in rects)
            box = np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], dtype=np.float32)
            angle = getattr(result, "text_angle", None)
            if angle:  # Windows reports the text angle separately; tilt the box to match
                center = ((x0 + x1) / 2, (y0 + y1) / 2)
                rot = cv2.getRotationMatrix2D(center, -float(angle), 1.0)
                box = cv2.transform(box[None], rot)[0]
            lines.append(OcrLine(text=line.text, box=box))
        return lines


class RapidOcrEngine(OcrEngine):
    name = "RapidOCR"
    gives_scores = True

    def __init__(self) -> None:
        try:
            from rapidocr import RapidOCR
        except ImportError as exc:
            raise OcrUnavailable(
                "RapidOCR kurulu değil. Python 3.13 veya altında: pip install rapidocr onnxruntime"
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


def available_ocr_engines() -> list[type[OcrEngine]]:
    return [WindowsOcrEngine, RapidOcrEngine]
