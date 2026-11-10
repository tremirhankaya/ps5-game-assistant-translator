import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from ps5_translator.ui.subtitle_window import SubtitleWindow


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app):
    w = SubtitleWindow()
    w.show_line("Anahtar nerede?", "Where is the key?")
    w.show_line("Hemen gitmeliyiz!", "We need to move. Now!")
    w.show_line("Bekle, Franklin.", "Wait, Franklin.")
    return w


def test_every_line_is_kept_in_history(window):
    assert [l.translated for l in window.lines] == ["Anahtar nerede?", "Hemen gitmeliyiz!", "Bekle, Franklin."]
    assert window.history_list.count() == 3
    assert window.current_label.text() == "Bekle, Franklin."
    assert window.recent_label.text() == "Anahtar nerede?\nHemen gitmeliyiz!"


def test_same_line_twice_in_a_row_is_added_once(window):
    window.show_line("Bekle, Franklin.", "Wait, Franklin.")
    assert len(window.lines) == 3


def test_search_matches_turkish_and_english(window):
    window.search_box.setText("franklin")
    assert window.history_list.count() == 1
    window.search_box.setText("KEY")
    assert window.history_list.count() == 1
    assert "Anahtar nerede?" in window.history_list.item(0).text()
    window.search_box.setText("")
    assert window.history_list.count() == 3


def test_new_line_respects_active_search(window):
    window.search_box.setText("franklin")
    window.show_line("Gidelim.", "Let's go.")
    assert window.history_list.count() == 1
    assert len(window.lines) == 4


def test_history_button_switches_views(window):
    assert not window.showing_history
    assert window.history_button.text() == "Geçmiş (3)"
    window.toggle_history()
    assert window.showing_history
    window.toggle_history()
    assert not window.showing_history
