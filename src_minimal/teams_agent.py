"""
Teams Agent — Tương tác với Microsoft Teams
Gõ tin nhắn, copy text, xử lý focus window
"""
import logging
import subprocess
import threading
import time
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class TeamsAgent:
    """
    Tương tác với cửa sổ Microsoft Teams:
    - Focus vào ô chat
    - Gõ text bằng tiếng Anh (khi user nhập tiếng Việt)
    - Đọc caption từ Teams meeting
    """

    def __init__(self, config_manager=None):
        self.config = config_manager
        self._teams_window_title = "Microsoft Teams"
        self._chat_input_focused = False
        self._on_text_received: Optional[Callable[[str], None]] = None
        self._clipboard_monitoring = False

    def set_on_text_received(self, callback: Callable[[str], None]):
        """Callback khi nhận được text từ Teams chat."""
        self._on_text_received = callback

    # ========= WINDOW MANAGEMENT =========

    def find_teams_window(self) -> bool:
        """Tìm và focus vào cửa sổ Teams."""
        try:
            import pyautogui
            # Tìm window có title chứa "Teams"
            windows = pyautogui.getWindowsWithTitle("Teams")
            teams_windows = [w for w in windows if "Microsoft Teams" in w.title or w.title.lower() == "teams"]

            if teams_windows:
                return True
            return False
        except Exception as e:
            logger.warning(f"Lỗi tìm Teams window: {e}")
            return False

    def focus_teams(self):
        """Đưa Teams lên foreground."""
        try:
            windows = pyautogui.getWindowsWithTitle("Teams")
            for w in windows:
                if "Microsoft Teams" in w.title or w.title.lower() == "teams":
                    w.activate()
                    time.sleep(0.3)
                    return True
            return False
        except Exception as e:
            logger.warning(f"Lỗi focus Teams: {e}")
            return False

    def is_teams_focused(self) -> bool:
        """Kiểm tra Teams có đang được focus không."""
        try:
            import pyautogui
            window = pyautogui.getActiveWindow()
            if window and ("Teams" in window.title or "Microsoft Teams" in window.title):
                return True
            return False
        except Exception:
            return False

    # ========= CHAT INPUT =========

    def type_to_chat(self, text: str):
        """
        Gõ text vào ô chat của Teams.
        Dùng pyautogui để type như người dùng thật.
        """
        if not text:
            return

        try:
            import pyautogui
            import keyboard

            # Focus Teams nếu cần
            if not self.is_teams_focused():
                self.focus_teams()
                time.sleep(0.3)

            # Click vào ô chat (Teams có ô chat ở dưới)
            # Try common positions or use keyboard shortcut
            # Cách 1: Click vào vị trí chat box (thường ở bottom của Teams window)
            # Cách 2: Gửi keyboard shortcut Ctrl+Shift+X để focus chat

            # Thử Ctrl+Shift+X (Teams shortcut for chat)
            pyautogui.hotkey('ctrl', 'shift', 'x')
            time.sleep(0.2)

            # Gõ text
            pyautogui.write(text, interval=0.01)

        except Exception as e:
            logger.error(f"Lỗi type to chat: {e}")

    def send_message(self, text: str):
        """
        Gõ text và gửi (Enter).
        Đây là chức năng chính: user gõ tiếng Việt → tự động gửi tiếng Anh.
        """
        if not text:
            return

        delay = self.config.get("auto_send_delay", 0.3) if self.config else 0.3

        try:
            import pyautogui
            import keyboard

            logger.info(f"Gửi tin nhắn: '{text[:80]}...'")

            # Focus Teams
            self.focus_teams()
            time.sleep(0.2)

            # Cách 1: Gửi bằng clipboard (nhanh hơn, tránh lỗi font)
            import pyperclip
            pyperclip.copy(text)
            time.sleep(0.05)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(delay)
            pyautogui.press('enter')

            logger.info(f"Đã gửi tin nhắn thành công")

        except Exception as e:
            logger.error(f"Lỗi send message: {e}")
            # Fallback: type từng chữ
            self._fallback_type(text)

    def _fallback_type(self, text: str):
        """Fallback khi clipboard không hoạt động."""
        try:
            import pyautogui
            pyautogui.write(text, interval=0.005)
            time.sleep(0.2)
            pyautogui.press('enter')
        except Exception as e2:
            logger.error(f"Fallback type cũng lỗi: {e2}")

    # ========= CLIPBOARD MONITOR (đọc nội dung chat) =========

    def start_clipboard_monitor(self):
        """Monitor clipboard để bắt nội dung từ Teams (cần user Ctrl+C)."""
        if self._clipboard_monitoring:
            return

        self._clipboard_monitoring = True
        self._last_clipboard = ""
        thread = threading.Thread(target=self._clipboard_loop, daemon=True)
        thread.start()
        logger.info("Đã bắt đầu monitor clipboard")

    def stop_clipboard_monitor(self):
        self._clipboard_monitoring = False

    def _clipboard_loop(self):
        """Vòng lặp kiểm tra clipboard mỗi 0.5s."""
        try:
            import pyperclip
            while self._clipboard_monitoring:
                try:
                    current = pyperclip.paste()
                    if current and current != self._last_clipboard and len(current) > 5:
                        # Có nội dung mới
                        self._last_clipboard = current
                        if self._on_text_received:
                            self._on_text_received(current)
                except Exception:
                    pass
                time.sleep(0.5)
        except Exception:
            pass

    # ========= LIVE CAPTION — đọc subtitle từ Teams meeting screen =========

    def read_live_caption(self) -> Optional[str]:
        """
        Đọc live caption/subtitle từ Teams meeting.
        
        Cách 1: Teams tích hợp sẵn tính năng "Live Captions"
        → Teams tự động hiển thị phụ đề trên màn hình.
        App chụp màn hình vùng đó và OCR.

        Cách 2: Dùng OCR phần bottom màn hình nơi caption xuất hiện.
        
        Returns: text từ caption, hoặc None nếu không đọc được.
        """
        try:
            import pyautogui
            from PIL import Image

            screenshot = pyautogui.screenshot()
            w, h = screenshot.size

            # Live captions của Teams thường xuất hiện ở bottom 20%
            # Teams có thể overlay caption ở bottom-center
            caption_area = screenshot.crop((
                int(w * 0.05),    # left: 5%
                int(h * 0.70),    # top: 70% (bottom 30% of screen)
                int(w * 0.95),    # right: 95%
                int(h * 0.95)     # bottom: leave taskbar
            ))
            caption_area.save("resources/caption_screenshot.png")

            # OCR
            try:
                import pytesseract
                text = pytesseract.image_to_string(
                    "resources/caption_screenshot.png",
                    lang='eng+vie',
                    config='--psm 7 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-\'":;'
                )
                cleaned = text.strip()
                # Lọc noise: caption thường là 1-2 dòng
                lines = [l.strip() for l in cleaned.split('\n') if l.strip()]
                if lines:
                    return ' '.join(lines)
                return None
            except ImportError:
                logger.warning("Chưa cài pytesseract. Cài: pip install pytesseract && winget install TesseractOCR")
                return None

        except Exception as e:
            logger.error(f"Lỗi đọc live caption: {e}")
            return None

    def start_live_caption_monitor(self, interval: float = 2.0):
        """
        Monitor live caption từ Teams meeting định kỳ.
        Cứ mỗi `interval` giây, đọc caption mới và gửi callback.
        """
        if self._clipboard_monitoring:
            return

        self._clipboard_monitoring = True
        self._last_caption = ""

        def _monitor():
            while self._clipboard_monitoring:
                try:
                    text = self.read_live_caption()
                    if text and text != self._last_caption and len(text) > 5:
                        self._last_caption = text
                        if self._on_text_received:
                            self._on_text_received(text)
                except Exception:
                    pass
                time.sleep(interval)

        thread = threading.Thread(target=_monitor, daemon=True)
        thread.start()
        logger.info(f"Đã bắt đầu monitor live caption (interval={interval}s)")

    # ========= WINDOWS OCR SETUP HELPER =========

    def check_tesseract_installed(self) -> bool:
        """Kiểm tra Tesseract OCR đã cài trên máy chưa."""
        try:
            import pytesseract
            # Thử gọi version
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract OK: {version}")
            return True
        except ImportError:
            logger.warning("pytesseract chưa cài. pip install pytesseract")
            return False
        except Exception as e:
            logger.warning(f"Tesseract chưa cài hoặc không trong PATH: {e}")
            return False
