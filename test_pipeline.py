#!/usr/bin/env python3
"""
Test pipeline: Loopback → faster-whisper → Dịch → In kết quả
"""
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.local_stt import transcribe, _get_model
from src.translator import Translator
from src.config_manager import ConfigManager
import sounddevice as sd
import numpy as np
from scipy import signal

# === Config ===
SAMPLE_RATE = 44100
TARGET_SR = 16000
CHUNK_S = 3
NUM_TESTS = 5
LOOPBACK_KEYWORDS = ["cable output (vb-audio virtual", "cable output", "cable input"]

# === Find loopback device ===
import pyaudio
p = pyaudio.PyAudio()
target_device = None
target_name = ""
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    name = info["name"].lower()
    if any(kw in name for kw in LOOPBACK_KEYWORDS) and info["maxInputChannels"] >= 2:
        target_device = i
        target_name = info["name"]
        break
p.terminate()

if target_device is None:
    print("❌ Không tìm thấy CABLE Output! Kiểm tra VB-CABLE đã cài chưa.")
    sys.exit(1)

# === Load model ===
print("⏳ Đang tải faster-whisper model...")
t0 = time.time()
model = _get_model("tiny.en", device="auto", compute_type="int8")
t1 = time.time()
print(f"✅ Model loaded in {t1-t0:.1f}s (device: {model.model.device})")
print(f"🎯 Loopback: [{target_device}] {target_name}")
print()

config = ConfigManager()
translator = Translator(config)

print(f"🎤 Test: ghi {CHUNK_S}s loopback x {NUM_TESTS} lần")
print("   Mở YouTube/video tiếng Anh trong lúc test...")
print()

for i in range(NUM_TESTS):
    print(f"--- Test {i+1}/{NUM_TESTS} ---")

    # Capture 3s từ loopback
    t_cap_start = time.time()
    recording = sd.rec(
        int(SAMPLE_RATE * CHUNK_S),
        samplerate=SAMPLE_RATE,
        channels=1,
        device=target_device,
        dtype="float32",
    )
    sd.wait()
    audio = recording.flatten()
    t_cap_end = time.time()

    # VAD check
    rms = np.sqrt(np.mean(audio ** 2))
    if rms < 0.003:
        print(f"   🔇 Im lặng (RMS={rms:.5f}) — bỏ qua")
        print()
        continue

    # Resample 44100 → 16000
    ratio = TARGET_SR / SAMPLE_RATE
    new_len = int(len(audio) * ratio)
    audio_resampled = signal.resample(audio, new_len).astype(np.float32)
    t_res_end = time.time()

    # faster-whisper
    t_stt_start = time.time()
    text = transcribe(audio_resampled, sample_rate=TARGET_SR, language="en")
    t_stt_end = time.time()

    if text:
        # Dịch
        t_tl_start = time.time()
        translated = translator.translate_bidirectional(text, direction="en2vi")
        t_tl_end = time.time()

        total_ms = (t_stt_end - t_cap_start) * 1000
        print(f'   🎤 English: "{text}"')
        print(f'   🇻🇳 Việt:    "{translated}"')
        print(f"   ⏱  STT={t_stt_end-t_stt_start:.2f}s | Dịch={t_tl_end-t_tl_start:.2f}s")
        print(f"      Capture={t_cap_end-t_cap_start:.2f}s | Resample={t_res_end-t_cap_end:.2f}s")
        print(f"      ⏱  TỔNG (capture→dịch xong): {total_ms:.0f}ms")
    else:
        print(f"   🤷 Không nhận dạng được (RMS={rms:.5f})")

    print()
