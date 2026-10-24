import os
import unittest
from unittest.mock import MagicMock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication
from src.caption_window import CaptionWindow as SrcCaptionWindow
from src.ui.live_input_window import LiveInputWindow as SrcLiveInputWindow
from src_minimal.caption_window import CaptionWindow as MinCaptionWindow
from src_minimal.ui.live_input_window import LiveInputWindow as MinLiveInputWindow


class AutoScrollTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_caption_window_autoscroll_on_new_stt_and_translation(self):
        win = SrcCaptionWindow()
        win.resize(600, 200)
        win.show()

        bar = win.history_view.verticalScrollBar()

        # Feed 25 captions
        for i in range(25):
            win.show_caption({
                "source_text": f"English speech transcript number {i}",
                "target_text": f"Ban dich tieng Viet so {i}",
                "source_lang": "en",
                "is_final": True
            })
            self.app.processEvents()

        self.assertGreater(bar.maximum(), 0)
        self.assertEqual(bar.value(), bar.maximum())

        # Simulate user scrolling up — do this right before the next caption event
        # (processEvents would fire pending singleShot timers and auto-scroll)
        bar.setValue(0)

        # New interim STT arrives
        win.show_caption({
            "source_text": "New incoming interim speech",
            "target_text": "",
            "source_lang": "en",
            "is_final": False
        })
        self.app.processEvents()
        self.assertEqual(bar.value(), bar.maximum())

        # Final translation arrives
        win.show_caption({
            "source_text": "New incoming interim speech",
            "target_text": "Ban dich noi dung moi nhat",
            "source_lang": "en",
            "is_final": True
        })
        self.app.processEvents()
        self.assertEqual(bar.value(), bar.maximum())

    def test_live_input_window_autoscroll_on_new_caption(self):
        mock_app = MagicMock()
        win = SrcLiveInputWindow(mock_app)
        win.resize(500, 400)
        win.show()

        bar = win.caption_view.verticalScrollBar()

        for i in range(25):
            win.update_live_caption({
                "source_text": f"English transcript {i}",
                "target_text": f"Ban dich tieng Viet {i}",
                "source_lang": "en",
                "is_final": True
            })
            self.app.processEvents()

        self.assertGreater(bar.maximum(), 0)
        self.assertEqual(bar.value(), bar.maximum())

        # Simulate user scrolling up
        bar.setValue(0)
        self.app.processEvents()
        self.assertEqual(bar.value(), 0)

        # New STT and translation arrives
        win.update_live_caption({
            "source_text": "Latest speech sentence",
            "target_text": "Cau dich moi nhat",
            "source_lang": "en",
            "is_final": True
        })
        self.app.processEvents()
        self.assertEqual(bar.value(), bar.maximum())

    def test_minimal_caption_window_autoscroll(self):
        win = MinCaptionWindow()
        win.resize(600, 200)
        win.show()

        bar = win.history_view.verticalScrollBar()

        for i in range(25):
            win.show_caption({
                "source_text": f"Speech sentence {i}",
                "target_text": f"Cau dich {i}",
                "source_lang": "en",
                "is_final": True
            })
            self.app.processEvents()

        self.assertGreater(bar.maximum(), 0)
        self.assertEqual(bar.value(), bar.maximum())

    def test_minimal_live_input_window_autoscroll(self):
        mock_app = MagicMock()
        win = MinLiveInputWindow(mock_app)
        win.resize(500, 400)
        win.show()

        bar_en = win.caption_en_view.verticalScrollBar()
        bar_vi = win.caption_vi_view.verticalScrollBar()

        for i in range(25):
            win.update_live_caption({
                "source_text": f"Speech sentence {i}",
                "target_text": f"Cau dich {i}",
                "source_lang": "en",
                "is_final": True
            })
            self.app.processEvents()

        self.assertGreater(bar_en.maximum(), 0)
        self.assertEqual(bar_en.value(), bar_en.maximum())
        self.assertGreater(bar_vi.maximum(), 0)
        self.assertEqual(bar_vi.value(), bar_vi.maximum())


if __name__ == "__main__":
    unittest.main()
