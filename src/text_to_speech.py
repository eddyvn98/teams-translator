"""Text-to-speech backends for meeting replies."""

import base64
import logging
import os
import tempfile
import threading
from typing import Callable, Optional

import requests

logger = logging.getLogger(__name__)


class TextToSpeech:
    """Speak English replies using Qwen TTS, with pyttsx3 as fallback."""

    def __init__(self, config_manager=None):
        self.config = config_manager
        self._speaking = False
        self._lock = threading.Lock()
        self._on_done: Optional[Callable] = None

    def speak(self, text: str, wait: bool = False):
        """Speak text in a worker thread so the PyQt UI stays responsive."""
        if not text or not text.strip():
            return

        def _do_speak():
            with self._lock:
                try:
                    self._speaking = True
                    backend = str(self._config_value("tts_backend", "qwen")).strip().lower()
                    if backend == "qwen":
                        try:
                            self._speak_qwen(text)
                        except Exception as exc:
                            logger.warning("Qwen TTS failed, falling back to pyttsx3: %s", exc)
                            self._speak_pyttsx3(text)
                    else:
                        self._speak_pyttsx3(text)

                    if self._on_done:
                        self._on_done()
                except Exception as exc:
                    logger.error("TTS error: %s", exc)
                finally:
                    self._speaking = False

        if wait:
            _do_speak()
        else:
            threading.Thread(target=_do_speak, daemon=True, name="TTS-Thread").start()

    def _config_value(self, key: str, default=None):
        return self.config.get(key, default) if self.config else default

    def _api_key(self) -> str:
        key = os.getenv("DASHSCOPE_API_KEY", "").strip() or os.getenv("QWEN_API_KEY", "").strip()
        if not key and self.config:
            key = str(self.config.get("qwen_api_key", "")).strip()
        return key

    def _speak_qwen(self, text: str):
        key = self._api_key()
        if not key:
            raise RuntimeError("Missing Qwen/DashScope API key")

        model = str(self._config_value("qwen_tts_model", "qwen3-tts-flash")).strip()
        voice = str(self._config_value("qwen_tts_voice", "Nofish")).strip()
        language_type = str(self._config_value("qwen_tts_language_type", "English")).strip()
        url = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
        payload = {
            "model": model,
            "input": {
                "text": text.strip(),
                "voice": voice,
                "language_type": language_type,
            },
        }
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=payload,
            timeout=90,
        )
        if response.status_code >= 400:
            raise RuntimeError(response.text[:500])

        data = response.json()
        audio = ((data.get("output") or {}).get("audio") or {})
        wav_bytes = b""
        if audio.get("data"):
            wav_bytes = base64.b64decode(audio["data"])
        elif audio.get("url"):
            audio_response = requests.get(audio["url"], timeout=90)
            if audio_response.status_code >= 400:
                raise RuntimeError(f"Audio download failed: {audio_response.status_code}")
            wav_bytes = audio_response.content

        if not wav_bytes:
            raise RuntimeError("Qwen TTS returned no audio")

        fd, path = tempfile.mkstemp(prefix="teams-translator-qwen-", suffix=".wav")
        try:
            with os.fdopen(fd, "wb") as audio_file:
                audio_file.write(wav_bytes)
            self._play_wav(path)
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

    def _play_wav(self, path: str):
        import numpy as np
        from scipy import signal
        import sounddevice as sd
        import soundfile as sf

        audio, sample_rate = sf.read(path, dtype="float32", always_2d=True)
        device = self._find_output_device(sd)
        device_info = sd.query_devices(device)
        target_rate = int(device_info.get("default_samplerate") or sample_rate)
        channels = min(2, int(device_info.get("max_output_channels") or audio.shape[1] or 1))
        if sample_rate != target_rate:
            target_len = int(round(len(audio) * target_rate / sample_rate))
            audio = signal.resample(audio, target_len, axis=0).astype("float32")
            sample_rate = target_rate
        if audio.shape[1] < channels:
            audio = np.repeat(audio, channels, axis=1)
        elif audio.shape[1] > channels:
            audio = audio[:, :channels]
        logger.info("Playing TTS audio to device=%s sample_rate=%s frames=%s", device, sample_rate, len(audio))
        sd.play(audio, sample_rate, device=device, blocking=True)

    def _find_output_device(self, sd):
        preferred = str(self._config_value("qwen_tts_output_device", "CABLE Input")).strip().lower()
        preferred_host = str(self._config_value("qwen_tts_output_host", "MME")).strip().lower()
        fallback = None
        for index, device in enumerate(sd.query_devices()):
            if int(device.get("max_output_channels") or 0) <= 0:
                continue
            host = sd.query_hostapis(device["hostapi"])["name"].lower()
            name = str(device.get("name") or "").lower()
            if fallback is None:
                fallback = index
            if preferred and preferred in name:
                if preferred_host and preferred_host in host:
                    return index
                fallback = index
        return fallback

    def _speak_pyttsx3(self, text: str):
        engine = None
        try:
            import pyttsx3

            engine = pyttsx3.init()
            self._apply_pyttsx3_config(engine)
            engine.say(text)
            engine.runAndWait()
        finally:
            if engine:
                try:
                    engine.stop()
                    del engine
                except Exception:
                    pass

    def _apply_pyttsx3_config(self, engine):
        if not engine or not self.config:
            return

        try:
            rate = self.config.get("tts_rate", 180)
            volume = self.config.get("tts_volume", 1.0)
            engine.setProperty("rate", rate)
            engine.setProperty("volume", volume)

            voices = engine.getProperty("voices")
            voice_choice = self.config.get("tts_voice", "english")
            if voice_choice == "english":
                for voice in voices:
                    voice_name = voice.name.lower()
                    voice_id = voice.id.lower()
                    if "english" in voice_name or "en_" in voice_id or "david" in voice_name or "zira" in voice_name:
                        engine.setProperty("voice", voice.id)
                        logger.info("Selected pyttsx3 voice: %s", voice.name)
                        break
            else:
                for voice in voices:
                    if "vietnamese" in voice.name.lower() or "vi_" in voice.id.lower():
                        engine.setProperty("voice", voice.id)
                        break
        except Exception as exc:
            logger.warning("pyttsx3 config error: %s", exc)

    def stop(self):
        self._speaking = False

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    def set_on_done(self, callback: Callable):
        self._on_done = callback
