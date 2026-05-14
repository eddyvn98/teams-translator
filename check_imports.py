import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("PyQt5...", end=" ")
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon
print("OK")

print("faster-whisper...", end=" ")
from faster_whisper import WhisperModel
print("OK")

print("sounddevice...", end=" ")
import sounddevice as sd
print("OK")

print("deep-translator...", end=" ")
from deep_translator import GoogleTranslator
print("OK")

print("local_stt...", end=" ")
from src.local_stt import transcribe, _get_model
print("OK")

print("\n✅ All imports OK")
