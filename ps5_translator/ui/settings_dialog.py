"""Settings: choose how subtitles are translated."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
)

from .. import settings
from ..translation import opus_engine


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ayarlar")
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        layout.addWidget(QLabel("<b>Çeviri nasıl yapılsın?</b>"))

        self.deepl_radio = QRadioButton("DeepL (önerilen): daha iyi çeviri, ücretsiz API anahtarı gerekir")
        layout.addWidget(self.deepl_radio)
        self.key_box = QLineEdit(settings.get_deepl_key() or "")
        self.key_box.setEchoMode(QLineEdit.Password)
        self.key_box.setPlaceholderText("DeepL API anahtarı (deepl.com/pro-api, sonu :fx ile biter)")
        layout.addWidget(self.key_box)
        layout.addWidget(self._note(
            "Ayda 500.000 karakter ücretsiz. Anahtar Windows Kimlik Bilgisi Yöneticisi'nde saklanır. "
            "Altyazı metinleri çevrilmek üzere DeepL'e gönderilir."
        ))

        self.opus_radio = QRadioButton("Yerel model (OPUS-MT): anahtar ve internet gerekmez, çeviri kalitesi daha düşük")
        layout.addWidget(self.opus_radio)
        downloaded = "Model indirilmiş." if opus_engine.is_downloaded() else (
            f"İlk kullanımda yaklaşık {opus_engine.MODEL_SIZE_MB} MB'lık model bir kez indirilir."
        )
        layout.addWidget(self._note(
            f"Çeviri tamamen bu bilgisayarda yapılır, hiçbir metin dışarı gönderilmez. {downloaded}"
        ))

        (self.opus_radio if settings.get_engine() == settings.ENGINE_OPUS else self.deepl_radio).setChecked(True)
        self.deepl_radio.toggled.connect(self.key_box.setEnabled)
        self.key_box.setEnabled(self.deepl_radio.isChecked())

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _note(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet("color:#888; margin-left:22px;")
        return label

    @property
    def engine(self) -> str:
        return settings.ENGINE_OPUS if self.opus_radio.isChecked() else settings.ENGINE_DEEPL

    @property
    def deepl_key(self) -> str:
        return self.key_box.text().strip()
