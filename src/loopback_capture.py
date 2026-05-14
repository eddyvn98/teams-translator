"""
Loopback Audio Capture â€” Báº¯t Ã¢m thanh tá»« loa PC (khÃ´ng dÃ¹ng mic)
DÃ¹ng Ä‘á»ƒ báº¯t giá»ng nÃ³i cá»§a ngÆ°á»i khÃ¡c trong Teams meeting

YÃªu cáº§u:
- Windows: VB-CABLE Virtual Audio Cable hoáº·c Stereo Mix
- Hoáº·c PyAudio loopback device
"""
import logging
import threading
import time
import queue
import tempfile
import os
import sys
from typing import Optional, Callable

import numpy as np

from src.qwen_stt import QwenSTT

logger = logging.getLogger(__name__)


class LoopbackCapture:
    """
    Báº¯t Ã¢m thanh tá»« loa/output device (nhá»¯ng gÃ¬ ngÆ°á»i khÃ¡c nÃ³i trong Teams).
    
    TrÃªn Windows, cáº§n 1 trong cÃ¡c Ä‘iá»u kiá»‡n sau:
    1. Stereo Mix enabled (Sound Control Panel â†’ Recording â†’ Show Disabled Devices â†’ Enable Stereo Mix)
    2. VB-CABLE Virtual Audio Cable cÃ i Ä‘áº·t
    3. PyAudio cÃ³ WASAPI loopback support
    """

    def __init__(self, config_manager=None):
        self.config = config_manager
        self._stt = QwenSTT(config_manager)
        self._capturing = False
        self._thread: Optional[threading.Thread] = None
        self._stt_threads: list[threading.Thread] = []
        self._stop_event = threading.Event()
        self._on_result: Optional[Callable[[str], None]] = None
        self._audio_queue: queue.Queue = queue.Queue(maxsize=8)
        self._queue_drops = 0

        # Tá»± Ä‘á»™ng tÃ¬m loopback device
        self._loopback_device = None
        self._sample_rate = 44100  # Äa sá»‘ devices há»— trá»£ 44100

    def list_loopback_devices(self) -> list:
        """
        Liá»‡t kÃª cÃ¡c thiáº¿t bá»‹ audio cÃ³ thá»ƒ dÃ¹ng Ä‘á»ƒ báº¯t loopback.
        Tráº£ vá» list dict: [{"index": N, "name": "...", "channels": N}, ...]
        """
        devices = []
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                name = info["name"].lower()
                # TÃ¬m thiáº¿t bá»‹ loopback: stereo mix, cble, loopback, what u hear
                if any(kw in name for kw in ["stereo mix", "cble", "loopback", "what u hear",
                                              "cable input", "cable output", "vb-audio",
                                              "virtual cable", "waveout"]):
                    devices.append({
                        "index": i,
                        "name": info["name"],
                        "channels": info["maxInputChannels"],
                        "sample_rate": int(info["defaultSampleRate"])
                    })
                # WASAPI loopback devices trÃªn Windows
                if "speaker" in name or "headphone" in name or "realtek" in name or "output" in name:
                    # Kiá»ƒm tra náº¿u cÃ³ WASAPI loopback host API
                    host_api = p.get_host_api_info_by_index(info["hostApi"])
                    if "wasapi" in host_api["name"].lower():
                        devices.append({
                            "index": i,
                            "name": info["name"] + " (WASAPI loopback)",
                            "channels": info["maxInputChannels"],
                            "sample_rate": int(info["defaultSampleRate"])
                        })
            p.terminate()
        except Exception as e:
            logger.error(f"Lá»—i liá»‡t kÃª loopback devices: {e}")

        return devices

    def find_best_loopback_device(self) -> Optional[int]:
        """Tá»± Ä‘á»™ng tÃ¬m thiáº¿t bá»‹ loopback tá»‘t nháº¥t."""
        devices = self.list_loopback_devices()
        if not devices:
            logger.warning("KhÃ´ng tÃ¬m tháº¥y loopback device nÃ o!")
            return None

        # Æ¯u tiÃªn: Stereo Mix > WASAPI loopback (Speakers) > CABLE Output
        # Stereo Mix: báº¯t trá»±c tiáº¿p Ã¢m thanh tá»« sound card, váº«n nghe Ä‘Æ°á»£c loa
        # Stereo Mix thÆ°á»ng cÃ³ index 3, 12, 25, 27 trÃªn mÃ¡y nÃ y
        for d in devices:
            if "stereo mix" in d["name"].lower():
                # XÃ¡c thá»±c báº±ng sounddevice
                try:
                    import sounddevice as sd
                    import numpy as np
                    candidates = []
                    for i in range(sd.query_devices().__len__()):
                        info = sd.query_devices(i)
                        if "stereo mix" in info["name"].lower() and info["max_input_channels"] >= 2:
                            candidates.append(i)
                    # Test tá»«ng candidate Ä‘á»ƒ tÃ¬m cÃ¡i cÃ³ tÃ­n hiá»‡u
                    for idx in candidates:
                        try:
                            sr = int(min(44100, info['default_samplerate']))
                            rec = sd.rec(int(sr * 2), samplerate=sr, channels=2, device=idx, dtype='float32')
                            sd.wait()
                            if abs(rec).max() > 0.003:
                                logger.info(f"TÃ¬m tháº¥y Stereo Mix (SD): [{idx}] {sd.query_devices(idx)['name']}")
                                return idx
                        except:
                            continue
                except:
                    pass
                logger.info(f"TÃ¬m tháº¥y Stereo Mix (PA): {d['name']} (index={d['index']})")
                return d["index"]
        # CABLE Output VB-Audio (Ä‘Ã£ test á»•n)
        for d in devices:
            name_lower = d["name"].lower()
            if "cable output (vb-audio virtual" in name_lower and d.get("channels", 0) >= 2:
                logger.info(f"TÃ¬m tháº¥y CABLE Output VB-Audio: {d['name']} (index={d['index']})")
                return d["index"]
        # Stereo Mix
        for d in devices:
            if "stereo mix" in d["name"].lower() and d.get("channels", 0) >= 2:
                logger.info(f"TÃ¬m tháº¥y Stereo Mix: {d['name']} (index={d['index']})")
                return d["index"]

        # Fallback: device Ä‘áº§u tiÃªn
        logger.info(f"DÃ¹ng loopback device: {devices[0]['name']} (index={devices[0]['index']})")
        return devices[0]["index"]

    def set_on_result(self, callback: Callable[[str], None]):
        self._on_result = callback

    def start_capture(self):
        """Báº¯t Ä‘áº§u capture Ã¢m thanh tá»« loa."""
        if self._capturing:
            return

        device_index = self.find_best_loopback_device()
        if device_index is None:
            logger.error(
                "âŒ KHÃ”NG tÃ¬m tháº¥y loopback device!\n"
                "CÃ i VB-CABLE: https://vb-audio.com/Cable/\n"
                "Hoáº·c báº­t Stereo Mix: Sound Panel â†’ Recording â†’ Show Disabled â†’ Enable Stereo Mix"
            )
            return

        self._capturing = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._capture_loop, args=(device_index,), daemon=True, name="Loopback-Capture")
        self._stt_threads = [
            threading.Thread(target=self._stt_loop, daemon=True, name=f"Loopback-STT-{i+1}")
            for i in range(2)
        ]
        self._thread.start()
        for t in self._stt_threads:
            t.start()
        logger.info(f"ÄÃ£ báº¯t Ä‘áº§u capture loopback (device={device_index})")

    def stop_capture(self):
        self._capturing = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        for t in self._stt_threads:
            if t.is_alive():
                t.join(timeout=3)
        logger.info("ÄÃ£ dá»«ng capture loopback")

    @property
    def is_capturing(self) -> bool:
        return self._capturing

    def _capture_loop(self, device_index: int):
        """
        VÃ²ng láº·p capture: ghi Ã¢m tá»«ng chunk, Google STT.
        """
        import sounddevice as sd
        import time
        sample_rate = self._sample_rate
        chunk_duration = 1.0
        overlap_duration = 0.2
        chunk_samples = int(sample_rate * chunk_duration)
        overlap_samples = int(sample_rate * overlap_duration)
        prev_tail = np.array([], dtype=np.float32)

        logger.info("Bat dau loopback stream (Qwen STT, chunk=1.0s, overlap=0.2s)...")

        while not self._stop_event.is_set():
            try:
                device_info = sd.query_devices(device_index)
                is_stereo = "stereo mix" in device_info['name'].lower()
                actual_channels = 2 if is_stereo else 1

                recording = sd.rec(
                    chunk_samples,
                    samplerate=sample_rate,
                    channels=actual_channels,
                    device=device_index,
                    dtype='float32'
                )
                sd.wait()

                if self._stop_event.is_set():
                    break

                if is_stereo:
                    recording = recording.mean(axis=1, keepdims=True)

                audio_mono = recording.flatten()
                if prev_tail.size > 0:
                    audio_send = np.concatenate([prev_tail, audio_mono], axis=0)
                else:
                    audio_send = audio_mono

                # VAD
                if not self._stt.has_energy(audio_send, threshold=0.003):
                    prev_tail = audio_mono[-overlap_samples:] if audio_mono.size > overlap_samples else audio_mono
                    continue
                item = (audio_send.copy(), sample_rate, "en")
                try:
                    self._audio_queue.put_nowait(item)
                except queue.Full:
                    self._queue_drops += 1
                    try:
                        self._audio_queue.get_nowait()
                    except Exception:
                        pass
                    try:
                        self._audio_queue.put_nowait(item)
                    except Exception:
                        pass
                    if self._queue_drops % 10 == 0:
                        logger.warning(f"Audio queue drop count={self._queue_drops}")

                prev_tail = audio_mono[-overlap_samples:] if audio_mono.size > overlap_samples else audio_mono

            except Exception as e:
                logger.error(f"Lá»—i capture loopback: {e}")
                time.sleep(1)

    def _stt_loop(self):
        """Worker gửi STT tách rời khỏi capture để tránh mất audio khi mạng chậm."""
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
                    logger.info(f"ðŸ”Š Loopback STT ({dt:.2f}s): '{text}'")
                    if self._on_result:
                        self._on_result(text)
            except Exception as e:
                logger.warning(f"Qwen STT request error: {e}")

    def capture_once(self, duration: int = 5) -> Optional[str]:
        """Capture loopback má»™t láº§n."""
        device_index = self.find_best_loopback_device()
        if device_index is None:
            return None

        try:
            import sounddevice as sd

            device_info = sd.query_devices(device_index)
            sample_rate = int(device_info.get('default_samplerate') or self._sample_rate or 44100)
            channels = min(1, int(device_info.get('max_input_channels', 0)))
            if channels == 0:
                logger.warning(f"Device {device_index} khÃ´ng cÃ³ input channel")
                return None

            # Stereo Mix cáº§n 2 channels, CABLE cáº§n 1
            actual_channels = 2 if "stereo mix" in device_info['name'].lower() else 1

            recording = sd.rec(
                int(sample_rate * duration),
                samplerate=sample_rate,
                channels=actual_channels,
                device=device_index,
                dtype='float32'
            )
            sd.wait()

            # Náº¿u stereo, convert sang mono
            if actual_channels == 2:
                recording = recording.mean(axis=1, keepdims=True)

            if actual_channels == 2:
                recording = recording.mean(axis=1, keepdims=True)
            text = self._stt.transcribe_audio(recording.flatten(), sample_rate=sample_rate, language="en")
            return text
        except Exception as e:
            logger.warning(f"capture_once lá»—i: {e}", exc_info=True)
            return None

    def get_available_devices_info(self) -> str:
        """Tráº£ vá» thÃ´ng tin cÃ¡c thiáº¿t bá»‹ audio Ä‘á»ƒ debug."""
        lines = ["=== Audio Devices ==="]
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                lines.append(
                    f"  [{i}] {info['name']} | "
                    f"in={info['maxInputChannels']} out={info['maxOutputChannels']} | "
                    f"{int(info['defaultSampleRate'])}Hz | "
                    f"host={p.get_host_api_info_by_index(info['hostApi'])['name']}"
                )
            p.terminate()
        except Exception as e:
            lines.append(f"  Lá»—i: {e}")
        return "\n".join(lines)

