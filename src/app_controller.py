import logging
import os
import sys
import threading
import time

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon, QCursor

from src.config_manager import ConfigManager
from src.translator import Translator
from src.speech_to_text import SpeechToText
from src.loopback_capture import LoopbackCapture
from src.caption_window import CaptionWindow
from src.teams_agent import TeamsAgent
from src.ui.floating_controls import FloatingControlWidget
from src.ui.settings_window import SettingsWindow
from src.ui.live_input_window import LiveInputWindow
from src.qwen_stt import QwenSTT

logger = logging.getLogger("TeamsTranslator")

class TeamsTranslatorApp:
    """
    Application chính. Chạy trong system tray.
    Pipeline: Loopback/Mic → STT → Dịch → Caption overlay
    """

    # Các chế độ capture
    MODE_LOOPBACK = "loopback"   # Bắt âm thanh số từ Windows (khuyên dùng)
    MODE_MIC = "mic"             # Dùng microphone
    MODE_OCR = "ocr"             # Đọc Teams live caption từ màn hình

    def __init__(self):
        self.config = ConfigManager()
        self.translator = Translator(self.config)
        self.stt = SpeechToText(self.config)
        self.loopback = LoopbackCapture(self.config)
        self.teams = TeamsAgent(self.config)
        self._ai_helper = QwenSTT(self.config)

        # Qt Application
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setApplicationName("Teams Translator")
        self.app.setApplicationDisplayName("Teams Translator - Caption Meeting")

        # Caption window
        self.caption_window = CaptionWindow(self.config)
        self.floating_controls = FloatingControlWidget(self)
        self.live_input_window = LiveInputWindow(self)

        # System tray
        self._settings_window = None
        self._setup_tray()

        # Hotkeys
        self._hotkeys_registered = False
        self._register_hotkeys()

        # Trạng thái
        self._capture_mode = self.MODE_LOOPBACK  # Mặc định: loopback
        self._caption_enabled = True

        # Connect callbacks
        self.loopback.set_on_result(self._on_loopback_result)
        self.stt.set_on_result(self._on_stt_result)
        self.teams.set_on_text_received(self._on_teams_caption)

        # Status
        self._status = {
            "mode": self._capture_mode,
            "capturing": False,
            "caption": True,
        }
        self.floating_controls.sync_state(capturing=False)
        self.floating_controls.move(20, 120)
        self.floating_controls.show()
        self.live_input_window.move(20, 190)
        self.live_input_window.show()

        self._ensure_icon()
        self._last_loopback_display = ""
        self._session_transcript = []
        self._last_summary_at = 0.0
        self._last_summarized_snapshot = ""


    def _set_caption_visible(self, visible: bool):
        """Ẩn hoặc hiện caption overlay (không ảnh hưởng tới trạng thái capture)."""
        self._caption_enabled = visible
        self._status["caption"] = visible
        self.act_caption.setChecked(visible)
        if visible:
            self.caption_window.show()
            self._notify("📺 Caption đã hiện lại")
        else:
            self.caption_window.hide()
            self._notify("📺 Caption đã ẩn (dùng Ctrl+Shift+C để hiện lại)")

    def _ensure_icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "icon.png")
        if not os.path.exists(icon_path):
            try:
                from PIL import Image, ImageDraw
                img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                draw.rounded_rectangle([4, 4, 60, 60], radius=12, fill=(0, 100, 200, 255), outline=(100, 180, 255, 255), width=2)
                draw.text((18, 12), "TT", fill=(255, 255, 255, 255), font=None)
                os.makedirs(os.path.dirname(icon_path), exist_ok=True)
                img.save(icon_path)
            except Exception as e:
                logger.warning(f"Không tạo được icon: {e}")

    def _setup_tray(self):
        icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "icon.png")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else self._make_icon_fallback()
        self.tray = QSystemTrayIcon(icon, parent=self.app)
        self.tray.setToolTip("Teams Translator 🇻🇳🇬🇧")
        menu = QMenu()

        # ===== NHÓM ĐIỀU KHIỂN CHÍNH =====
        capture_menu = menu.addMenu("🎯 Điều khiển")

        # Nút bắt/dừng
        self.act_capture = QAction("▶️ Bắt đầu capture")
        self.act_capture.triggered.connect(self._toggle_capture)
        capture_menu.addAction(self.act_capture)

        capture_menu.addSeparator()

        # Chế độ capture
        self.act_loopback = QAction("🔄 Loopback (khuyên dùng)", checkable=True)
        self.act_loopback.setChecked(True)
        self.act_loopback.triggered.connect(lambda: self._set_mode(self.MODE_LOOPBACK))
        capture_menu.addAction(self.act_loopback)

        self.act_mic = QAction("🎤 Micro", checkable=True)
        self.act_mic.triggered.connect(lambda: self._set_mode(self.MODE_MIC))
        capture_menu.addAction(self.act_mic)

        self.act_ocr = QAction("📖 OCR Teams Caption", checkable=True)
        self.act_ocr.triggered.connect(lambda: self._set_mode(self.MODE_OCR))
        capture_menu.addAction(self.act_ocr)

        menu.addSeparator()

        # ===== CAPTION OVERLAY =====
        caption_menu = menu.addMenu("📺 Caption")

        self.act_caption = QAction("Bật caption overlay", checkable=True)
        self.act_caption.setChecked(True)
        self.act_caption.triggered.connect(self._toggle_caption)
        caption_menu.addAction(self.act_caption)

        act_caption_hide = QAction("Ẩn caption ngay")
        act_caption_hide.triggered.connect(lambda: self._set_caption_visible(False))
        caption_menu.addAction(act_caption_hide)

        act_caption_show = QAction("Hiện caption lại")
        act_caption_show.triggered.connect(lambda: self._set_caption_visible(True))
        caption_menu.addAction(act_caption_show)

        menu.addSeparator()

        # ===== LIVE INPUT =====
        live_menu = menu.addMenu("⌨️ Gõ VN -> EN")
        self.act_live_input = QAction("Hiện ô gõ trung gian", checkable=True)
        self.act_live_input.setChecked(True)
        self.act_live_input.triggered.connect(self._toggle_live_input)
        live_menu.addAction(self.act_live_input)

        act_mark_target = QAction("Đánh dấu input đích (Ctrl+Shift+V)")
        act_mark_target.triggered.connect(self._mark_target_input)
        live_menu.addAction(act_mark_target)

        menu.addSeparator()

        # ===== CÔNG CỤ =====
        tools_menu = menu.addMenu("🔧 Công cụ")

        act_devices = QAction("🔊 Kiểm tra thiết bị audio")
        act_devices.triggered.connect(self._show_audio_devices)
        tools_menu.addAction(act_devices)

        act_settings = QAction("⚙️ Mở cài đặt")
        act_settings.triggered.connect(self._open_settings)
        tools_menu.addAction(act_settings)

        tools_menu.addSeparator()

        act_about = QAction("ℹ️ Giới thiệu / Hướng dẫn")
        act_about.triggered.connect(self._show_about)
        tools_menu.addAction(act_about)

        tools_menu.addSeparator()
        act_quit_tools = QAction("⏹️ Thoát hẳn app")
        act_quit_tools.triggered.connect(self._quit)
        tools_menu.addAction(act_quit_tools)

        menu.addSeparator()

        # ===== THOÁT =====
        act_quit_top = QAction("⏹️ Thoát hẳn app")
        act_quit_top.triggered.connect(self._quit)
        menu.addAction(act_quit_top)

        menu.addSeparator()
        act_quit = QAction("⏹️ Dừng hẳn và thoát app")
        act_quit.triggered.connect(self._quit)
        menu.addAction(act_quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

        self.tray.showMessage(
            "Teams Translator",
            "🚀 Đã khởi động!\n"
            "Dùng menu system tray để điều khiển.\n"
            "Hotkey: Ctrl+Shift+T (bắt/dừng), Ctrl+Shift+C (caption), Ctrl+Alt+Q (thoát)",
            QSystemTrayIcon.MessageIcon.Information,
            5000
        )

    def _make_icon_fallback(self) -> QIcon:
        """Tạo icon fallback inline bằng QPixmap (không cần file)."""
        from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush
        from PyQt5.QtCore import QRect, Qt

        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Rounded rect nền
        painter.setPen(QPen(QColor(100, 180, 255), 2))
        painter.setBrush(QBrush(QColor(0, 100, 200)))
        painter.drawRoundedRect(4, 4, 56, 56, 12, 12)
        # Chữ TT
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Arial", 18, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(QRect(0, 12, 64, 40), Qt.AlignmentFlag.AlignCenter, "TT")
        painter.end()
        return QIcon(pixmap)

    def _register_hotkeys(self):
        if self._hotkeys_registered:
            return
        try:
            import keyboard

            def on_toggle():
                self._toggle_capture()

            def on_toggle_caption():
                self._toggle_caption()

            def on_quit():
                logger.info("Hotkey Ctrl+Shift+Q: thoát app")
                self._notify("⏹️ Đang thoát app...")
                # Gọi quit trên main thread qua QTimer
                QTimer.singleShot(100, self._quit)

            def on_hide_show():
                self._toggle_caption()

            def on_mark_target():
                self._mark_target_input()

            keyboard.add_hotkey('ctrl+shift+t', on_toggle)
            keyboard.add_hotkey('ctrl+shift+c', on_toggle_caption)
            keyboard.add_hotkey('ctrl+alt+q', on_quit)
            keyboard.add_hotkey('ctrl+shift+h', on_hide_show)
            keyboard.add_hotkey('ctrl+shift+v', on_mark_target)

            self._hotkeys_registered = True
            logger.info("Hotkeys đã đăng ký:")
            logger.info("  Ctrl+Shift+T: Bắt đầu/Dừng capture")
            logger.info("  Ctrl+Shift+C: Bật/Tắt caption overlay")
            logger.info("  Ctrl+Shift+H: Bật/Tắt caption (alias)")
            logger.info("  Ctrl+Alt+Q: Thoát app hoàn toàn")
            logger.info("  Ctrl+Shift+V: Đánh dấu input đích dưới chuột")
        except Exception as e:
            logger.warning(f"Không register được hotkeys: {e}")

    # ============ CHẾ ĐỘ ============

    def _set_mode(self, mode: str):
        """Đổi chế độ capture."""
        # Cập nhật UI check
        self.act_loopback.setChecked(mode == self.MODE_LOOPBACK)
        self.act_mic.setChecked(mode == self.MODE_MIC)
        self.act_ocr.setChecked(mode == self.MODE_OCR)

        # Nếu đang capture thì dừng rồi chuyển
        was_capturing = self._status["capturing"]
        if was_capturing:
            self._stop_current_capture()

        self._capture_mode = mode
        self._status["mode"] = mode

        mode_names = {
            self.MODE_LOOPBACK: "🔄 Loopback",
            self.MODE_MIC: "🎤 Micro",
            self.MODE_OCR: "📖 OCR",
        }
        logger.info(f"Đã chuyển sang chế độ: {mode_names.get(mode, mode)}")

        if was_capturing:
            self._start_capture()
            self._notify(f"Đã chuyển sang {mode_names.get(mode, mode)}")
        else:
            self._notify(f"Đã chọn {mode_names.get(mode, mode)}. Nhấn '▶️ Bắt đầu' để chạy.")

    # ============ CAPTURE CONTROL ============

    def _toggle_capture(self):
        if self._status["capturing"]:
            self._stop_current_capture()
            self.act_capture.setText("▶️ Bắt đầu")
            self._status["capturing"] = False
            self.floating_controls.sync_state(capturing=False)
            self._notify("⏹️ Đã dừng")
        else:
            self._start_capture()
            self.act_capture.setText("⏹️ Dừng")
            self._status["capturing"] = True
            self.floating_controls.sync_state(capturing=True)
            self._notify(f"▶️ Đang lắng nghe (chế độ {self._get_mode_name()})")

    def _get_mode_name(self) -> str:
        return {
            self.MODE_LOOPBACK: "Loopback - bắt trực tiếp từ Windows",
            self.MODE_MIC: "Micro",
            self.MODE_OCR: "OCR Teams Caption",
        }.get(self._capture_mode, self._capture_mode)

    def _start_capture(self):
        if self._capture_mode == self.MODE_LOOPBACK:
            self._start_loopback()
        elif self._capture_mode == self.MODE_MIC:
            self._start_stt()
        elif self._capture_mode == self.MODE_OCR:
            self._start_ocr()

    def _stop_current_capture(self):
        self._stop_loopback()
        self._stop_stt()
        self._stop_ocr()

    def _start_loopback(self):
        try:
            self.loopback.start_capture()
        except Exception as e:
            logger.error(f"Lỗi start loopback: {e}")
            self._notify("❌ Lỗi loopback. Kiểm tra 'Kiểm tra thiết bị audio'")

    def _stop_loopback(self):
        try:
            self.loopback.stop_capture()
        except Exception:
            pass

    def _start_stt(self):
        try:
            self.stt.start_listening(language="en-US")
        except Exception as e:
            logger.error(f"Lỗi start micro: {e}")
            self._notify("❌ Lỗi micro. Kiểm tra thiết bị âm thanh")

    def _stop_stt(self):
        try:
            self.stt.stop_listening()
        except Exception:
            pass

    def _start_ocr(self):
        """Bắt đầu monitor Teams live caption."""
        try:
            has_tess = self.teams.check_tesseract_installed()
            if not has_tess:
                self._notify("⚠️ Cần cài Tesseract OCR. Xem log để biết chi tiết.")
                return
            self.teams.start_live_caption_monitor(interval=2.0)
            logger.info("📖 OCR caption monitor đã bắt đầu")
        except Exception as e:
            logger.error(f"Lỗi start OCR: {e}")

    def _stop_ocr(self):
        try:
            self.teams.stop_clipboard_monitor()
        except Exception:
            pass

    # ============ CALLBACKS ============

    def _on_loopback_result(self, text: str):
        """
        ⭐ Luồng CHÍNH: Loopback bắt được giọng người khác.
        Người khác nói tiếng Anh → App bắt âm thanh số → STT → Dịch → Caption Việt
        """
        if not text or not text.strip():
            return
        logger.info(f"🔊 Loopback: '{text}'")
        # Qwen LiveTranslate đã trả về tiếng Việt, tránh dịch lần 2 gây câu cụt.
        src_lang = self.translator.detect_language(text)
        if src_lang == "vi":
            result = {
                "source_text": text,
                "target_text": text,
                "source_lang": "vi",
                "display_text": text,
            }
        else:
            result = self.translator.translate_bidirectional(text, direction="en2vi")
        if result.get("display_text"):
            result["display_text"] = self._stabilize_loopback_text(result["display_text"])
            result["target_text"] = result["display_text"]
        if self._status["caption"] and result.get("display_text"):
            self.caption_window.show_caption(result)
            self._append_session_text(result.get("display_text", ""))

    def _stabilize_loopback_text(self, text: str) -> str:
        """Giảm giật/lặp caption khi dùng micro-batch có overlap."""
        current = (text or "").strip()
        if not current:
            return ""
        prev = (self._last_loopback_display or "").strip()
        if not prev:
            self._last_loopback_display = current
            return current
        if current == prev:
            return ""
        if current.startswith(prev):
            self._last_loopback_display = current
            return current
        if prev.startswith(current):
            return ""
        self._last_loopback_display = current
        return current

    def _on_stt_result(self, text: str):
        """
        Micro mode: bắt giọng từ microphone.
        """
        if not text or not text.strip():
            return
        logger.info(f"🎤 Mic: '{text}'")
        result = self.translator.translate_bidirectional(text, direction="auto")
        if self._status["caption"]:
            self.caption_window.show_caption(result)
            self._append_session_text(result.get("display_text", ""))

    def _on_teams_caption(self, text: str):
        """
        OCR mode: đọc Teams live caption từ màn hình.
        """
        if not text or not text.strip() or len(text) < 10:
            return
        logger.info(f"📖 OCR: '{text[:80]}...'")
        result = self.translator.translate_bidirectional(text, direction="en2vi")
        if self._status["caption"]:
            self.caption_window.show_caption(result)
            self._append_session_text(result.get("display_text", ""))

    def _append_session_text(self, text: str):
        clean = (text or "").strip()
        if not clean:
            return
        if self._session_transcript and self._session_transcript[-1] == clean:
            return
        self._session_transcript.append(clean)
        if len(self._session_transcript) > 300:
            self._session_transcript = self._session_transcript[-300:]
        self._maybe_update_summary()

    def _maybe_update_summary(self):
        now = time.time()
        if now - self._last_summary_at < 60:
            return
        if not self._status.get("capturing", False):
            return
        self._last_summary_at = now
        text_blob = "\n".join(self._session_transcript[-80:])
        if len(text_blob) < 80:
            return
        if text_blob == self._last_summarized_snapshot:
            return

        def worker():
            summary = self._ai_helper.summarize_text(text_blob)
            if summary:
                self.caption_window.set_summary(summary)
                self._last_summarized_snapshot = text_blob

        threading.Thread(target=worker, daemon=True, name="Summary-Worker").start()

    # ============ UI ACTIONS ============

    def _toggle_caption(self):
        self._caption_enabled = not self._caption_enabled
        self.act_caption.setChecked(self._caption_enabled)
        self._status["caption"] = self._caption_enabled
        if self._caption_enabled:
            self.caption_window.show()
            self._notify("📺 Caption overlay đã bật")
        else:
            self.caption_window.hide()
            self._notify("📺 Caption overlay đã tắt")

    def _toggle_live_input(self):
        visible = not self.live_input_window.isVisible()
        self.act_live_input.setChecked(visible)
        if visible:
            self.live_input_window.show()
            self._notify("⌨️ Đã hiện ô gõ VN -> EN")
        else:
            self.live_input_window.hide()
            self._notify("⌨️ Đã ẩn ô gõ VN -> EN")

    def _mark_target_input(self):
        try:
            import pyautogui
            x, y = pyautogui.position()
            self.live_input_window.update_target_position(x, y)
            self._notify(f"🎯 Đã đánh dấu input đích tại ({x}, {y})")
        except Exception as e:
            logger.error(f"Lỗi đánh dấu input đích: {e}")
            self._notify("❌ Không đánh dấu được input đích")

    def _show_audio_devices(self):
        """Kiểm tra và hiển thị thiết bị audio."""
        info = self.loopback.get_available_devices_info()
        logger.info(f"\n{info}")
        devices = self.loopback.list_loopback_devices()
        msg = "🔊 Thiết bị audio:\n"
        if devices:
            msg += f"✅ Loopback devices:\n"
            for d in devices:
                msg += f"  - {d['name']}\n"
            msg += "\nLoopback đã sẵn sàng! Không cần loa to."
        else:
            msg += "❌ Không tìm thấy loopback device.\n"
            msg += "→ Cần cài VB-CABLE: https://vb-audio.com/Cable/\n"
            msg += "  Hoặc bật Stereo Mix trong Sound Settings\n\n"
            msg += "Cách bật Stereo Mix:\n"
            msg += "  1. Chuột phải icon loa → Sound settings\n"
            msg += "  2. Sound Control Panel → Recording tab\n"
            msg += "  3. Chuột phải → Show Disabled Devices\n"
            msg += "  4. Enable Stereo Mix\n"

        self.tray.showMessage("Kiểm tra thiết bị", msg, QSystemTrayIcon.MessageIcon.Information, 8000)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            # Fallback nhanh khi menu/submenu khó thao tác ở khu vực system tray.
            self._quit()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Click trái: bung menu ngay vị trí con trỏ để dễ bấm hơn.
            menu = self.tray.contextMenu()
            if menu:
                menu.popup(QCursor.pos())
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._open_settings()

    def _open_settings(self):
        if self._settings_window is None:
            self._settings_window = SettingsWindow(self.config, self)
        self._settings_window.show()
        self._settings_window.raise_()
        self._settings_window.activateWindow()

    def _show_about(self):
        self.tray.showMessage(
            "Về Teams Translator",
            "Phiên bản 1.0.0\n"
            "Dịch real-time Anh → Việt trong Teams meeting\n\n"
            "🔄 Loopback: bắt âm thanh số từ Windows\n"
            "  → Không cần loa to, không cần mic\n"
            "  → Chất lượng STT tốt nhất\n\n"
            "🎤 Micro: dùng mic bắt âm phòng\n"
            "📖 OCR: đọc Teams live caption\n\n"
            "Hotkeys:\n"
            "  Ctrl+Shift+T: Bắt đầu/Dừng\n"
            "  Ctrl+Shift+C: Bật/Tắt caption",
            QSystemTrayIcon.MessageIcon.Information,
            8000
        )

    def _notify(self, message: str):
        self.tray.showMessage("Teams Translator", message, QSystemTrayIcon.MessageIcon.Information, 2000)

    def _quit(self):
        logger.info("Đang thoát...")
        # Cleanup global hotkeys để tránh keyboard hook giữ process nền.
        if self._hotkeys_registered:
            try:
                import keyboard
                keyboard.unhook_all_hotkeys()
                keyboard.unhook_all()
            except Exception as e:
                logger.warning(f"Cleanup hotkeys lỗi: {e}")
            finally:
                self._hotkeys_registered = False

        self._stop_current_capture()
        try:
            self.tray.hide()
        except Exception:
            pass
        try:
            self.floating_controls.close()
        except Exception:
            pass
        try:
            self.live_input_window.close()
        except Exception:
            pass
        self.caption_window.close()
        if self._settings_window:
            self._settings_window.close()
        self.app.quit()

    def start(self):
        """Khởi động app."""
        # Tự động kiểm tra loopback device khi start
        threading.Thread(target=self._auto_check, daemon=True).start()
        logger.info("Teams Translator đã khởi động! Chọn chế độ trong system tray.")
        return self.app.exec()

    def _auto_check(self):
        """Kiểm tra thiết bị khi khởi động."""
        time.sleep(3)
        devices = self.loopback.list_loopback_devices()
        if devices:
            logger.info(f"✅ Loopback sẵn sàng: {[d['name'] for d in devices]}")
        else:
            logger.warning(
                "⚠️ Loopback chưa sẵn sàng.\n"
                "  Cài VB-CABLE: https://vb-audio.com/Cable/\n"
                "  Hoặc bật Stereo Mix"
            )


class SettingsWindow:
    """Cửa sổ cài đặt."""

    def __init__(self, config, app_ref):
        from PyQt5.QtWidgets import (
            QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            QCheckBox, QSlider, QSpinBox, QPushButton, QGroupBox,
            QComboBox, QTabWidget, QFormLayout
        )

        self.config = config
        self.app_ref = app_ref
        self.window = QMainWindow()
        self.window.setWindowTitle("Teams Translator - Cài đặt")
        self.window.setFixedSize(500, 500)
        self.window.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.WindowCloseButtonHint
        )

        central = QWidget()
        self.window.setCentralWidget(central)
        tabs = QTabWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(tabs)

        # Tab: Chung
        gen_tab = QWidget()
        gen_layout = QFormLayout(gen_tab)
        tabs.addTab(gen_tab, "Chung")

        # Tab: Hiển thị
        cap_tab = QWidget()
        cap_layout = QFormLayout(cap_tab)

        self.font_size = QSpinBox()
        self.font_size.setRange(8, 36)
        self.font_size.setValue(config.get("caption_font_size", 14))
        self.font_size.valueChanged.connect(lambda v: config.set("caption_font_size", v))
        cap_layout.addRow("Cỡ chữ:", self.font_size)

        self.opacity = QSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(20, 100)
        self.opacity.setValue(int(config.get("caption_opacity", 0.85) * 100))
        self.opacity.valueChanged.connect(lambda v: config.set("caption_opacity", v / 100))
        cap_layout.addRow("Độ trong suốt:", self.opacity)

        tabs.addTab(cap_tab, "Caption")

        # Tab: Audio
        audio_tab = QWidget()
        audio_layout = QFormLayout(audio_tab)

        self.energy = QSlider(Qt.Orientation.Horizontal)
        self.energy.setRange(100, 1000)
        self.energy.setValue(config.get("stt_energy_threshold", 300))
        self.energy.valueChanged.connect(lambda v: config.set("stt_energy_threshold", v))
        audio_layout.addRow("Độ nhạy microphone:", self.energy)

        tabs.addTab(audio_tab, "Âm thanh")

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_detect = QPushButton("🔊 Kiểm tra thiết bị audio")
        btn_detect.clicked.connect(lambda: self.app_ref._show_audio_devices())
        btn_layout.addWidget(btn_detect)
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.window.close)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

