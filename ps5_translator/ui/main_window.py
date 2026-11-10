"""Test window for the translation step.

For now the English text is typed by hand. Later the OCR step will feed
the same pipeline automatically.
"""
from __future__ import annotations

import time
from datetime import datetime

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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
from ..translation import Result, TranslationPipeline, available_engines


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
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PS5 Game Assistant Translator")
        self.resize(1000, 700)

        # One worker thread: lines are translated in the order they arrive.
        self._pool = QThreadPool()
        self._jobs: set[QRunnable] = set()  # keep jobs alive until they report back
        self._pool.setMaxThreadCount(1)
        self._engines = available_engines()
        self._pipeline: TranslationPipeline | None = None
        self._translated_since_usage = 0
        self._camera_window = None
        self._stability = StabilityFilter()

        self._build_ui()
        self._select_engine(0)

    # ------------------------------------------------------------- layout

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        top = QHBoxLayout()
        top.addWidget(QLabel("Çeviri motoru:"))
        self.engine_box = QComboBox()
        for engine in self._engines:
            self.engine_box.addItem(engine.name)
        self.engine_box.currentIndexChanged.connect(self._select_engine)
        top.addWidget(self.engine_box)
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

    def _select_engine(self, index: int) -> None:
        engine_cls = self._engines[index]
        self.engine_box.setEnabled(False)

        def prepare():
            engine = engine_cls()
            warm_up = getattr(engine, "warm_up", None)
            if warm_up:
                start = time.perf_counter()
                warm_up()
                return engine, (time.perf_counter() - start) * 1000
            return engine, None

        if getattr(engine_cls, "model", ""):
            self._write_log(
                f"{engine_cls.name} hazırlanıyor...",
                "Yerel model ilk kullanımda diskten ekran kartına (ya da RAM'e) yükleniyor. "
                "Bunu şimdi yapıyoruz ki ilk altyazı beklemesin.",
            )
        job = _CallJob(prepare)
        job.signals.done.connect(lambda outcome: self._engine_ready(engine_cls, outcome))
        self._start(job)

    def _engine_ready(self, engine_cls, outcome) -> None:
        self.engine_box.setEnabled(True)
        ok, value = outcome
        if not ok:
            self._write_log(
                f"{engine_cls.name} başlatılamadı: {value}",
                "Bu motor için gereken program ya da model hazır değil. Mesajdaki adımı uygulayıp tekrar seç.",
            )
            return
        engine, load_ms = value
        if self._pipeline is None:
            self._pipeline = TranslationPipeline(engine)
        else:
            self._pipeline.set_engine(engine)
        note = getattr(engine, "ready_note", None)
        self.usage_label.setText("")
        self._refresh_usage()
        if load_ms is not None:
            self._write_log(
                f"{engine.name} hazır (yükleme {load_ms / 1000:.1f} sn).",
                "Model 30 dakika bellekte kalacak, sonraki çeviriler hızlı olacak.",
            )
        self._write_log(
            f"Motor değişti: {engine.name}",
            "Önceki çeviriler silindi, çünkü farklı motorların sonuçları karışmasın.",
        )
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
        if self._engines[self.engine_box.currentIndex()].name == "DeepL":
            self._select_engine(self.engine_box.currentIndex())

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
        source_note = "kayıttan" if result.from_cache else f"{result.ms:.0f} ms"
        self.source.setText(f"{result.source}   ·   {source_note}")

    def _write_log(self, what: str, why: str = "") -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log.appendPlainText(f"[{stamp}] {what}")
        if why:
            self.log.appendPlainText(f"           Neden: {why}")
        self.log.appendPlainText("")
