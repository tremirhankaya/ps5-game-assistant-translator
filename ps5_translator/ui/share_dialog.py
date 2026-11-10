"""Dialog with the address and QR code for opening the subtitle page on a phone."""
from __future__ import annotations

import io

import segno
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout


def qr_pixmap(text: str, scale: int = 8) -> QPixmap:
    buffer = io.BytesIO()
    segno.make(text, error="m").save(buffer, kind="png", scale=scale, border=3)
    pixmap = QPixmap()
    pixmap.loadFromData(buffer.getvalue(), "PNG")
    return pixmap


class ShareDialog(QDialog):
    def __init__(self, url: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Telefonda göster")
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        intro = QLabel("Telefonun kamerasıyla QR kodu okut ya da adresi tarayıcıya yaz.")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        qr = QLabel()
        qr.setAlignment(Qt.AlignCenter)
        qr.setPixmap(qr_pixmap(url))
        layout.addWidget(qr)

        address = QLabel(url)
        address.setAlignment(Qt.AlignCenter)
        address.setFont(QFont("Consolas", 13))
        address.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(address)

        notes = QLabel(
            "• Telefon ve bilgisayar aynı Wi-Fi ağında olmalı.\n"
            "• Sayfa açılmazsa Windows Güvenlik Duvarı'nda bu uygulamaya 'Özel ağlar' için izin ver.\n"
            "• Telefon ekranı kapanmasın diye telefonun ayarlarından ekran zaman aşımını uzat.\n"
            "• Bu pencereyi kapatabilirsin; paylaşım 'Telefonda göster' düğmesi basılı kaldıkça sürer."
        )
        notes.setWordWrap(True)
        notes.setStyleSheet("color:#888;")
        layout.addWidget(notes)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
