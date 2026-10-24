"""Text-to-speech backends for meeting replies."""

import base64
import logging
import os
import re
import tempfile
import threading
import time
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

    def play_wav_bytes(self, wav_bytes: bytes, wait: bool = False):
        """Play audio bytes (WAV/PCM) directly via the configured output device."""
        if not wav_bytes:
            return

        def _do_play():
            with self._lock:
                try:
                    self._speaking = True
                    fd, path = tempfile.mkstemp(prefix="teams-translator-remote-", suffix=".wav")
                    try:
                        with os.fdopen(fd, "wb") as audio_file:
                            audio_file.write(wav_bytes)
                        self._play_wav(path)
                    finally:
                        try:
                            os.remove(path)
                        except OSError:
                            pass
                    if self._on_done:
                        self._on_done()
                except Exception as exc:
                    logger.error("Failed to play remote audio bytes: %s", exc)
                finally:
                    self._speaking = False

        if wait:
            _do_play()
        else:
            threading.Thread(target=_do_play, daemon=True, name="AudioBytes-Play-Thread").start()

    def _config_value(self, key: str, default=None):
        return self.config.get(key, default) if self.config else default

    def _api_key(self) -> str:
        key = os.getenv("DASHSCOPE_API_KEY", "").strip() or os.getenv("QWEN_API_KEY", "").strip()
        if not key and self.config:
            key = str(self.config.get("qwen_api_key", "")).strip()
        return key

    def _speak_qwen(self, text: str):
        model = str(self._config_value("qwen_tts_model", "qwen3-tts-flash-realtime")).strip()
        if "realtime" in model:
            try:
                self._speak_qwen_realtime(text, model=model)
                return
            except Exception as exc:
                logger.warning("Qwen realtime TTS failed, falling back to REST TTS: %s", exc)
                fallback_model = str(self._config_value("qwen_tts_rest_fallback_model", "qwen3-tts-flash")).strip()
                self._speak_qwen_rest(text, model=fallback_model)
                return
        self._speak_qwen_rest(text, model=model)

    def _speak_qwen_realtime(self, text: str, model: str):
        key = self._api_key()
        if not key:
            raise RuntimeError("Missing Qwen/DashScope API key")

        import dashscope
        import sounddevice as sd
        from dashscope.audio.qwen_tts_realtime import (
            AudioFormat,
            QwenTtsRealtime,
            QwenTtsRealtimeCallback,
        )

        dashscope.api_key = key
        url = str(self._config_value("qwen_tts_realtime_url", "wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime")).strip()
        voice = str(self._config_value("qwen_tts_realtime_voice", self._config_value("qwen_tts_voice", "Cherry"))).strip()
        wait_timeout = float(self._config_value("qwen_tts_wait_timeout", 30) or 30)
        device = self._find_output_device(sd)
        stream = sd.RawOutputStream(
            samplerate=24000,
            channels=1,
            dtype="int16",
            device=device,
            blocksize=0,
        )

        class RealtimeCallback(QwenTtsRealtimeCallback):
            def __init__(self):
                super().__init__()
                self.complete_event = threading.Event()
                self.error = None

            def on_event(self, response):
                try:
                    event_type = response.get("type") if isinstance(response, dict) else None
                    if event_type == "response.audio.delta":
                        chunk = base64.b64decode(response.get("delta") or "")
                        if chunk:
                            stream.write(chunk)
                    elif event_type in ("response.done", "session.finished"):
                        self.complete_event.set()
                except Exception as exc:
                    self.error = exc
                    self.complete_event.set()

            def on_close(self, close_status_code, close_msg) -> None:
                self.complete_event.set()

        callback = RealtimeCallback()
        qwen_tts = QwenTtsRealtime(model=model, callback=callback, url=url)
        try:
            logger.info("[TTS] backend=qwen-realtime model=%s voice=%s", model, voice)
            stream.start()
            qwen_tts.connect()
            qwen_tts.update_session(
                voice=voice,
                response_format=AudioFormat.PCM_24000HZ_MONO_16BIT,
                mode="server_commit",
            )
            for chunk in self._text_chunks(text):
                qwen_tts.append_text(chunk)
                time.sleep(0.03)
            qwen_tts.finish()
            callback.complete_event.wait(timeout=wait_timeout)
            if callback.error:
                raise callback.error
        finally:
            try:
                qwen_tts.close()
            except Exception:
                pass
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass

    def _text_chunks(self, text: str) -> list[str]:
        chunks = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]
        return chunks or [text.strip()]

    def _speak_qwen_rest(self, text: str, model: str):
        key = self._api_key()
        if not key:
            raise RuntimeError("Missing Qwen/DashScope API key")

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

        audio_orig, sample_rate_orig = sf.read(path, dtype="float32", always_2d=True)
        primary_dev, monitor_dev = self._find_output_devices(sd)

        def _play_on_device(dev_index):
            if dev_index is None:
                return
            dev_info = sd.query_devices(dev_index)
            target_rate = int(dev_info.get("default_samplerate") or sample_rate_orig)
            channels = min(2, int(dev_info.get("max_output_channels") or audio_orig.shape[1] or 1))
            cur_audio = audio_orig
            cur_rate = sample_rate_orig
            if cur_rate != target_rate:
                target_len = int(round(len(cur_audio) * target_rate / cur_rate))
                cur_audio = signal.resample(cur_audio, target_len, axis=0).astype("float32")
                cur_rate = target_rate
            if cur_audio.shape[1] < channels:
                cur_audio = np.repeat(cur_audio, channels, axis=1)
            elif cur_audio.shape[1] > channels:
                cur_audio = cur_audio[:, :channels]
            logger.info("Playing TTS audio to device=%s (%s) sample_rate=%s frames=%s", dev_index, dev_info["name"], cur_rate, len(cur_audio))
            try:
                with sd.OutputStream(device=dev_index, samplerate=cur_rate, channels=channels, dtype="float32") as stream:
                    stream.write(cur_audio)
            except Exception as err:
                logger.warning("OutputStream playback failed on dev %s, falling back to sd.play: %s", dev_index, err)
                sd.play(cur_audio, cur_rate, device=dev_index, blocking=True)

        if monitor_dev is not None and monitor_dev != primary_dev:
            # Play concurrently on both virtual cable (Teams) and monitor speaker (User)
            t_mon = threading.Thread(target=_play_on_device, args=(monitor_dev,), daemon=True, name="TTS-Monitor-Play")
            t_mon.start()
            _play_on_device(primary_dev)
            duration_sec = len(audio_orig) / max(1, sample_rate_orig)
            t_mon.join(timeout=max(5.0, duration_sec + 3.0))
        else:
            _play_on_device(primary_dev)

    def _find_output_devices(self, sd):
        """
        Find primary output device (virtual cable for Teams)
        and optional monitor output device (physical speaker/headphones for user).
        """
        preferred = str(self._config_value("qwen_tts_output_device", "")).strip().lower()
        virtual_keywords = ["blackhole", "cable input", "vb-audio", "virtual", "soundflower", "loopback"]

        virtual_dev = None
        physical_dev = None
        default_dev = None

        for index, device in enumerate(sd.query_devices()):
            if int(device.get("max_output_channels") or 0) <= 0:
                continue
            name = str(device.get("name") or "").lower()

            if default_dev is None:
                default_dev = index

            # Check if user explicitly configured preferred device
            if preferred and preferred in name:
                virtual_dev = index
                continue

            # Check if it is a virtual audio device
            if any(kw in name for kw in virtual_keywords):
                if virtual_dev is None:
                    virtual_dev = index
            else:
                # Prioritize headphones or built-in speakers for physical monitor
                if physical_dev is None:
                    physical_dev = index
                elif any(kw in name for kw in ["headphone", "headset", "airpod", "loa macbook", "speakers"]):
                    physical_dev = index

        if virtual_dev is not None:
            monitor = physical_dev if physical_dev is not None else default_dev
            return virtual_dev, monitor

        target = physical_dev if physical_dev is not None else default_dev
        return target, None

    def _find_output_device(self, sd):
        primary, _ = self._find_output_devices(sd)
        return primary

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
            voice_choice = str(self.config.get("tts_voice", "english")).strip().lower()
            
            # Helper to find a specific voice by keyword
            def set_voice_by_keyword(keyword):
                for voice in voices:
                    if keyword in voice.name.lower() or keyword in voice.id.lower():
                        engine.setProperty("voice", voice.id)
                        logger.info("Selected pyttsx3 voice: %s", voice.name)
                        return True
                return False

            if "david" in voice_choice:
                # Force male voice (David)
                if not set_voice_by_keyword("david"):
                    set_voice_by_keyword("english")
            elif "zira" in voice_choice:
                # Force female voice (Zira)
                if not set_voice_by_keyword("zira"):
                    set_voice_by_keyword("english")
            elif voice_choice == "english":
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
