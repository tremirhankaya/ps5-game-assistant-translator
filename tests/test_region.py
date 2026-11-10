import cv2
import numpy as np

from ps5_translator import settings
from ps5_translator.vision import Region


def test_corners_are_ordered_regardless_of_click_order():
    region = Region()
    for p in [(0.9, 0.9), (0.1, 0.1), (0.1, 0.9), (0.9, 0.1)]:
        region.add_point(*p)
    expected = [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)]
    assert np.allclose(region.ordered(), expected)


def test_fifth_click_starts_a_new_region():
    region = Region()
    for _ in range(4):
        region.add_point(0.5, 0.5)
    region.add_point(0.2, 0.3)
    assert region.points == [(0.2, 0.3)]


def test_points_are_kept_inside_the_image():
    region = Region()
    region.add_point(-0.2, 1.5)
    assert region.points == [(0.0, 1.0)]


def test_warp_flattens_a_tilted_area():
    # White image with a tilted black quadrilateral; warping it must give an
    # almost fully black rectangle.
    frame = np.full((400, 600, 3), 255, np.uint8)
    corners = np.array([(100, 120), (500, 80), (520, 300), (80, 320)], np.int32)
    cv2.fillPoly(frame, [corners], (0, 0, 0))

    region = Region()
    for x, y in corners:
        region.add_point(x / 600, y / 400)
    flat = region.warp(frame)

    assert flat.shape[1] > flat.shape[0]  # wider than tall
    assert flat.mean() < 10  # nearly all black: we cut exactly the shape


def test_region_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    region = Region()
    for p in [(0.1, 0.7), (0.9, 0.7), (0.9, 0.9), (0.1, 0.9)]:
        region.add_point(*p)
    settings.save_config(region=region.to_dict(), camera_index=1)
    config = settings.load_config()
    assert Region.from_dict(config["region"]).points == region.points
    assert config["camera_index"] == 1
