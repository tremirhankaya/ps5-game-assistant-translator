import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtWidgets import QApplication

from ps5_translator.ui.camera_window import CameraThread


def test_only_the_latest_frame_is_kept_and_signalled_once():
    QApplication.instance() or QApplication([])
    thread = CameraThread(0)
    signals = []
    thread.frame_ready.connect(lambda: signals.append(1))
    frames = [np.full((4, 4, 3), i, np.uint8) for i in range(50)]
    for f in frames:  # the window is busy and does not take frames
        thread.publish(f)
    assert len(signals) == 1  # no queue of 50 signals / frames
    assert thread.take_frame()[0, 0, 0] == 49  # newest frame wins
    thread.publish(frames[0])
    assert len(signals) == 2  # after taking, the next frame signals again
