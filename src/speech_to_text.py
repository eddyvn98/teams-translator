"""
Speech-to-Text module - Nhận dạng giọng nói từ microphone
"""
import logging
import queue
import threading
import time
from typing import Optional, Callable

import numpy as np

from src.qwen_stt import QwenSTT

logger = logging.getLogger(__name__)


class SpeechToText:
    """
    Lắng nghe microphone và chuyển giọng nói thành text.
    Hỗ trợ tiếng Anh và tiếng Việt.
    """

    def __init__(self, config_manager=None):
        self.config = config_manager
        self._recognizer = None
        self._microphone = None
        self._listening = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._text_queue = queue.Queue()
        self._on_result: Optional[Callable[[str], None]] = None
        self._push_to_talk = False
        self._qwen_stt = QwenSTT(config_manager)

    def _get_recognizer(self):
        if self._recognizer is None:
            import speech_recognition as sr
            self._recognizer = sr.Recognizer()
            self._microphone = sr.Microphone()

            if self.config:
                self._recognizer.energy_threshold = self.config.get("stt_energy_threshold", 300)
                self._recognizer.pause_threshold = self.config.get("stt_pause_threshold", 0.8)

            try:
                with self._microphone as source:
                    self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
            except Exception as e:
                logger.warning(f"Không thể calibrate microphone: {e}")

        return self._recognizer

    @property
    def is_listening(self) -> bool:
        return self._listening

    def set_on_result(self, callback: Callable[[str], None]):
        self._on_result = callback

    def start_listening(self, language: str = "vi-VN"):
        if self._listening:
            return

        self._listening = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._listen_loop,
            args=(language,),
            daemon=True,
            name="STT-Listener"
        )
        self._thread.start()
        logger.info(f"Đã bắt đầu lắng nghe (lang={language})")

    def stop_listening(self):
        self._listening = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        logger.info("Đã dừng lắng nghe")

    def _listen_loop(self, language: str):
        recognizer = self._get_recognizer()

        while not self._stop_event.is_set():
            try:
                if self._push_to_talk and not self._is_key_pressed():
                    time.sleep(0.1)
                    continue

                audio = recognizer.listen(
                    self._microphone,
                    timeout=self.config.get("stt_timeout", 5) if self.config else 5,
                    phrase_time_limit=self.config.get("stt_phrase_time_limit", 10) if self.config else 10
                )

                if self._stop_event.is_set():
                    break

                threading.Thread(
                    target=self._recognize_audio,
                    args=(audio, language),
                    daemon=True
                ).start()

            except queue.Empty:
                continue
            except Exception as e:
                if "listening" not in str(e).lower():
                    logger.debug(f"Lỗi listen: {e}")
                time.sleep(0.1)

    def _recognize_audio(self, audio, language: str):
        try:
            audio_pcm = audio.get_raw_data()
            sample_rate = int(audio.sample_rate)
            sample_width = int(audio.sample_width)
            if sample_width != 2:
                raise RuntimeError(f"sample_width không hỗ trợ: {sample_width}")

            pcm_int16 = np.frombuffer(audio_pcm, dtype=np.int16)
            audio_f32 = (pcm_int16.astype(np.float32) / 32768.0).copy()
            lang = "en" if language.lower().startswith("en") else "vi"
            text = self._qwen_stt.transcribe_audio(audio_f32, sample_rate=sample_rate, language=lang)

            if text and text.strip():
                logger.info(f"STT nhận dạng: '{text}'")
                if self._on_result:
                    self._on_result(text)
        except Exception as e:
            logger.debug(f"Không nhận dạng được: {e}")

    def listen_once(self, language: str = "vi-VN", timeout: int = 5) -> Optional[str]:
        recognizer = self._get_recognizer()
        try:
            audio = recognizer.listen(self._microphone, timeout=timeout, phrase_time_limit=10)
            audio_pcm = audio.get_raw_data()
            sample_rate = int(audio.sample_rate)
            sample_width = int(audio.sample_width)
            if sample_width != 2:
                raise RuntimeError(f"sample_width không hỗ trợ: {sample_width}")

            pcm_int16 = np.frombuffer(audio_pcm, dtype=np.int16)
            audio_f32 = (pcm_int16.astype(np.float32) / 32768.0).copy()
            lang = "en" if language.lower().startswith("en") else "vi"
            text = self._qwen_stt.transcribe_audio(audio_f32, sample_rate=sample_rate, language=lang)
            return text
        except Exception as e:
            logger.debug(f"listen_once lỗi: {e}")
            return None

    def set_push_to_talk(self, enabled: bool):
        self._push_to_talk = enabled

    def _is_key_pressed(self) -> bool:
        try:
            import keyboard
            return keyboard.is_pressed('ctrl+shift+m')
        except Exception:
            return True
