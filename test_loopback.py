"""Test: bắt âm thanh loopback 5 giây và nhận dạng speech-to-text"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.loopback_capture import LoopbackCapture
import time

# Bước 1: Liệt kê loopback devices
print("=== KIỂM TRA LOOPBACK DEVICE ===")
capture = LoopbackCapture()
devices = capture.list_loopback_devices()
if devices:
    print(f"✅ Tìm thấy {len(devices)} loopback device(s):")
    for d in devices:
        print(f"   - [{d['index']}] {d['name']} ({d['channels']} channels)")
    
    # Chọn device tốt nhất
    best = capture.find_best_loopback_device()
    print(f"\n🔊 Device được chọn: index {best}")
else:
    print("❌ KHÔNG tìm thấy loopback device nào!")
    sys.exit(1)

# Bước 2: Thử bắt âm thanh 5 giây
print("\n=== BẮT ÂM THANH LOOPBACK 5 GIÂY ===")
print(">>> HÃY MỞ YOUTUBE TIẾNG ANH VÀ PHÁT ÂM THANH <<<")
print(">>> Bắt đầu sau 3 giây...")
time.sleep(3)

result = capture.capture_once(duration=5)
print(f">>> Kết quả: {result}")
if result and "error" not in result.lower():
    print("✅ Đã nhận dạng được giọng nói!")
    print(f"   Text: {result}")
else:
    print("⚠️ Không nhận dạng được hoặc không có âm thanh.")
    print("   Kiểm tra: YouTube có đang phát không? Volume có đủ không?")

print("\n=== KẾT THÚC TEST ===")
