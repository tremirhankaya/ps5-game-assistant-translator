"""Full-screen subtitle view for the second monitor.

Live view: the current translation in large text, the English original below
it, and the previous few lines dimmed above, so the dialogue can be followed.
History view: every translation so far, scrollable and searchable.
Esc, F11 or a double-click leaves full screen; H switches between the views.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

RECENT_LINES = 3

_BUTTON_STYLE = (
    "QPushButton { color:#ccc; background:#222; border:1px solid #444; border-radius:6px; padding:8px 18px; }"
    "QPushButton:hover { background:#333; }"
)


@dataclass
class Line:
    time: str
    source: str
    translated: str

    def matches(self, query: str) -> bool:
        query = query.casefold()
        return query in self.source.casefold() or query in self.translated.casefold()


class SubtitleWindow(QWidget):
    closed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PS5 Game Assistant Translator - Altyazı")
        self.setStyleSheet("background:#000;")
        self.lines: list[Line] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 24, 40, 24)

        top = QHBoxLayout()
        top.addStretch()
        self.history_button = QPushButton()
        self.history_button.setStyleSheet(_BUTTON_STYLE)
        self.history_button.setFocusPolicy(Qt.NoFocus)
        self.history_button.clicked.connect(self.toggle_history)
        top.addWidget(self.history_button)
        outer.addLayout(top)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_live_page())
        self.pages.addWidget(self._build_history_page())
        outer.addWidget(self.pages, stretch=1)

        self.hint_label = self._label("#444")
        outer.addWidget(self.hint_label)
        self._update_texts()

    # -- pages

    def _label(self, color: str) -> QLabel:
        label = QLabel()
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"color:{color}; background:transparent;")
        return label

    def _build_live_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        layout.addStretch(1)
        self.recent_label = self._label("#777")
        layout.addWidget(self.recent_label)
        self.current_label = self._label("#fff")
        self.current_label.setText("Çeviri burada görünecek")
        layout.addWidget(self.current_label)
        self.source_label = self._label("#999")
        layout.addWidget(self.source_label)
        layout.addStretch(1)
        return page

    def _build_history_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Geçmişte ara (Türkçe ya da İngilizce)")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.setStyleSheet(
            "color:#fff; background:#161616; border:1px solid #444; border-radius:6px; padding:8px;"
        )
        self.search_box.textChanged.connect(self._refill_history)
        layout.addWidget(self.search_box)
        self.history_list = QListWidget()
        self.history_list.setWordWrap(True)
        self.history_list.setStyleSheet(
            "QListWidget { color:#ddd; background:#000; border:none; }"
            "QListWidget::item { padding:10px; border-bottom:1px solid #222; }"
            "QListWidget::item:selected { background:#1d2a3a; color:#fff; }"
        )
        layout.addWidget(self.history_list, stretch=1)
        return page

    # -- content

    def show_line(self, translated: str, source: str) -> bool:
        """Show a new line. Returns False if it repeats the line already on screen."""
        if self.lines and self.lines[-1].translated == translated and self.lines[-1].source == source:
            return False
        line = Line(datetime.now().strftime("%H:%M:%S"), source, translated)
        self.lines.append(line)
        recent = self.lines[-(RECENT_LINES + 1) : -1]
        self.recent_label.setText("\n".join(l.translated for l in recent))
        self.current_label.setText(translated)
        self.source_label.setText(source)
        if line.matches(self.search_box.text()):
            at_bottom = self._history_at_bottom()
            self._add_history_item(line)
            if at_bottom:
                self.history_list.scrollToBottom()
        self._update_texts()
        return True

    def _add_history_item(self, line: Line) -> None:
        item = QListWidgetItem(f"{line.time}   {line.translated}\n                 {line.source}")
        self.history_list.addItem(item)

    def _history_at_bottom(self) -> bool:
        bar = self.history_list.verticalScrollBar()
        return bar.value() >= bar.maximum() - 2

    def _refill_history(self) -> None:
        query = self.search_box.text()
        self.history_list.clear()
        for line in self.lines:
            if line.matches(query):
                self._add_history_item(line)
        self.history_list.scrollToBottom()

    # -- switching views

    @property
    def showing_history(self) -> bool:
        return self.pages.currentIndex() == 1

    def toggle_history(self) -> None:
        self.pages.setCurrentIndex(0 if self.showing_history else 1)
        if self.showing_history:
            self.history_list.scrollToBottom()
            self.search_box.setFocus()
        else:
            self.setFocus()
        self._update_texts()

    def _update_texts(self) -> None:
        if self.showing_history:
            self.history_button.setText("Canlı görünüme dön")
            self.hint_label.setText("Esc: canlı görünüme dön")
        else:
            self.history_button.setText(f"Geçmiş ({len(self.lines)})")
            self.hint_label.setText("H: geçmiş   ·   Esc ya da çift tık: tam ekrandan çık")

    def show_on(self, screen) -> None:
        """Open full screen on the given monitor."""
        self.setGeometry(screen.geometry())
        self.showFullScreen()
        self.setFocus()

    # -- sizing and keys

    def resizeEvent(self, event) -> None:
        h = max(self.height(), 200)
        for widget, share, weight in (
            (self.current_label, 1 / 13, QFont.DemiBold),
            (self.recent_label, 1 / 28, QFont.Normal),
            (self.source_label, 1 / 32, QFont.Normal),
            (self.history_list, 1 / 36, QFont.Normal),
            (self.search_box, 1 / 40, QFont.Normal),
            (self.history_button, 1 / 50, QFont.Normal),
            (self.hint_label, 1 / 60, QFont.Normal),
        ):
            font = QFont("Segoe UI")
            font.setPixelSize(max(int(h * share), 10))
            font.setWeight(weight)
            widget.setFont(font)
        super().resizeEvent(event)

    def keyPressEvent(self, event) -> None:
        key = event.key()
        if key == Qt.Key_Escape and self.showing_history:
            self.toggle_history()
        elif key in (Qt.Key_Escape, Qt.Key_F11):
            self.close()
        elif key == Qt.Key_H and not self.showing_history:
            self.toggle_history()
        else:
            super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if not self.showing_history:
            self.close()

    def closeEvent(self, event) -> None:
        self.closed.emit()
        super().closeEvent(event)
