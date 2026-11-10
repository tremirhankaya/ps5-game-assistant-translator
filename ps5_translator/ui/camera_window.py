"""Camera window: live webcam view and subtitle area selection.

Click the four corners of the area where subtitles appear on the monitor.
The flattened result is shown below; this is exactly what OCR will read.
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
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import settings
from ..vision import Region


class CameraThread(QThread):
    """Reads frames from the webcam on its own thread."""

    frame_ready = Signal(object)
    opened = Signal(int, int)
    failed = Signal(str)

    def __init__(self, index: int, width: int = 1920, height: int = 1080, preview_fps: int = 15) -> None:
        super().__init__()
        self.index = index
        self.width = width
        self.height = height
        self.preview_interval = 1 / preview_fps

    def run(self) -> None:
        # DirectShow opens most webcams faster on Windows than the default backend.
        backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
        cap = cv2.VideoCapture(self.index, backend)
        if not cap.isOpened():
            self.failed.emit(f"{self.index} numaralı kamera açılamadı.")
            return
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.opened.emit(int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

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
        self.requestInterruption()
        self.wait(3000)


def to_pixmap(frame: np.ndarray) -> QPixmap:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    image = QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888).copy()
    return QPixmap.fromImage(image)


class _ClickableView(QLabel):
    """Shows a frame scaled to fit and reports clicks in 0..1 image coordinates."""

    clicked = Signal(float, float)

    def __init__(self) -> None:
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(640, 360)
        self.setStyleSheet("background:#000;")
        self._image_size = (1, 1)

    def show_frame(self, frame: np.ndarray) -> None:
        h, w = frame.shape[:2]
        self._image_size = (w, h)
        self.setPixmap(to_pixmap(frame).scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def mousePressEvent(self, event) -> None:
        w, h = self._image_size
        scale = min(self.width() / w, self.height() / h)
        offset_x = (self.width() - w * scale) / 2
        offset_y = (self.height() - h * scale) / 2
        x = (event.position().x() - offset_x) / (w * scale)
        y = (event.position().y() - offset_y) / (h * scale)
        if 0 <= x <= 1 and 0 <= y <= 1:
            self.clicked.emit(x, y)


class CameraWindow(QWidget):
    region_changed = Signal(object)

    def __init__(self, log: Callable[[str, str], None]) -> None:
        super().__init__()
        self.setWindowTitle("Kamera ve altyazı bölgesi")
        self.resize(1000, 800)
        self._log = log
        self._thread: CameraThread | None = None
        self.latest_frame: np.ndarray | None = None

        config = settings.load_config()
        self.region = Region.from_dict(config.get("region"))
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
        reset = QPushButton("Bölgeyi sıfırla")
        reset.clicked.connect(self._reset_region)
        top.addWidget(reset)
        top.addStretch()
        layout.addLayout(top)

        self.hint = QLabel()
        self.hint.setFont(QFont("Segoe UI", 11))
        layout.addWidget(self.hint)

        self.view = _ClickableView()
        self.view.clicked.connect(self._add_point)
        layout.addWidget(self.view, stretch=3)

        layout.addWidget(QLabel("OCR'ın göreceği düzleştirilmiş görüntü:"))
        self.flat_view = QLabel()
        self.flat_view.setAlignment(Qt.AlignCenter)
        self.flat_view.setMinimumHeight(120)
        self.flat_view.setStyleSheet("background:#000;")
        layout.addWidget(self.flat_view, stretch=1)

        self._update_hint()
        self._start_camera(camera_index)

    # -- camera

    def _start_camera(self, index: int) -> None:
        self._stop_camera()
        settings.save_config(camera_index=index)
        self._log(
            f"Kamera {index} açılıyor...",
            "Bilgisayara birden fazla kamera bağlıysa (ör. laptop kamerası) numaraları farklı olur. "
            "Görüntü yanlışsa üstten başka numara seç.",
        )
        self._thread = CameraThread(index)
        self._thread.frame_ready.connect(self._on_frame)
        self._thread.opened.connect(self._on_opened)
        self._thread.failed.connect(lambda msg: self._log(msg, "Kamera başka bir programda açık olabilir ya da bu numarada kamera yoktur."))
        self._thread.start()

    def _stop_camera(self) -> None:
        if self._thread:
            self._thread.stop()
            self._thread = None

    def _on_opened(self, width: int, height: int) -> None:
        self._log(
            f"Kamera açıldı: {width}x{height}.",
            "Çözünürlük önemli: altyazı harfleri görüntüde ne kadar çok pikselden oluşursa OCR o kadar doğru okur. "
            "1920x1080 istedik; kamera desteklemiyorsa daha düşüğünü verir.",
        )

    def _on_frame(self, frame: np.ndarray) -> None:
        self.latest_frame = frame
        shown = frame.copy()
        h, w = shown.shape[:2]
        if self.region.points:
            pts = [(int(x * w), int(y * h)) for x, y in self.region.points]
            for p in pts:
                cv2.circle(shown, p, 8, (0, 200, 255), -1)
            if self.region.is_complete:
                poly = self.region.pixel_points(w, h).astype(np.int32)
                cv2.polylines(shown, [poly], True, (0, 200, 255), 3)
        self.view.show_frame(shown)

        if self.region.is_complete:
            flat = self.region.warp(frame)
            self.flat_view.setPixmap(
                to_pixmap(flat).scaled(self.flat_view.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

    # -- region

    def _add_point(self, x: float, y: float) -> None:
        self.region.add_point(x, y)
        if self.region.is_complete:
            settings.save_config(region=self.region.to_dict())
            self._log(
                "Altyazı bölgesi kaydedildi ve düzleştirildi.",
                "Kamera monitöre açılı baktığı için yazılar yamuk görünür. Dört köşeyle görüntüyü düz bir "
                "dikdörtgene çeviriyoruz (perspektif düzeltme), çünkü OCR düz satırları çok daha iyi okur. "
                "Bölge kaydedildi, bir dahaki açılışta tekrar seçmen gerekmez.",
            )
            self.region_changed.emit(self.region)
        self._update_hint()

    def _reset_region(self) -> None:
        self.region.clear()
        self.flat_view.clear()
        settings.save_config(region=None)
        self.region_changed.emit(self.region)
        self._update_hint()

    def _update_hint(self) -> None:
        n = len(self.region.points)
        if n == 4:
            text = "Bölge seçili. Değiştirmek için tekrar tıkla ya da 'Bölgeyi sıfırla'ya bas."
        else:
            text = (
                f"Monitörde altyazıların çıktığı alanın 4 köşesine tıkla ({n}/4). "
                "Biraz geniş tut ki iki satırlık altyazılar da sığsın."
            )
        self.hint.setText(text)

    def closeEvent(self, event) -> None:
        self._stop_camera()
        super().closeEvent(event)
