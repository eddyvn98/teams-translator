import unittest

from src.app_controller import TeamsTranslatorApp


class _Translator:
    def detect_language(self, text):
        return "en"

    def translate_bidirectional(self, text, direction="auto"):
        return {
            "source_text": text,
            "target_text": f"vi:{text}",
            "source_lang": "en",
            "display_text": f"vi:{text}",
        }


class _CaptionSink:
    def __init__(self):
        self.items = []

    def show_caption(self, payload):
        self.items.append(payload)

    def update_live_caption(self, payload):
        self.items.append(payload)


class AppControllerInterimCaptionTests(unittest.TestCase):
    def test_interim_loopback_caption_is_not_appended_to_history(self):
        app = TeamsTranslatorApp.__new__(TeamsTranslatorApp)
        app.translator = _Translator()
        app.caption_window = _CaptionSink()
        app.live_input_window = _CaptionSink()
        app._status = {"caption": True}
        app._last_loopback_display = ""
        app._last_loopback_partial_text = ""
        app._last_loopback_partial_at = 0
        app.config = None
        appended = []
        app._append_session_text = lambda payload: appended.append(payload)

        app._on_loopback_result("we need the updated number", is_final=False)

        self.assertEqual(app.caption_window.items[0]["is_final"], False)
        self.assertEqual(app.caption_window.items[0]["target_text"], "")
        self.assertEqual(appended, [])


if __name__ == "__main__":
    unittest.main()
