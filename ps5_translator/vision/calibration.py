"""Two-step calibration: where the screen is, and where subtitles appear on it.

Step 1: the user clicks the four corners of the monitor screen. These are easy
to see. Because we know the screen's shape (16:9), the flattened image has the
correct proportions and text comes out straight.

If the camera sits below the monitor (so it does not bother the player), it
only sees the lower part of the screen. In "partial" mode the user picks the
corners of a rectangle on that visible part instead. Its true shape is not
known, so we estimate it from the camera image and let the user correct the
height with a slider (text seen from below looks squashed).

Step 2: on the flattened screen, the user drags a normal rectangle around the
area where subtitles appear (the "band"). Only this part is sent to OCR, so
other text on the screen (menus, notifications) is ignored.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

from .region import Region

Band = tuple[float, float, float, float]  # x0, y0, x1, y1 as fractions of the flat screen

FULL = "full"  # the camera sees the whole screen; we know it is 16:9
PARTIAL = "partial"  # the camera sees only part of the screen


@dataclass
class Calibration:
    screen: Region = field(default_factory=Region)
    aspect: float = 16 / 9
    band: Band | None = None
    mode: str = FULL
    height_scale: float = 1.0  # partial mode: user correction for squashed text
    rotation: float = 0.0  # degrees; straightens text that is still a little tilted

    @property
    def has_screen(self) -> bool:
        return self.screen.is_complete

    @property
    def is_complete(self) -> bool:
        return self.has_screen and self.band is not None

    def size_for(self, width: int, height: int) -> tuple[int, int]:
        """Size of the flattened area for a camera image of width x height."""
        natural_w, natural_h = self.screen.natural_size(width, height)
        if self.mode == FULL:
            out_h = natural_w / self.aspect  # known shape: the monitor is 16:9
        else:
            out_h = natural_h * self.height_scale  # estimated shape, corrected by the user
        return natural_w, max(int(round(out_h)), 1)

    def screen_size(self, frame: np.ndarray) -> tuple[int, int]:
        h, w = frame.shape[:2]
        return self.size_for(w, h)

    def flatten_screen(self, frame: np.ndarray) -> np.ndarray:
        return self.screen.warp(frame, self.screen_size(frame))

    def set_band(self, x0: float, y0: float, x1: float, y1: float) -> None:
        x0, x1 = sorted((min(max(x0, 0.0), 1.0), min(max(x1, 0.0), 1.0)))
        y0, y1 = sorted((min(max(y0, 0.0), 1.0), min(max(y1, 0.0), 1.0)))
        if x1 - x0 < 0.02 or y1 - y0 < 0.01:  # a click, not a drag
            return
        self.band = (float(x0), float(y0), float(x1), float(y1))

    def subtitle_crop(self, frame: np.ndarray) -> np.ndarray | None:
        """The subtitle band, flat and upright. This is what OCR reads."""
        if not self.is_complete:
            return None
        h, w = frame.shape[:2]
        screen_w, screen_h = self.screen_size(frame)
        x0, y0, x1, y1 = self.band
        # Warp the band directly from the camera image (one step, no extra blur).
        out_w = max(int((x1 - x0) * screen_w), 1)
        out_h = max(int((y1 - y0) * screen_h), 1)
        to_flat = self.screen.matrix(w, h, (screen_w, screen_h))
        shift = np.array([[1, 0, -x0 * screen_w], [0, 1, -y0 * screen_h], [0, 0, 1]], dtype=np.float64)
        crop = cv2.warpPerspective(frame, shift @ to_flat, (out_w, out_h))
        if abs(self.rotation) > 0.05:
            rot = cv2.getRotationMatrix2D((out_w / 2, out_h / 2), self.rotation, 1.0)
            crop = cv2.warpAffine(crop, rot, (out_w, out_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return crop

    def grid_lines(self, width: int, height: int, divisions: int = 4) -> list[np.ndarray]:
        """Lines of a grid on the screen, drawn in camera coordinates.
        If the corners are right, these lines follow the monitor's edges."""
        flat_w, flat_h = self.size_for(width, height)
        screen_size = (1000, max(int(1000 * flat_h / flat_w), 1))
        inverse = np.linalg.inv(self.screen.matrix(width, height, screen_size))
        sw, sh = screen_size
        lines = []
        for i in range(1, divisions):
            for a, b in (((sw * i / divisions, 0), (sw * i / divisions, sh)),
                         ((0, sh * i / divisions), (sw, sh * i / divisions))):
                pts = np.array([[a, b]], dtype=np.float32)
                lines.append(cv2.perspectiveTransform(pts, inverse)[0].astype(np.int32))
        return lines

    # -- saving

    def to_dict(self) -> dict:
        return {
            "screen": self.screen.to_dict(),
            "band": list(self.band) if self.band else None,
            "mode": self.mode,
            "height_scale": self.height_scale,
            "rotation": self.rotation,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> "Calibration":
        data = data or {}
        band = data.get("band")
        return cls(
            screen=Region.from_dict(data.get("screen")),
            band=tuple(band) if band else None,
            mode=data.get("mode", FULL),
            height_scale=float(data.get("height_scale", 1.0)),
            rotation=float(data.get("rotation", 0.0)),
        )
