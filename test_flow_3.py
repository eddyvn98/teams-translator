"""Test Loopback → STT → Dịch 3 lần, mỗi lần 7 giây"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

from src.loopback_capture import LoopbackCapture
from src.translator import Translator

capture = LoopbackCapture()
translator = Translator()
device = capture.find_best_loopback_device()
print(f"🔊 Device: [{device}]")

for i in range(3):
    print(f"\n{'='*40}")
    print(f"  🎤 Lần {i+1}/3: Ghi 7 giây...")
    print(f"{'='*40}")
    
    result = capture.capture_once(duration=7)
    
    if result:
        print(f"  ✅ English: {result}")
        try:
            translated = translator.translate(result, source_lang="en", target_lang="vi")
            print(f"  🌐 Tiếng Việt: {translated}")
        except Exception as e:
            print(f"  ❌ Lỗi dịch: {e}")
    else:
        print(f"  ⚠️ Không nhận dạng được")
        print(f"  (Có thể âm thanh chưa qua VB-CABLE, hoặc volume nhỏ)")
    
    if i < 2:
        print(f"  ⏳ Chờ 2 giây...")
        time.sleep(2)

print(f"\n{'='*40}")
print("  ✅ KẾT THÚC TEST")
print(f"{'='*40}")
