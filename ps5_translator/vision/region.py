"""The subtitle area on the monitor, as seen by the webcam.

The webcam looks at the monitor from an angle, so the subtitle area is not a
rectangle in the camera image but a tilted four-sided shape. The user clicks
its four corners; we then "flatten" it back into a rectangle (perspective
correction) so OCR reads straight text.

Points are stored as fractions of the image size (0..1), so they still fit
if the camera resolution changes.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np


@dataclass
class Region:
    points: list[tuple[float, float]] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return len(self.points) == 4

    def add_point(self, x: float, y: float) -> None:
        if self.is_complete:
            self.points.clear()
        self.points.append((min(max(x, 0.0), 1.0), min(max(y, 0.0), 1.0)))

    def clear(self) -> None:
        self.points.clear()

    def ordered(self) -> list[tuple[float, float]]:
        """Corners in the order top-left, top-right, bottom-right, bottom-left,
        no matter in which order the user clicked them."""
        pts = np.array(self.points, dtype=np.float32)
        s = pts.sum(axis=1)  # x + y: smallest at top-left, largest at bottom-right
        d = pts[:, 1] - pts[:, 0]  # y - x: smallest at top-right, largest at bottom-left
        tl, br = pts[np.argmin(s)], pts[np.argmax(s)]
        tr, bl = pts[np.argmin(d)], pts[np.argmax(d)]
        return [tuple(map(float, p)) for p in (tl, tr, br, bl)]

    def pixel_points(self, width: int, height: int) -> np.ndarray:
        return np.array([(x * width, y * height) for x, y in self.ordered()], dtype=np.float32)

    def warp(self, frame: np.ndarray) -> np.ndarray:
        """Return the subtitle area as a flat, upright rectangle."""
        if not self.is_complete:
            raise ValueError("Region needs 4 points")
        h, w = frame.shape[:2]
        src = self.pixel_points(w, h)
        tl, tr, br, bl = src
        out_w = int(max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl)))
        out_h = int(max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr)))
        out_w, out_h = max(out_w, 1), max(out_h, 1)
        dst = np.array([(0, 0), (out_w - 1, 0), (out_w - 1, out_h - 1), (0, out_h - 1)], dtype=np.float32)
        matrix = cv2.getPerspectiveTransform(src, dst)
        return cv2.warpPerspective(frame, matrix, (out_w, out_h))

    # -- saving

    def to_dict(self) -> dict:
        return {"points": [list(p) for p in self.points]}

    @classmethod
    def from_dict(cls, data: dict | None) -> "Region":
        points = (data or {}).get("points", [])
        region = cls()
        for x, y in points[:4]:
            region.add_point(float(x), float(y))
        return region
