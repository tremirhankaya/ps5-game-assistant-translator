"""Test window for the translation step.

For now the English text is typed by hand. Later the OCR step will feed
the same pipeline automatically.
"""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import settings
from ..explain import explain
from ..ocr.stability import StabilityFilter
from .subtitle_window import SubtitleWindow
from ..translation import DeepLEngine, Result, TranslationPipeline


class _Signals(QObject):
    done = Signal(object)


class _TranslateJob(QRunnable):
    """Runs the pipeline off the UI thread so the window never freezes."""

    def __init__(self, pipeline: TranslationPipeline, text: str) -> None:
        super().__init__()
        self.pipeline = pipeline
        self.text = text
        self.signals = _Signals()

    def run(self) -> None:
        self.signals.done.emit(self.pipeline.process(self.text))


class _CallJob(QRunnable):
    """Runs any slow function off the UI thread. Emits (ok, value_or_error)."""

    def __init__(self, fn) -> None:
        super().__init__()
        self.fn = fn
        self.signals = _Signals()

    def run(self) -> None:
        try:
            self.signals.done.emit((True, self.fn()))
        except Exception as exc:
            self.signals.done.emit((False, str(exc) or exc.__class__.__name__))


class MainWindow(QMainWindow):
    def __init__(self, engine_factory=DeepLEngine) -> None:
        super().__init__()
        self._engine_factory = engine_factory
        self.setWindowTitle("PS5 Game Assistant Translator")
        self.resize(1000, 700)

        # One worker thread: lines are translated in the order they arrive.
        self._pool = QThreadPool()
        self._jobs: set[QRunnable] = set()  # keep jobs alive until they report back
        self._pool.setMaxThreadCount(1)
        self._pipeline: TranslationPipeline | None = None
        self._translated_since_usage = 0
        self._camera_window = None
        self._stability = StabilityFilter()
        self._subtitle_window = SubtitleWindow()

        self._build_ui()
        self._load_engine()

    # ------------------------------------------------------------- layout

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        top = QHBoxLayout()
        camera_button = QPushButton("Kamera")
        camera_button.clicked.connect(self._open_camera)
        top.addWidget(camera_button)
        settings_button = QPushButton("Ayarlar")
        settings_button.clicked.connect(self._open_settings)
        top.addWidget(settings_button)
        self.live_toggle = QCheckBox("Canlı çeviri")
        self.live_toggle.setToolTip("Kameranın okuduğu altyazıları otomatik çevirir.")
        self.live_toggle.toggled.connect(self._live_toggled)
        top.addWidget(self.live_toggle)
        fullscreen_button = QPushButton("Tam ekran")
        fullscreen_button.setToolTip("Çevirileri bu monitörde tam ekran gösterir (F11). Çıkmak için Esc.")
        fullscreen_button.setShortcut("F11")
        fullscreen_button.clicked.connect(self._open_fullscreen)
        top.addWidget(fullscreen_button)
        top.addStretch()
        self.usage_label = QLabel("")
        self.usage_label.setStyleSheet("color:#888;")
        top.addWidget(self.usage_label)
        self.explain_toggle = QCheckBox("Açıklamaları göster")
        self.explain_toggle.setChecked(True)
        self.explain_toggle.toggled.connect(lambda on: self.log.setVisible(on))
        top.addWidget(self.explain_toggle)
        layout.addLayout(top)

        self.subtitle = QLabel("Çeviri burada görünecek")
        self.subtitle.setWordWrap(True)
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setMinimumHeight(180)
        self.subtitle.setFont(QFont("Segoe UI", 30, QFont.DemiBold))
        self.subtitle.setStyleSheet("background:#111; color:#fff; border-radius:8px; padding:16px;")
        layout.addWidget(self.subtitle)

        self.source = QLabel("")
        self.source.setWordWrap(True)
        self.source.setAlignment(Qt.AlignCenter)
        self.source.setFont(QFont("Segoe UI", 14))
        self.source.setStyleSheet("color:#888;")
        layout.addWidget(self.source)

        row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("İngilizce bir altyazı yaz ve Enter'a bas")
        self.input.setFont(QFont("Segoe UI", 12))
        self.input.returnPressed.connect(self._submit)
        row.addWidget(self.input)
        send = QPushButton("Çevir")
        send.clicked.connect(self._submit)
        row.addWidget(send)
        layout.addLayout(row)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Consolas", 10))
        self.log.setPlaceholderText("Uygulamanın her adımda ne yaptığı ve neden yaptığı burada görünür.")
        layout.addWidget(self.log, stretch=1)

        self.setCentralWidget(root)

    # ------------------------------------------------------------- actions

    def _load_engine(self) -> None:
        job = _CallJob(self._engine_factory)
        job.signals.done.connect(self._engine_ready)
        self._start(job)

    def _engine_ready(self, outcome) -> None:
        ok, value = outcome
        if not ok:
            self._write_log(f"Çeviri başlatılamadı: {value}")
            return
        engine = value
        if self._pipeline is None:
            self._pipeline = TranslationPipeline(engine)
        else:
            self._pipeline.set_engine(engine)
        self.usage_label.setText("")
        self._refresh_usage()
        self._write_log(f"Çeviri hazır: {engine.name}.")
        note = getattr(engine, "ready_note", None)
        if note:
            self._write_log(*note)

    def _refresh_usage(self) -> None:
        engine = self._pipeline.engine if self._pipeline else None
        usage = getattr(engine, "usage", None)
        if usage is None:
            return
        self._translated_since_usage = 0
        job = _CallJob(usage)
        job.signals.done.connect(self._show_usage)
        self._start(job)

    def _show_usage(self, outcome) -> None:
        ok, value = outcome
        if ok and value:
            used, limit = value
            self.usage_label.setText(f"DeepL kotası: {used:,} / {limit:,} karakter".replace(",", "."))

    def _open_fullscreen(self) -> None:
        # Opens on the monitor this window is on: drag the app to the second monitor first.
        self._subtitle_window.show_on(self.screen())

    def _ensure_camera(self):
        from .camera_window import CameraWindow

        if self._camera_window is None:
            self._camera_window = CameraWindow(log=self._write_log)
            self._camera_window.ocr_read.connect(self._on_ocr)
        return self._camera_window

    def _open_camera(self) -> None:
        window = self._ensure_camera()
        window.show()
        window.raise_()

    # -- live translation

    def _live_toggled(self, on: bool) -> None:
        camera = self._ensure_camera()
        self._stability.reset()
        camera.set_live(on)
        if not on:
            self._write_log("Canlı çeviri durduruldu.")
            return
        if not camera.calibration.is_complete:
            self._write_log(
                "Canlı çeviri için önce kamera ayarı gerekli.",
                "Kamera penceresinde köşeleri ve altyazı alanını seç; seçince çeviri kendiliğinden başlar.",
            )
            self._open_camera()
            return
        self._write_log(
            "Canlı çeviri başladı.",
            "Kamera altyazı alanını sürekli okuyor. Bir yazı art arda iki okumada aynı çıkınca çeviriye gönderilir. "
            "Kamera penceresini kapatabilirsin; arka planda çalışmaya devam eder.",
        )

    def _on_ocr(self, result) -> None:
        if not self.live_toggle.isChecked() or self._pipeline is None:
            return
        text = self._stability.feed(result.text)
        if text is None:
            return
        score = f", güven {result.score:.2f}" if result.score is not None else ""
        self._write_log(
            f"OCR okudu ve yazı sabitlendi: \"{text}\" ({result.ms:.0f} ms{score})",
            "Aynı yazı art arda iki kez okundu, yani altyazı tamamlandı ve kamera titremesi değil. "
            "Yarım cümleleri çevirmemek ve kotayı boşa harcamamak için bunu bekliyoruz.",
        )
        job = _TranslateJob(self._pipeline, text)
        job.signals.done.connect(self._show_result)
        self._start(job)

    def closeEvent(self, event) -> None:
        self._subtitle_window.close()
        if self._camera_window is not None:
            self._camera_window.close()
            self._camera_window.shutdown()
        super().closeEvent(event)

    def _open_settings(self) -> None:
        current = settings.get_deepl_key() or ""
        key, ok = QInputDialog.getText(
            self,
            "DeepL anahtarı",
            "deepl.com/pro-api adresinden aldığın ücretsiz API anahtarını yapıştır.\n"
            "Boş bırakırsan kayıtlı anahtar silinir.",
            QLineEdit.Password,
            current,
        )
        if not ok:
            return
        try:
            settings.set_deepl_key(key)
        except Exception as exc:
            self._write_log(f"Anahtar kaydedilemedi: {exc}")
            return
        self._write_log(
            "DeepL anahtarı Windows Kimlik Bilgisi Yöneticisi'ne kaydedildi." if key.strip()
            else "DeepL anahtarı silindi.",
            "Anahtar proje klasöründe düz bir dosyada dursaydı yanlışlıkla GitHub'a gönderilebilirdi. "
            "Windows'un kendi şifre kasasında saklamak daha güvenli.",
        )
        self._load_engine()

    def _start(self, job: QRunnable) -> None:
        job.setAutoDelete(False)
        self._jobs.add(job)
        job.signals.done.connect(lambda _: self._jobs.discard(job))
        self._pool.start(job)

    def _submit(self) -> None:
        text = self.input.text()
        if not text.strip() or self._pipeline is None:
            return
        self.input.clear()
        job = _TranslateJob(self._pipeline, text)
        job.signals.done.connect(self._show_result)
        self._start(job)

    def _show_result(self, result: Result | None) -> None:
        if result is None:
            return
        for event in result.events:
            exp = explain(event)
            self._write_log(exp.what, exp.why)
        if result.skipped or result.error:
            return
        if not result.from_cache:
            self._translated_since_usage += 1
            if self._translated_since_usage >= 20:
                self._refresh_usage()
        self.subtitle.setText(result.translated)
        self._subtitle_window.show_line(result.translated, result.source)
        source_note = "kayıttan" if result.from_cache else f"{result.ms:.0f} ms"
        self.source.setText(f"{result.source}   ·   {source_note}")

    def _write_log(self, what: str, why: str = "") -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log.appendPlainText(f"[{stamp}] {what}")
        if why:
            self.log.appendPlainText(f"           Neden: {why}")
        self.log.appendPlainText("")
