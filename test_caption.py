"""Test Caption Window UI - hiển thị text thử"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

from PyQt5.QtWidgets import QApplication
from src.caption_window import CaptionWindow

app = QApplication(sys.argv)

# Tạo caption window
win = CaptionWindow(config_manager=None)

# Hiển thị text mẫu
win.show_caption({
    "source_text": "The defense secretary has defended the cost of the war",
    "target_text": "Bộ trưởng Quốc phòng đã bảo vệ chi phí cuộc chiến",
    "source_lang": "en"
})

win.resize(700, 200)
win.show()
win.raise_()

print("🪟 Đã mở caption window với text mẫu!")
print(">>> NHÌN LÊN MÀN HÌNH - có thấy ô caption đen viền xanh không?")
print(">>> Ấn Esc để đóng, hoặc đợi 15 giây tự đóng.")

QApplication.processEvents()
time.sleep(15)

win.hide()
print("Đã đóng.")
