"""Test: kiểm tra mức tín hiệu loopback + thử STT với ngưỡng dynamic"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import sounddevice as sd
import speech_recognition as sr
import time

device_idx = 2  # CABLE Output
sample_rate = 16000

print("=== KIỂM TRA MỨC ÂM THANH LOOPBACK ===")
print("🔊 Device: CABLE Output (VB-Audio)")
print(">>> HÃY ĐẢM BẢO YOUTUBE ĐANG PHÁT TIẾNG ANH <<<")
print()

# Test 1: Ghi 3 giây kiểm tra level
print("📊 Test 1: Ghi 3 giây để đo mức âm thanh...")
recording = sd.rec(int(sample_rate * 3), samplerate=sample_rate, channels=1, device=device_idx, dtype='float32')
sd.wait()
max_amp = abs(recording).max()
mean_amp = abs(recording).mean()
print(f"   Max amplitude: {max_amp:.6f}")
print(f"   Mean amplitude: {mean_amp:.6f}")

if max_amp < 0.005:
    print("   ❌ Tín hiệu RẤT YẾU hoặc KHÔNG CÓ!")
    print("   Kiểm tra: Windows Sound Settings → Output có phải 'CABLE Input' không?")
    print("   Volume output có đủ to không?")
elif max_amp < 0.05:
    print("   ⚠️ Tín hiệu yếu, có thể cần tăng volume")
else:
    print("   ✅ Tín hiệu tốt!")

# Test 2: Thử 5 giây + STT
print(f"\n📊 Test 2: Ghi 5 giây + Google STT...")
recording2 = sd.rec(int(sample_rate * 5), samplerate=sample_rate, channels=1, device=device_idx, dtype='float32')
sd.wait()

max_amp2 = abs(recording2).max()
mean_amp2 = abs(recording2).mean()
print(f"   Max amplitude: {max_amp2:.6f}")
print(f"   Mean amplitude: {mean_amp2:.6f}")

if max_amp2 > 0.02:
    audio_int16 = (recording2 * 32767).astype(np.int16)
    audio_data = sr.AudioData(audio_int16.tobytes(), sample_rate, 2)
    recognizer = sr.Recognizer()
    try:
        text = recognizer.recognize_google(audio_data, language="en-US")
        print(f"   ✅ STT thành công: \"{text}\"")
    except sr.UnknownValueError:
        print("   ❌ Google STT: không nhận dạng được (có thể không phải giọng nói)")
    except sr.RequestError as e:
        print(f"   ❌ Lỗi kết nối Google STT: {e}")
else:
    print("   ⏭️ Bỏ qua STT vì tín hiệu quá yếu")

# Test 3: Ghi 10 giây dài hơn 
print(f"\n📊 Test 3: Ghi 10 giây + STT (cơ hội cao hơn)...")
recording3 = sd.rec(int(sample_rate * 10), samplerate=sample_rate, channels=1, device=device_idx, dtype='float32')
sd.wait()

max_amp3 = abs(recording3).max()
if max_amp3 > 0.02:
    audio_int16 = (recording3 * 32767).astype(np.int16)
    audio_data = sr.AudioData(audio_int16.tobytes(), sample_rate, 2)
    try:
        text = recognizer.recognize_google(audio_data, language="en-US")
        print(f"   ✅ STT thành công (10s): \"{text}\"")
    except sr.UnknownValueError:
        print("   ❌ Google STT (10s): không nhận dạng được")
else:
    print(f"   ⏭️ Bỏ qua STT - tín hiệu quá yếu (max={max_amp3:.6f})")

print("\n=== KẾT THÚC TEST ===")
