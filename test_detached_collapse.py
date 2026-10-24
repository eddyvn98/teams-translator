import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication
from src.ui.live_input_window import LiveInputWindow as FullLIW
from src_minimal.ui.live_input_window import LiveInputWindow as MinimalLIW


class _DummyApp:
    def __init__(self):
        self.receive_tts_enabled = False
        self.translator = None

    def _toggle_capture(self):
        pass

    def _toggle_caption(self):
        pass

    def _mark_target_input(self):
        pass

    def manual_setup_audio(self):
        pass

    def manual_restore_audio(self):
        pass

    def _minimize_to_floating(self):
        pass

    def _toggle_detached_caption_panel(self):
        pass

    def _toggle_summary_updates(self):
        pass

    def start_new_session(self):
        pass

    def open_session_history(self):
        pass

    def toggle_receive_tts(self):
        pass


class DetachedCollapseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_src_minimal_detached_collapses_and_restores(self):
        app_ref = _DummyApp()
        win = MinimalLIW(app_ref)
        win.show()

        # Initial attached state
        self.assertEqual(win.minimumHeight(), 660)
        self.assertFalse(win._detached_mode)
        self.assertEqual(win.caption_title.text(), "LIVE TRANSLATION")
        self.assertTrue(win.caption_en_view.isVisible())
        self.assertTrue(win.caption_vi_view.isVisible())

        # Detach
        win.set_detached_mode(True)
        self.assertTrue(win._detached_mode)
        self.assertEqual(win.caption_title.text(), "LIVE TRANSLATION (ĐÃ TÁCH)")
        self.assertFalse(win.caption_en_view.isVisible())
        self.assertFalse(win.caption_vi_view.isVisible())
        self.assertFalse(win.caption_section_toggle.isVisible())
        self.assertLessEqual(win.minimumHeight(), 250)
        self.assertLessEqual(win.height(), 400)

        # Signal update while detached does not break compact mode
        win.set_caption_enabled(True)
        self.assertFalse(win.caption_en_view.isVisible())
        self.assertLessEqual(win.height(), 400)

        # Re-attach
        win.set_detached_mode(False)
        self.assertFalse(win._detached_mode)
        self.assertEqual(win.caption_title.text(), "LIVE TRANSLATION")
        self.assertTrue(win.caption_en_view.isVisible())
        self.assertTrue(win.caption_vi_view.isVisible())
        self.assertEqual(win.minimumHeight(), 660)
        self.assertGreaterEqual(win.height(), 660)

    def test_src_full_detached_collapses_and_restores(self):
        app_ref = _DummyApp()
        win = FullLIW(app_ref)
        win.show()

        # Initial attached state
        self.assertEqual(win.minimumHeight(), 520)
        self.assertFalse(win._detached_mode)
        self.assertEqual(win.caption_title.text(), "LIVE CAPTION")
        self.assertTrue(win.caption_view.isVisible())

        # Detach
        win.set_detached_mode(True)
        self.assertTrue(win._detached_mode)
        self.assertEqual(win.caption_title.text(), "LIVE CAPTION (ĐÃ TÁCH)")
        self.assertFalse(win.caption_view.isVisible())
        self.assertFalse(win.summary_view.isVisible())
        self.assertFalse(win.caption_section_toggle.isVisible())
        self.assertLessEqual(win.minimumHeight(), 380)
        self.assertLessEqual(win.height(), 500)

        # Signal update while detached does not break compact mode
        win.set_caption_enabled(True)
        self.assertFalse(win.caption_view.isVisible())
        self.assertLessEqual(win.height(), 500)

        # Re-attach
        win.set_detached_mode(False)
        self.assertFalse(win._detached_mode)
        self.assertEqual(win.caption_title.text(), "LIVE CAPTION")
        self.assertTrue(win.caption_view.isVisible())
        self.assertEqual(win.minimumHeight(), 520)
        self.assertGreaterEqual(win.height(), 520)

    def test_minimal_vn_input_auto_resize(self):
        app_ref = _DummyApp()
        win = MinimalLIW(app_ref)
        win.show()

        # Initial single-line height (56px for non-clipped Vietnamese descenders)
        initial_h = win.vn_input.height()
        self.assertLessEqual(initial_h, 60)
        self.assertGreaterEqual(initial_h, 50)

        # Multi-line typing expands input
        win.vn_input.setPlainText("Dòng 1\nDòng 2\nDòng 3\nDòng 4\nDòng 5")
        multiline_h = win.vn_input.height()
        self.assertGreater(multiline_h, initial_h)
        self.assertLessEqual(multiline_h, 160)

        # Clearing text shrinks input back
        win.vn_input.clear()
        cleared_h = win.vn_input.height()
        self.assertEqual(cleared_h, initial_h)

    def test_minimal_input_section_toggle_and_config_persistence(self):
        class _ConfigDummyApp(_DummyApp):
            def __init__(self):
                super().__init__()
                self._store = {}
                self.config = self

            def get(self, key, default=None):
                return self._store.get(key, default)

            def set(self, key, value):
                self._store[key] = value

        app_ref = _ConfigDummyApp()
        win = MinimalLIW(app_ref)
        win.show()

        self.assertTrue(win.input_container.isVisible())
        self.assertTrue(win._input_section_visible)

        # Toggle to hide
        win.toggle_input_section()
        self.assertFalse(win.input_container.isVisible())
        self.assertFalse(win._input_section_visible)
        self.assertFalse(app_ref.get("input_section_visible"))

        # Reopen new window should restore hidden state
        win2 = MinimalLIW(app_ref)
        win2.show()
        self.assertFalse(win2.input_container.isVisible())
        self.assertFalse(win2._input_section_visible)

        # Toggle to show
        win2.toggle_input_section()
        self.assertTrue(win2.input_container.isVisible())
        self.assertTrue(win2._input_section_visible)
        self.assertTrue(app_ref.get("input_section_visible"))

    def test_detached_removes_empty_space(self):
        app_ref = _DummyApp()
        win = MinimalLIW(app_ref)
        win.show()

        win.set_detached_mode(True)
        # Verify distance between caption title and input title is compact (no large white space)
        gap = win.input_title.y() - win.caption_title.y()
        self.assertLess(gap, 60)
        self.assertLessEqual(win.height(), 350)


if __name__ == "__main__":
    unittest.main()
