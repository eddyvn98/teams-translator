"""
Config Manager — quản lý cấu hình và cài đặt
"""
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv(Path.cwd() / ".env")

CONFIG_DIR = Path.home() / ".teams-translator"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    # Translation
    "source_lang": "auto",
    "target_lang_vi": "vi",
    "target_lang_en": "en",
    "translation_google_timeout": 1.8,
    "translation_qwen_timeout": 4.0,
    "translation_cache_size": 256,

    # Qwen STT
    "qwen_base_url": "https://dich.vivutrade.io.vn/v1",
    "qwen_stt_model": "iic/SenseVoiceSmall",
    "qwen_mt_model": "qwen-mt-flash",
    "qwen_api_key": "",
    "loopback_stt_mode": "realtime",
    "loopback_realtime_frame_ms": 100,
    "loopback_realtime_sample_rate": 16000,
    "loopback_partial_translate_min_chars": 8,
    "loopback_partial_translate_interval_ms": 350,

    # Speech
    "stt_energy_threshold": 300,
    "stt_pause_threshold": 0.8,
    "stt_timeout": 5,
    "stt_phrase_time_limit": 10,

    # TTS
    "tts_backend": "pyttsx3",  # qwen / pyttsx3
    "tts_rate": 180,
    "tts_volume": 1.0,
    "tts_voice": "english",  # english / vietnamese
    "qwen_tts_model": "qwen3-tts-flash-realtime",
    "qwen_tts_rest_fallback_model": "qwen3-tts-flash",
    "qwen_tts_voice": "Nofish",
    "qwen_tts_realtime_voice": "Ethan",
    "qwen_tts_language_type": "English",
    "qwen_tts_realtime_url": "wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime",
    "qwen_tts_wait_timeout": 30,
    "qwen_tts_output_device": "CABLE Input",
    "qwen_tts_output_host": "MME",

    # Translation direction
    # "auto" = auto-detect input language
    # "en2vi" = always English → Vietnamese
    # "vi2en" = always Vietnamese → English
    "direction": "auto",

    # Caption window
    "caption_opacity": 0.85,
    "caption_font_size": 14,
    "caption_width": 600,
    "caption_height": 250,
    "caption_x": None,  # None = center
    "caption_y": None,

    # Auto-send
    "auto_send_enabled": True,
    "auto_send_delay": 0.3,  # seconds between typing + Enter

    # Features
    "stt_enabled": True,
    "tts_enabled": True,
    "caption_enabled": True,
    "auto_type_enabled": True,

    # Hotkeys
    "hotkey_toggle": "ctrl+shift+t",
    "hotkey_push_to_talk": "ctrl+shift+m",
    "hotkey_toggle_caption": "ctrl+shift+c",
}


class ConfigManager:
    def __init__(self):
        self.config = {}
        self._load()

    def _load(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8-sig") as f:
                    loaded = json.load(f)
                
                # Migrate old Qwen values to new ASR server settings if they exist
                if loaded.get("qwen_base_url") == "https://dashscope-intl.aliyuncs.com/compatible-mode/v1":
                    loaded["qwen_base_url"] = DEFAULT_CONFIG["qwen_base_url"]
                if loaded.get("qwen_stt_model") == "qwen3-asr-flash-realtime":
                    loaded["qwen_stt_model"] = DEFAULT_CONFIG["qwen_stt_model"]
                if loaded.get("tts_backend") == "qwen":
                    loaded["tts_backend"] = DEFAULT_CONFIG["tts_backend"]

                # Merge with defaults (keep user values, fill missing)
                self.config = {**DEFAULT_CONFIG, **loaded}
                self._save()
            except Exception:
                self.config = dict(DEFAULT_CONFIG)
        else:
            self.config = dict(DEFAULT_CONFIG)
            self._save()

    def _save(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self._save()

    def get_all(self):
        return dict(self.config)

    def reset(self):
        self.config = dict(DEFAULT_CONFIG)
        self._save()

