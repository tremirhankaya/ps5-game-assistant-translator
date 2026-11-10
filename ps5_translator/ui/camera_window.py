"""Camera window: live webcam view and two-step subtitle area selection.

Step 1 (left): click the four corners of the monitor screen. Drag a corner to
fine-tune it. The grid should run parallel to the monitor's edges.
Step 2 (right): on the flattened screen, drag a rectangle around the area
where subtitles appear.
Bottom: exactly what OCR will read.
"""
from __future__ import annotations

import os
import time
from typing import Callable

import cv2
import numpy as np
from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtGui import QFont, QImage, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QSizePolicy,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import settings
from ..vision import Calibration

DRAG_DISTANCE = 0.03  # how close (as a fraction of the image) a click must be to grab a corner
YELLOW = (0, 200, 255)
GREEN = (80, 220, 80)


class CameraThread(QThread):
    """Reads frames from the webcam on its own thread."""

    frame_ready = Signal(object)
    opened = Signal(int, int, str)
    failed = Signal(str)

    def __init__(self, index: int, width: int = 1920, height: int = 1080, preview_fps: int = 15) -> None:
        super().__init__()
        self.index = index
        self.width = width
        self.height = height
        self.preview_interval = 1 / preview_fps

    def _open(self):
        # Windows has several camera systems; not every webcam or OpenCV version
        # works with all of them, so try them in order.
        if os.name == "nt":
            backends = [(cv2.CAP_MSMF, "Media Foundation"), (cv2.CAP_DSHOW, "DirectShow")]
        else:
            backends = [(cv2.CAP_ANY, "default")]
        for backend, name in backends:
            if self.isInterruptionRequested():
                return None, ""
            cap = cv2.VideoCapture(self.index, backend)
            if cap.isOpened():
                return cap, name
            cap.release()
        return None, ""

    def run(self) -> None:
        cap, backend_name = self._open()
        if cap is None:
            if not self.isInterruptionRequested():
                self.failed.emit(f"{self.index} numaralı kamera açılamadı.")
            return
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.opened.emit(
            int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), backend_name
        )

        last = 0.0
        while not self.isInterruptionRequested():
            ok, frame = cap.read()
            if not ok:
                self.failed.emit("Kameradan görüntü alınamadı.")
                break
            now = time.monotonic()
            if now - last >= self.preview_interval:
                last = now
                self.frame_ready.emit(frame)
        cap.release()

    def stop(self) -> None:
        """Ask the thread to finish. Does not block: some (virtual) cameras take
        seconds to release, and the window must not freeze meanwhile."""
        self.requestInterruption()


def to_pixmap(frame: np.ndarray) -> QPixmap:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    image = QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888).copy()
    return QPixmap.fromImage(image)


class _FrameView(QLabel):
    """Shows an image scaled to fit and reports mouse actions in 0..1 image coordinates."""

    pressed = Signal(float, float)
    moved = Signal(float, float)
    released = Signal(float, float)

    def __init__(self, min_w: int, min_h: int) -> None:
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(min_w, min_h)
        self.setStyleSheet("background:#000;")
        self._image_size = (1, 1)

    def show_frame(self, frame: np.ndarray) -> None:
        h, w = frame.shape[:2]
        self._image_size = (w, h)
        self.setPixmap(to_pixmap(frame).scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _to_image(self, event) -> tuple[float, float]:
        w, h = self._image_size
        scale = min(self.width() / w, self.height() / h)
        offset_x = (self.width() - w * scale) / 2
        offset_y = (self.height() - h * scale) / 2
        return (
            (event.position().x() - offset_x) / (w * scale),
            (event.position().y() - offset_y) / (h * scale),
        )

    def mousePressEvent(self, event) -> None:
        self.pressed.emit(*self._to_image(event))

    def mouseMoveEvent(self, event) -> None:
        self.moved.emit(*self._to_image(event))

    def mouseReleaseEvent(self, event) -> None:
        self.released.emit(*self._to_image(event))


def _caption(text: str = "") -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
    return label


class CameraWindow(QWidget):
    calibration_changed = Signal(object)

    def __init__(self, log: Callable[[str, str], None]) -> None:
        super().__init__()
        self.setWindowTitle("Kamera ve altyazı bölgesi")
        self.resize(1300, 850)
        self._log = log
        self._thread: CameraThread | None = None
        # Threads that were asked to stop but are still closing their camera.
        # We keep a reference until they finish; deleting a running QThread crashes Qt.
        self._closing_threads: set[CameraThread] = set()
        self.latest_frame: np.ndarray | None = None
        self._dragging: int | None = None
        self._band_start: tuple[float, float] | None = None
        self._band_preview: tuple[float, float, float, float] | None = None

        config = settings.load_config()
        self.calibration = Calibration.from_dict(config.get("calibration"))
        camera_index = int(config.get("camera_index", 0))

        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("Kamera:"))
        self.camera_box = QComboBox()
        for i in range(4):
            self.camera_box.addItem(f"Kamera {i}", i)
        self.camera_box.setCurrentIndex(camera_index)
        self.camera_box.currentIndexChanged.connect(self._start_camera)
        top.addWidget(self.camera_box)
        reset_corners = QPushButton("Köşeleri sıfırla")
        reset_corners.clicked.connect(self._reset_corners)
        top.addWidget(reset_corners)
        reset_band = QPushButton("Altyazı alanını sıfırla")
        reset_band.clicked.connect(self._reset_band)
        top.addWidget(reset_band)
        top.addStretch()
        layout.addLayout(top)

        self.hint = _caption()
        self.hint.setFont(QFont("Segoe UI", 11))
        layout.addWidget(self.hint)

        views = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(_caption("1. Kamera görüntüsü: monitörün 4 köşesi"))
        self.camera_view = _FrameView(560, 380)
        self.camera_view.pressed.connect(self._camera_pressed)
        self.camera_view.moved.connect(self._camera_moved)
        self.camera_view.released.connect(self._camera_released)
        left.addWidget(self.camera_view)
        views.addLayout(left, stretch=1)

        right = QVBoxLayout()
        right.addWidget(_caption("2. Düzleştirilmiş ekran: altyazı alanını sürükleyerek seç"))
        self.screen_view = _FrameView(560, 315)
        self.screen_view.pressed.connect(self._screen_pressed)
        self.screen_view.moved.connect(self._screen_moved)
        self.screen_view.released.connect(self._screen_released)
        right.addWidget(self.screen_view)
        views.addLayout(right, stretch=1)
        layout.addLayout(views, stretch=3)

        layout.addWidget(_caption("OCR'ın okuyacağı görüntü:"))
        self.crop_view = _FrameView(400, 120)
        layout.addWidget(self.crop_view, stretch=1)

        self._update_hint()
        self._start_camera(camera_index)

    # -- camera

    def _start_camera(self, index: int) -> None:
        self._stop_camera()
        settings.save_config(camera_index=index)
        self._log(
            f"Kamera {index} açılıyor...",
            "Bilgisayarda birden fazla kamera olabilir; NVIDIA Broadcast, OBS gibi programlar da sanal kamera "
            "ekler. Görüntü yanlışsa üstten başka numara seç.",
        )
        self._thread = CameraThread(index)
        self._thread.frame_ready.connect(self._on_frame)
        self._thread.opened.connect(self._on_opened)
        self._thread.failed.connect(
            lambda msg: self._log(msg, "Kamera başka bir programda açık olabilir ya da bu numarada kamera yoktur.")
        )
        self._thread.start()

    def _stop_camera(self) -> None:
        thread = self._thread
        if thread is None:
            return
        self._thread = None
        for signal in (thread.frame_ready, thread.opened, thread.failed):
            signal.disconnect()
        self._closing_threads.add(thread)
        thread.finished.connect(lambda: self._closing_threads.discard(thread))
        thread.stop()

    def shutdown(self, timeout_ms: int = 8000) -> None:
        """Stop all camera threads and wait for them (used when the app closes)."""
        self._stop_camera()
        for thread in list(self._closing_threads):
            thread.wait(timeout_ms)

    def _on_opened(self, width: int, height: int, backend: str) -> None:
        self._log(
            f"Kamera açıldı: {width}x{height} ({backend}).",
            "Çözünürlük önemli: altyazı harfleri görüntüde ne kadar çok pikselden oluşursa OCR o kadar doğru okur. "
            "1920x1080 istedik; kamera desteklemiyorsa daha düşüğünü verir.",
        )

    def _on_frame(self, frame: np.ndarray) -> None:
        self.latest_frame = frame
        calib = self.calibration
        h, w = frame.shape[:2]

        shown = frame.copy()
        for x, y in calib.screen.points:
            cv2.circle(shown, (int(x * w), int(y * h)), 10, YELLOW, -1)
        if calib.has_screen:
            cv2.polylines(shown, [calib.screen.pixel_points(w, h).astype(np.int32)], True, YELLOW, 3)
            for line in calib.grid_lines(w, h):
                cv2.line(shown, tuple(map(int, line[0])), tuple(map(int, line[1])), YELLOW, 1)
        self.camera_view.show_frame(shown)

        if not calib.has_screen:
            self.screen_view.clear()
            self.crop_view.clear()
            return

        flat = calib.flatten_screen(frame)
        band = self._band_preview or calib.band
        if band:
            fh, fw = flat.shape[:2]
            x0, y0, x1, y1 = band
            cv2.rectangle(flat, (int(x0 * fw), int(y0 * fh)), (int(x1 * fw), int(y1 * fh)), GREEN, 2)
        self.screen_view.show_frame(flat)

        crop = calib.subtitle_crop(frame)
        if crop is not None:
            self.crop_view.show_frame(crop)
        else:
            self.crop_view.clear()

    # -- step 1: screen corners

    def _camera_pressed(self, x: float, y: float) -> None:
        screen = self.calibration.screen
        if not (0 <= x <= 1 and 0 <= y <= 1):
            return
        near = screen.nearest_point(x, y, DRAG_DISTANCE)
        if near is not None:
            self._dragging = near
            return
        if screen.is_complete:
            return  # ignore clicks away from corners; use "Köşeleri sıfırla" to start over
        screen.add_point(x, y)
        if screen.is_complete:
            self._screen_done()
        self._update_hint()

    def _camera_moved(self, x: float, y: float) -> None:
        if self._dragging is not None:
            self.calibration.screen.move_point(self._dragging, x, y)

    def _camera_released(self, x: float, y: float) -> None:
        if self._dragging is not None:
            self._dragging = None
            if self.calibration.has_screen:
                self._save()

    def _screen_done(self) -> None:
        self._save()
        self._log(
            "Monitörün köşeleri seçildi, ekran düzleştirildi.",
            "Kamera monitöre açılı baktığı için ekran yamuk görünür. Monitörün 16:9 olduğunu bildiğimiz için "
            "4 köşeden ekranı tam doğru oranlarla düz bir dikdörtgene çevirebiliyoruz (perspektif düzeltme). "
            "Izgara çizgileri monitörün kenarlarına paralel değilse bir köşeyi sürükleyerek düzelt.",
        )

    # -- step 2: subtitle band

    def _screen_pressed(self, x: float, y: float) -> None:
        if self.calibration.has_screen:
            self._band_start = (x, y)

    def _screen_moved(self, x: float, y: float) -> None:
        if self._band_start:
            self._band_preview = (*self._band_start, x, y)
            x0, y0, x1, y1 = self._band_preview
            self._band_preview = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))

    def _screen_released(self, x: float, y: float) -> None:
        if not self._band_start:
            return
        before = self.calibration.band
        self.calibration.set_band(*self._band_start, x, y)
        self._band_start = None
        self._band_preview = None
        if self.calibration.band != before:
            self._save()
            self._log(
                "Altyazı alanı seçildi.",
                "OCR'a ekranın tamamını değil sadece bu bandı gönderiyoruz. Böylece menüler, bildirimler gibi "
                "başka yazılar çeviriye karışmaz ve OCR daha hızlı çalışır.",
            )
        self._update_hint()

    # -- helpers

    def _save(self) -> None:
        settings.save_config(calibration=self.calibration.to_dict())
        self.calibration_changed.emit(self.calibration)

    def _reset_corners(self) -> None:
        self.calibration.screen.clear()
        self._save()
        self._update_hint()

    def _reset_band(self) -> None:
        self.calibration.band = None
        self._save()
        self._update_hint()

    def _update_hint(self) -> None:
        calib = self.calibration
        n = len(calib.screen.points)
        if n < 4:
            text = (
                f"Adım 1: Soldaki görüntüde monitör ekranının 4 köşesine tıkla ({n}/4). "
                "Ekranın parlak alanının bittiği köşeleri seç."
            )
        elif calib.band is None:
            text = (
                "Adım 2: Sağdaki düz ekranda altyazının çıktığı alanı fareyle sürükleyerek seç. "
                "İki satırlık altyazılar da sığacak kadar yüksek tut. Köşeleri sürükleyerek ince ayar yapabilirsin."
            )
        else:
            text = (
                "Hazır. Köşeleri sürükleyerek ince ayar yapabilir, sağda yeni bir alan sürükleyerek altyazı "
                "bölgesini değiştirebilirsin."
            )
        self.hint.setText(text)

    def showEvent(self, event) -> None:
        if self._thread is None:  # reopened after being closed
            self._start_camera(self.camera_box.currentIndex())
        super().showEvent(event)

    def closeEvent(self, event) -> None:
        self._stop_camera()  # camera keeps closing in the background; the app waits for it on exit
        super().closeEvent(event)
