"""
Speech-to-Text module - Nhận dạng giọng nói từ microphone.
Được tối ưu hóa cho Micro-Batching REST ASR với độ trễ cực thấp.
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
    Sử dụng kỹ thuật Micro-Batching REST API để vượt qua giới hạn vùng của tài khoản Quốc tế.
    """

    def __init__(self, config_manager=None):
        self.config = config_manager
        self._stt = QwenSTT(config_manager)
        self._listening = False
        self._thread: Optional[threading.Thread] = None
        self._stt_threads: list[threading.Thread] = []
        self._stop_event = threading.Event()
        self._on_result: Optional[Callable[[str], None]] = None
        self._push_to_talk = False
        self._audio_queue: queue.Queue = queue.Queue(maxsize=8)

    def set_on_result(self, callback: Callable[[str], None]):
        self._on_result = callback

    @property
    def is_listening(self) -> bool:
        return self._listening

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
        self._stt_threads = [
            threading.Thread(
                target=self._stt_loop,
                daemon=True,
                name=f"STT-Worker-{i+1}"
            )
            for i in range(2)
        ]
        self._thread.start()
        for t in self._stt_threads:
            t.start()
        logger.info(f"Đã bắt đầu lắng nghe micro (lang={language})")

    def stop_listening(self):
        if not self._listening:
            return
        self._listening = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
            self._thread = None
        for t in self._stt_threads:
            if t.is_alive():
                t.join(timeout=3)
        self._stt_threads = []
        logger.info("Đã dừng lắng nghe micro")

    def _stt_has_energy(self, audio: np.ndarray, threshold: float = 0.002) -> bool:
        if audio is None or len(audio) == 0:
            return False
        rms = float(np.sqrt(np.mean(np.square(audio, dtype=np.float32))))
        return rms >= threshold

    def _listen_loop(self, language: str):
        import sounddevice as sd
        
        try:
            device_index = sd.default.device[0]
            if device_index < 0:
                raise RuntimeError("Không tìm thấy thiết bị thu âm mặc định.")
            
            device_info = sd.query_devices(device_index)
            sample_rate = int(device_info.get("default_samplerate") or 16000)
            channels = min(1, int(device_info.get("max_input_channels", 1)))
        except Exception as e:
            logger.error(f"Lỗi khởi động thiết bị micro: {e}")
            self._listening = False
            return

        chunk_duration = 1.2
        overlap_duration = 0.4
        chunk_samples = int(sample_rate * chunk_duration)
        overlap_samples = int(sample_rate * overlap_duration)
        prev_tail = np.array([], dtype=np.float32)

        logger.info("Bắt đầu ghi âm micro (Qwen REST STT, chunk=1.2s, overlap=0.4s)...")

        while not self._stop_event.is_set() and self._listening:
            try:
                if self._push_to_talk and not self._is_key_pressed():
                    time.sleep(0.1)
                    continue

                recording = sd.rec(
                    chunk_samples,
                    samplerate=sample_rate,
                    channels=channels,
                    device=device_index,
                    dtype='float32'
                )
                sd.wait()

                if self._stop_event.is_set():
                    break

                if channels > 1:
                    recording = recording.mean(axis=1, keepdims=True)

                audio_mono = recording.flatten()
                if prev_tail.size > 0:
                    audio_send = np.concatenate([prev_tail, audio_mono], axis=0)
                else:
                    audio_send = audio_mono

                # VAD
                if not self._stt_has_energy(audio_send, threshold=0.002):
                    prev_tail = audio_mono[-overlap_samples:] if audio_mono.size > overlap_samples else audio_mono
                    continue

                lang = "en" if language.lower().startswith("en") else "vi"
                item = (audio_send.copy(), sample_rate, lang)
                try:
                    self._audio_queue.put_nowait(item)
                except queue.Full:
                    try:
                        self._audio_queue.get_nowait()
                    except Exception:
                        pass
                    try:
                        self._audio_queue.put_nowait(item)
                    except Exception:
                        pass

                prev_tail = audio_mono[-overlap_samples:] if audio_mono.size > overlap_samples else audio_mono

            except Exception as e:
                logger.error(f"Lỗi ghi âm micro: {e}")
                time.sleep(1)

    def _stt_loop(self):
        """Worker gửi REST ASR tách rời khỏi capture để tránh giật lag."""
        while not self._stop_event.is_set():
            try:
                audio_send, sample_rate, language = self._audio_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                t0 = time.time()
                text = self._stt.transcribe_audio(audio_send, sample_rate=sample_rate, language=language)
                dt = time.time() - t0
                if text and text.strip():
                    logger.info(f"Micro STT ({dt:.2f}s): '{text}'")
                    if self._on_result:
                        self._on_result(text)
            except Exception as e:
                logger.warning(f"Qwen STT micro request error: {e}")

    def listen_once(self, language: str = "vi-VN", timeout: int = 5) -> Optional[str]:
        """Ghi âm một lần (chế độ batch) để tương thích ngược."""
        import sounddevice as sd
        try:
            device_index = sd.default.device[0]
            if device_index < 0:
                return None
            device_info = sd.query_devices(device_index)
            sample_rate = int(device_info.get('default_samplerate') or 16000)
            channels = min(1, int(device_info.get("max_input_channels", 1)))

            recording = sd.rec(
                int(sample_rate * timeout),
                samplerate=sample_rate,
                channels=channels,
                device=device_index,
                dtype='float32'
            )
            sd.wait()

            if channels > 1:
                recording = recording.mean(axis=1, keepdims=True)

            text = self._stt.transcribe_audio(recording.flatten(), sample_rate=sample_rate, language="vi")
            return text
        except Exception as e:
            logger.warning(f"listen_once lỗi: {e}", exc_info=True)
            return None

    def set_push_to_talk(self, enabled: bool):
        self._push_to_talk = enabled

    def _is_key_pressed(self) -> bool:
        try:
            import keyboard
            return keyboard.is_pressed('ctrl+shift+m')
        except Exception:
            return True
