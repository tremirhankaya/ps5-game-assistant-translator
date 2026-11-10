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
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..explain import explain
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
        top.addStretch()
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
        if load_ms is not None:
            self._write_log(
                f"{engine.name} hazır (yükleme {load_ms / 1000:.1f} sn).",
                "Model 30 dakika bellekte kalacak, sonraki çeviriler hızlı olacak.",
            )
        self._write_log(
            f"Motor değişti: {engine.name}",
            "Önceki çeviriler silindi, çünkü farklı motorların sonuçları karışmasın.",
        )

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
        self.subtitle.setText(result.translated)
        source_note = "kayıttan" if result.from_cache else f"{result.ms:.0f} ms"
        self.source.setText(f"{result.source}   ·   {source_note}")

    def _write_log(self, what: str, why: str = "") -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log.appendPlainText(f"[{stamp}] {what}")
        if why:
            self.log.appendPlainText(f"           Neden: {why}")
        self.log.appendPlainText("")
