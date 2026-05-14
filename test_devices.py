"""Test loopback với device cụ thể - thử từng device một"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import time
import speech_recognition as sr
import sounddevice as sd

# Danh sách device cần thử (theo thứ tự ưu tiên)
test_devices = [
    23,  # Stereo Mix
    21,  # CABLE Output (2ch)
    18,  # Speakers WASAPI loopback
    20,  # Microphone WASAPI loopback
    2,   # CABLE Output (16ch)
]

sample_rate = 16000

print("=== THỬ TỪNG LOOPBACK DEVICE ===")
print(">> HÃY MỞ YOUTUBE TIẾNG ANH VÀ PHÁT TO <<")
print()

for dev_idx in test_devices:
    print(f"📢 Thử device [{dev_idx}]...", end=" ", flush=True)
    try:
        # Kiểm tra device có tồn tại
        device_info = sd.query_devices(dev_idx)
        print(f"{device_info['name']}", end=" ")
        if device_info['max_input_channels'] == 0:
            print("⏭️ (không có input channel)")
            continue
            
        # Test record 3 giây
        recording = sd.rec(
            int(sample_rate * 3),
            samplerate=sample_rate,
            channels=1,
            device=dev_idx,
            dtype='float32',
            blocking=True
        )
        
        max_amp = abs(recording).max()
        
        if max_amp < 0.005:
            print(f"🔇 (tín hiệu: {max_amp:.5f})")
            continue
            
        print(f"🔊 (tín hiệu: {max_amp:.4f}) -> thử STT...", end=" ", flush=True)
        
        # Thử nhận dạng
        audio_int16 = (recording * 32767).astype(np.int16)
        audio_data = sr.AudioData(audio_int16.tobytes(), sample_rate, 2)
        recognizer = sr.Recognizer()
        text = recognizer.recognize_google(audio_data, language="en-US")
        print(f"✅ {text}")
        print(f"\n🎉 DEVICE [{dev_idx}] HOẠT ĐỘNG! Đây là device phù hợp.")
        break
        
    except Exception as e:
        print(f"❌ {e}")
    time.sleep(0.5)
else:
    print("\n❌ Không device nào hoạt động! Kiểm tra VB-CABLE/Stereo Mix và volume.")

print("\n=== KẾT THÚC ===")
