"""
Automated validation for 2026 Minimalist SVG Icon & Action Card Buttons.
Verifies all buttons across all windows have valid icons/text, proper types, and descriptive tooltips/labels.
"""
import sys
from unittest.mock import MagicMock
from PyQt5.QtWidgets import QApplication, QPushButton, QToolButton, QAbstractButton

app = QApplication.instance() or QApplication(sys.argv)

def check_buttons(window_name, buttons, allow_text=False):
    print(f"\n--- Checking {window_name} ({len(buttons)} buttons) ---")
    for i, btn in enumerate(buttons):
        assert isinstance(btn, (QPushButton, QToolButton, QAbstractButton)), f"Element {i} is not a button: {type(btn)}"
        text = btn.text()
        icon = btn.icon()
        tip = btn.toolTip()
        
        has_icon = not icon.isNull()
        has_text = bool(text and text.strip())
        assert has_icon or has_text, f"[{window_name}] Button {btn.objectName()} has neither icon nor text"
        assert (tip and tip.strip()) or has_text, f"[{window_name}] Button {btn.objectName()} has neither tooltip nor text"
        print(f"  OK: obj='{btn.objectName()}', text='{text}', tip='{tip}'")

def test_floating_controls():
    from src.ui.floating_controls import FloatingControlWidget as FCW1
    from src_minimal.ui.floating_controls import FloatingControlWidget as FCW2
    
    mock_app = MagicMock()
    for name, Cls in [("src.FloatingControlWidget", FCW1), ("src_minimal.FloatingControlWidget", FCW2)]:
        w = Cls(mock_app)
        btns = [w.pause_btn, w.caption_btn, w.input_btn, w.exit_btn]
        check_buttons(name, btns)
        
        # Test state sync toggle
        w.sync_state(True)
        w.sync_state(False)
        print(f"  State toggling passed for {name}")

def test_caption_window():
    from src.caption_window import CaptionWindow as CW1
    from src_minimal.caption_window import CaptionWindow as CW2
    
    mock_app = MagicMock()
    mock_cfg = MagicMock()
    mock_cfg.get.side_effect = lambda key, default=None: "both" if key == "display_mode" else (14 if "font" in key else default)
    
    # CW1 (src)
    c1 = CW1(mock_cfg, None, mock_app)
    btns1 = [c1.display_mode_btn, c1.summary_toggle, c1.summary_pause_btn, c1.new_session_btn, c1.history_btn, c1.min_btn, c1.close_btn]
    check_buttons("src.CaptionWindow", btns1, allow_text=True)
    c1._cycle_display_mode()
    c1._toggle_summary()
    c1.set_summary_enabled(False)
    print("  State toggling passed for src.CaptionWindow")
    
    # CW2 (src_minimal)
    c2 = CW2(mock_cfg, None, mock_app)
    btns2 = [c2.new_session_btn, c2.history_btn, c2.min_btn, c2.close_btn]
    check_buttons("src_minimal.CaptionWindow", btns2, allow_text=True)

def test_live_input_window():
    from src.ui.live_input_window import LiveInputWindow as LIW1
    from src_minimal.ui.live_input_window import LiveInputWindow as LIW2
    
    mock_app = MagicMock()
    mock_app.receive_tts_enabled = True
    
    # LIW1 (src)
    w1 = LIW1(mock_app)
    btns1 = [
        w1.pause_btn, w1.caption_btn, w1.mark_btn, w1.setup_audio_btn, w1.restore_audio_btn,
        w1.hide_btn, w1.detach_btn, w1.caption_section_toggle, w1.summary_toggle_btn,
        w1.new_session_btn, w1.history_btn, w1.clear_btn, w1.reply_btn, w1.auto_reply_btn,
        w1.speak_btn, w1.translate_btn, w1.min_btn, w1.close_btn
    ]
    check_buttons("src.LiveInputWindow", btns1, allow_text=True)
    w1.set_detached_mode(True)
    w1.set_detached_mode(False)
    w1._on_capture_state_update(True)
    w1._on_capture_state_update(False)
    w1._on_caption_enabled_update(False)
    w1._on_summary_enabled_update(False)
    print("  State toggling passed for src.LiveInputWindow")

    # LIW2 (src_minimal)
    w2 = LIW2(mock_app)
    btns2 = [
        w2.pause_btn, w2.caption_btn, w2.mark_btn, w2.setup_audio_btn, w2.restore_audio_btn,
        w2.receive_tts_btn, w2.hide_btn, w2.detach_btn, w2.caption_section_toggle,
        w2.clear_btn, w2.speak_btn, w2.translate_btn, w2.min_btn, w2.close_btn
    ]
    check_buttons("src_minimal.LiveInputWindow", btns2, allow_text=True)
    w2.set_detached_mode(True)
    w2.set_detached_mode(False)
    w2._on_capture_state_update(True)
    w2._on_capture_state_update(False)
    w2._on_caption_enabled_update(False)
    w2._update_receive_tts_btn(True)
    w2._update_receive_tts_btn(False)
    print("  State toggling passed for src_minimal.LiveInputWindow")

def test_settings_window():
    from src.ui.settings_window import SettingsWindow as SW1
    from src_minimal.ui.settings_window import SettingsWindow as SW2
    
    mock_app = MagicMock()
    for name, Cls in [("src.SettingsWindow", SW1), ("src_minimal.SettingsWindow", SW2)]:
        s = Cls({}, mock_app)
        # Skip internal Qt scroll arrows (empty objectName) – they have no icon or text
        btns = [b for b in s.window.findChildren(QAbstractButton) if b.objectName()]
        check_buttons(name, btns, allow_text=True)

if __name__ == "__main__":
    print("Starting automated verification of 2026 SVG buttons...")
    test_floating_controls()
    test_caption_window()
    test_live_input_window()
    test_settings_window()
    print("\n==========================================")
    print(" ALL BUTTON CHECKS PASSED SUCCESSFULLY! ")
    print("==========================================")
