"""Full-screen subtitle view for the second monitor.

Shows the current translation in large text, the English original below it,
and the previous few lines dimmed above, so the dialogue can be followed.
Esc, F11 or a double-click leaves full screen.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

HISTORY_LINES = 3


class SubtitleWindow(QWidget):
    closed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PS5 Game Assistant Translator - Altyazı")
        self.setStyleSheet("background:#000;")
        self._history: list[str] = []
        self._current = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 40, 60, 30)
        layout.setSpacing(24)
        layout.addStretch(1)

        self.history_label = self._label("#777")
        layout.addWidget(self.history_label)
        self.current_label = self._label("#fff")
        self.current_label.setText("Çeviri burada görünecek")
        layout.addWidget(self.current_label)
        self.source_label = self._label("#999")
        layout.addWidget(self.source_label)

        layout.addStretch(1)
        self.hint_label = self._label("#444")
        self.hint_label.setText("Çıkmak için Esc ya da çift tık")
        layout.addWidget(self.hint_label)

    def _label(self, color: str) -> QLabel:
        label = QLabel()
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"color:{color}; background:transparent;")
        return label

    def show_line(self, translated: str, source: str) -> None:
        if translated == self._current:
            return
        if self._current:
            self._history = (self._history + [self._current])[-HISTORY_LINES:]
        self._current = translated
        self.history_label.setText("\n".join(self._history))
        self.current_label.setText(translated)
        self.source_label.setText(source)

    def show_on(self, screen) -> None:
        """Open full screen on the given monitor."""
        self.setGeometry(screen.geometry())
        self.showFullScreen()

    # -- sizing and leaving

    def resizeEvent(self, event) -> None:
        h = max(self.height(), 200)
        for label, share, weight in (
            (self.current_label, 1 / 13, QFont.DemiBold),
            (self.history_label, 1 / 28, QFont.Normal),
            (self.source_label, 1 / 32, QFont.Normal),
            (self.hint_label, 1 / 60, QFont.Normal),
        ):
            font = QFont("Segoe UI")
            font.setPixelSize(max(int(h * share), 10))
            font.setWeight(weight)
            label.setFont(font)
        super().resizeEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key_Escape, Qt.Key_F11):
            self.close()
        else:
            super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        self.close()

    def closeEvent(self, event) -> None:
        self.closed.emit()
        super().closeEvent(event)
