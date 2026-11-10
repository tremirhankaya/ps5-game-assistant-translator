import cv2
import numpy as np

from ps5_translator import settings
from ps5_translator.vision import Calibration, Region


def make_camera_frame():
    """A 16:9 'screen' with a white subtitle bar, seen by a camera at an angle."""
    screen = np.full((450, 800, 3), 60, np.uint8)
    cv2.rectangle(screen, (200, 380), (600, 420), (255, 255, 255), -1)  # subtitle bar
    cv2.rectangle(screen, (650, 20), (780, 60), (0, 0, 255), -1)  # notification (red)
    corners = np.float32([(300, 200), (1500, 120), (1560, 900), (260, 860)])
    matrix = cv2.getPerspectiveTransform(np.float32([(0, 0), (799, 0), (799, 449), (0, 449)]), corners)
    frame = cv2.warpPerspective(screen, matrix, (1920, 1080))
    calib = Calibration()
    for x, y in corners:
        calib.screen.add_point(x / 1920, y / 1080)
    return frame, calib


def test_flat_screen_has_the_monitor_aspect_ratio():
    frame, calib = make_camera_frame()
    flat = calib.flatten_screen(frame)
    h, w = flat.shape[:2]
    assert abs(w / h - 16 / 9) < 0.01


def test_band_crop_contains_only_the_subtitle_area():
    frame, calib = make_camera_frame()
    calib.set_band(200 / 800, 370 / 450, 600 / 800, 430 / 450)
    crop = calib.subtitle_crop(frame)
    # Mostly white (the subtitle bar), and no red from the notification.
    assert crop.mean() > 150
    assert (crop[:, :, 2].astype(int) - crop[:, :, 1]).max() < 60


def test_click_without_drag_does_not_set_a_band():
    calib = Calibration()
    calib.set_band(0.5, 0.5, 0.505, 0.502)
    assert calib.band is None


def test_band_is_sorted_and_clamped():
    calib = Calibration()
    calib.set_band(0.9, 1.2, 0.1, 0.8)
    assert calib.band == (0.1, 0.8, 0.9, 1.0)


def test_grid_lines_stay_inside_the_screen():
    frame, calib = make_camera_frame()
    poly = calib.screen.pixel_points(1920, 1080)
    for line in calib.grid_lines(1920, 1080):
        for x, y in line:
            assert cv2.pointPolygonTest(poly, (float(x), float(y)), True) > -3


def test_nearest_point_for_dragging():
    region = Region()
    for p in [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)]:
        region.add_point(*p)
    assert region.nearest_point(0.88, 0.12, 0.05) == 1
    assert region.nearest_point(0.5, 0.5, 0.05) is None
    region.move_point(1, 0.8, 0.2)
    assert region.points[1] == (0.8, 0.2)


def test_calibration_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    _, calib = make_camera_frame()
    calib.set_band(0.2, 0.8, 0.8, 0.95)
    settings.save_config(calibration=calib.to_dict())
    loaded = Calibration.from_dict(settings.load_config()["calibration"])
    assert loaded.band == calib.band
    assert loaded.screen.points == calib.screen.points
