"""
Loopback Audio Capture — Bắt âm thanh từ loa PC (không dùng mic)
Dùng để bắt giọng nói của người khác trong Teams meeting

Yêu cầu:
- Windows: VB-CABLE Virtual Audio Cable hoặc Stereo Mix
- Hoặc PyAudio loopback device
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
    Bắt âm thanh từ loa/output device (những gì người khác nói trong Teams).
    
    Trên Windows, cần 1 trong các điều kiện sau:
    1. Stereo Mix enabled (Sound Control Panel → Recording → Show Disabled Devices → Enable Stereo Mix)
    2. VB-CABLE Virtual Audio Cable cài đặt
    3. PyAudio có WASAPI loopback support
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

        # Tự động tìm loopback device
        self._loopback_device = None
        self._sample_rate = 44100  # Đa số devices hỗ trợ 44100

    def list_loopback_devices(self) -> list:
        """
        Liệt kê các thiết bị audio có thể dùng để bắt loopback.
        Trả về list dict: [{"index": N, "name": "...", "channels": N}, ...]
        """
        devices = []
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                name = info["name"].lower()
                # Tìm thiết bị loopback: stereo mix, cble, loopback, what u hear
                if any(kw in name for kw in ["stereo mix", "cble", "loopback", "what u hear",
                                              "cable input", "cable output", "vb-audio",
                                              "virtual cable", "waveout"]):
                    devices.append({
                        "index": i,
                        "name": info["name"],
                        "channels": info["maxInputChannels"],
                        "sample_rate": int(info["defaultSampleRate"])
                    })
                # WASAPI loopback devices trên Windows
                if "speaker" in name or "headphone" in name or "realtek" in name or "output" in name:
                    # Kiểm tra nếu có WASAPI loopback host API
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
            logger.error(f"Lỗi liệt kê loopback devices: {e}")

        return devices

    def find_best_loopback_device(self) -> Optional[int]:
        """Tự động tìm thiết bị loopback tốt nhất."""
        devices = self.list_loopback_devices()
        if not devices:
            logger.warning("Không tìm thấy loopback device nào!")
            return None

        # Ưu tiên: Stereo Mix > WASAPI loopback (Speakers) > CABLE Output
        # Stereo Mix: bắt trực tiếp âm thanh từ sound card, vẫn nghe được loa
        # Stereo Mix thường có index 3, 12, 25, 27 trên máy này
        for d in devices:
            if "stereo mix" in d["name"].lower():
                # Xác thực bằng sounddevice
                try:
                    import sounddevice as sd
                    import numpy as np
                    candidates = []
                    for i in range(sd.query_devices().__len__()):
                        info = sd.query_devices(i)
                        if "stereo mix" in info["name"].lower() and info["max_input_channels"] >= 2:
                            candidates.append(i)
                    # Test từng candidate để tìm cái có tín hiệu
                    for idx in candidates:
                        try:
                            sr = int(min(44100, info['default_samplerate']))
                            rec = sd.rec(int(sr * 2), samplerate=sr, channels=2, device=idx, dtype='float32')
                            sd.wait()
                            if abs(rec).max() > 0.003:
                                logger.info(f"Tìm thấy Stereo Mix (SD): [{idx}] {sd.query_devices(idx)['name']}")
                                return idx
                        except:
                            continue
                except:
                    pass
                logger.info(f"Tìm thấy Stereo Mix (PA): {d['name']} (index={d['index']})")
                return d["index"]
        # CABLE Output VB-Audio (đã test ổn)
        for d in devices:
            name_lower = d["name"].lower()
            if "cable output (vb-audio virtual" in name_lower and d.get("channels", 0) >= 2:
                logger.info(f"Tìm thấy CABLE Output VB-Audio: {d['name']} (index={d['index']})")
                return d["index"]
        # Stereo Mix
        for d in devices:
            if "stereo mix" in d["name"].lower() and d.get("channels", 0) >= 2:
                logger.info(f"Tìm thấy Stereo Mix: {d['name']} (index={d['index']})")
                return d["index"]

        # Fallback: device đầu tiên
        logger.info(f"Dùng loopback device: {devices[0]['name']} (index={devices[0]['index']})")
        return devices[0]["index"]

    def set_on_result(self, callback: Callable[[str], None]):
        self._on_result = callback

    def start_capture(self):
        """Bắt đầu capture âm thanh từ loa."""
        if self._capturing:
            return

        device_index = self.find_best_loopback_device()
        if device_index is None:
            logger.error(
                "❌ KHÔNG tìm thấy loopback device!\n"
                "Cài VB-CABLE: https://vb-audio.com/Cable/\n"
                "Hoặc bật Stereo Mix: Sound Panel → Recording → Show Disabled → Enable Stereo Mix"
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
        logger.info(f"Đã bắt đầu capture loopback (device={device_index})")

    def stop_capture(self):
        self._capturing = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        for t in self._stt_threads:
            if t.is_alive():
                t.join(timeout=3)
        logger.info("Đã dừng capture loopback")

    @property
    def is_capturing(self) -> bool:
        return self._capturing

    def _capture_loop(self, device_index: int):
        """
        Vòng lặp capture: ghi âm từng chunk, Google STT.
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
                logger.error(f"Lỗi capture loopback: {e}")
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
                    logger.info(f"Loopback STT ({dt:.2f}s): '{text}'")
                    if self._on_result:
                        self._on_result(text)
            except Exception as e:
                logger.warning(f"Qwen STT request error: {e}")

    def capture_once(self, duration: int = 5) -> Optional[str]:
        """Capture loopback một lần."""
        device_index = self.find_best_loopback_device()
        if device_index is None:
            return None

        try:
            import sounddevice as sd

            device_info = sd.query_devices(device_index)
            sample_rate = int(device_info.get('default_samplerate') or self._sample_rate or 44100)
            channels = min(1, int(device_info.get('max_input_channels', 0)))
            if channels == 0:
                logger.warning(f"Device {device_index} không có input channel")
                return None

            # Stereo Mix cần 2 channels, CABLE cần 1
            actual_channels = 2 if "stereo mix" in device_info['name'].lower() else 1

            recording = sd.rec(
                int(sample_rate * duration),
                samplerate=sample_rate,
                channels=actual_channels,
                device=device_index,
                dtype='float32'
            )
            sd.wait()

            # Nếu stereo, convert sang mono
            if actual_channels == 2:
                recording = recording.mean(axis=1, keepdims=True)

            if actual_channels == 2:
                recording = recording.mean(axis=1, keepdims=True)
            text = self._stt.transcribe_audio(recording.flatten(), sample_rate=sample_rate, language="en")
            return text
        except Exception as e:
            logger.warning(f"capture_once lỗi: {e}", exc_info=True)
            return None

    def get_available_devices_info(self) -> str:
        """Trả về thông tin các thiết bị audio để debug."""
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
            lines.append(f"  Lỗi: {e}")
        return "\n".join(lines)

