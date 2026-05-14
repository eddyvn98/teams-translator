"""Test full flow: Loopback → STT → Dịch → Caption
Chạy độc lập để test nhanh, mở caption overlay thực tế"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

from src.loopback_capture import LoopbackCapture
from src.translator import Translator
from src.caption_window import CaptionWindow
from src.config_manager import ConfigManager
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import signal
import threading

app = QApplication(sys.argv)
config = ConfigManager()

# Khởi tạo caption window
caption = CaptionWindow(config_manager=config)
caption.setWindowTitle("Teams Translator - TEST")
caption.show()

# Khởi tạo translator
translator = Translator(config_manager=config)

# Khởi tạo loopback capture
capture = LoopbackCapture(config_manager=config)

# Callback: nhận text từ loopback → dịch → hiển thị
def on_speech(text):
    print(f"\n🎤 STT: {text}")
    try:
        translated = translator.translate(text, source_lang="en", target_lang="vi")
        print(f"🌐 Việt: {translated}")
        caption.show_caption({
            "source_text": text,
            "target_text": translated,
            "source_lang": "en"
        })
    except Exception as e:
        print(f"❌ Lỗi dịch: {e}")

capture.set_on_result(on_speech)

# Bắt đầu capture
capture.start_capture()

print("=" * 50)
print("  🔴 APP ĐANG CHẠY TEST LOOPBACK + CAPTION")
print("  Bạn đang nghe YouTube tiếng Anh?")
print("  Caption overlay sẽ hiện trên màn hình!")
print("  Đóng cửa sổ này để dừng.")
print("=" * 50)

# Timer để kiểm tra
def check_status():
    status = "🟢" if capture.is_capturing else "🔴"
    print(f"  {status} Capturing: {capture.is_capturing}", end="\r", flush=True)

timer = QTimer()
timer.timeout.connect(check_status)
timer.start(5000)

# Xử lý Ctrl+C
signal.signal(signal.SIGINT, lambda s, f: app.quit())

sys.exit(app.exec())
