import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from src.caption_window import CaptionWindow


class _Config:
    def get(self, key, default=None):
        values = {
            "display_mode": "en_only",
            "caption_width": 720,
            "caption_height": 360,
            "caption_font_size": 14,
            "caption_opacity": 0.85,
        }
        return values.get(key, default)

    def set(self, key, value):
        pass


class CaptionWindowLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_live_caption_box_is_above_history_and_summary(self):
        window = CaptionWindow(_Config())
        layout = window.card.layout()

        live_index = layout.indexOf(window.live_caption_box)
        history_index = layout.indexOf(window.history_view)
        summary_index = layout.indexOf(window.summary_view)

        self.assertLess(live_index, history_index)
        self.assertLess(live_index, summary_index)


if __name__ == "__main__":
    unittest.main()
