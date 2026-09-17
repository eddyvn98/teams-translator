import time
import numpy as np
from src_minimal.config_manager import ConfigManager
from src_minimal.qwen_realtime_stt import QwenRealtimeSTT

cfg = ConfigManager()
results = []
def on_text(text, is_final):
    print(f'CALLBACK: text="{text}", is_final={is_final}')
    results.append((text, is_final))

stt = QwenRealtimeSTT(cfg, on_text_received=on_text)
stt.start(sample_rate=16000)

# Send 2 seconds of silence
silence = np.zeros(32000, dtype=np.int16).tobytes()
stt.send_audio(silence)
time.sleep(1.5)
stt.stop()
print("Done. Results count:", len(results))
