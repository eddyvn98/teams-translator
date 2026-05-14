"""
Config Manager — quản lý cấu hình và cài đặt
"""
import json
import os
from pathlib import Path


CONFIG_DIR = Path.home() / ".teams-translator"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    # Translation
    "source_lang": "auto",
    "target_lang_vi": "vi",
    "target_lang_en": "en",

    # Qwen STT
    "qwen_base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    "qwen_stt_model": "qwen3-livetranslate-flash",
    "qwen_api_key": "",

    # Speech
    "stt_energy_threshold": 300,
    "stt_pause_threshold": 0.8,
    "stt_timeout": 5,
    "stt_phrase_time_limit": 10,

    # TTS
    "tts_rate": 180,
    "tts_volume": 1.0,
    "tts_voice": "english",  # english / vietnamese

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
                # Merge with defaults (keep user values, fill missing)
                self.config = {**DEFAULT_CONFIG, **loaded}
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

