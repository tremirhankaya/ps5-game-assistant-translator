"""Four corners of an area as seen by the webcam.

The webcam looks at the monitor from an angle, so a rectangle on the screen
appears as a tilted four-sided shape in the camera image. With its four
corners we can "flatten" it back into a rectangle (perspective correction).

Points are stored as fractions of the image size (0..1), so they still fit
if the camera resolution changes.
"""
from __future__ import annotations

import math
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
        self.points.append(_clamp_point(x, y))

    def move_point(self, index: int, x: float, y: float) -> None:
        self.points[index] = _clamp_point(x, y)

    def nearest_point(self, x: float, y: float, max_distance: float) -> int | None:
        """Index of the corner closest to (x, y), if it is close enough."""
        best, best_d = None, max_distance
        for i, (px, py) in enumerate(self.points):
            d = math.hypot(px - x, py - y)
            if d <= best_d:
                best, best_d = i, d
        return best

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

    def natural_size(self, width: int, height: int) -> tuple[int, int]:
        """Size of the flattened area if we keep roughly the pixels the camera sees."""
        tl, tr, br, bl = self.pixel_points(width, height)
        out_w = int(max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl)))
        out_h = int(max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr)))
        return max(out_w, 1), max(out_h, 1)

    def matrix(self, width: int, height: int, out_size: tuple[int, int]) -> np.ndarray:
        out_w, out_h = out_size
        dst = np.array([(0, 0), (out_w - 1, 0), (out_w - 1, out_h - 1), (0, out_h - 1)], dtype=np.float32)
        return cv2.getPerspectiveTransform(self.pixel_points(width, height), dst)

    def warp(self, frame: np.ndarray, out_size: tuple[int, int] | None = None) -> np.ndarray:
        """Return the area as a flat, upright rectangle."""
        if not self.is_complete:
            raise ValueError("Region needs 4 points")
        h, w = frame.shape[:2]
        size = out_size or self.natural_size(w, h)
        return cv2.warpPerspective(frame, self.matrix(w, h, size), size)

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


def _clamp_point(x: float, y: float) -> tuple[float, float]:
    x, y = float(x), float(y)  # plain floats so they can be saved as JSON
    return min(max(x, 0.0), 1.0), min(max(y, 0.0), 1.0)
