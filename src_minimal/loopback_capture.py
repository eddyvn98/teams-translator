"""
Loopback Audio Capture — Bắt âm thanh từ loa PC (không dùng mic)
Được tối ưu hóa cho Micro-Batching REST ASR với độ trễ cực thấp.
"""
import logging
import threading
import time
import queue
from math import gcd
from typing import Optional, Callable

import numpy as np

from src_minimal.qwen_stt import QwenSTT

logger = logging.getLogger(__name__)


class LoopbackCapture:
    """
    Bắt âm thanh từ loa/output device (những gì người khác nói trong Teams).
    Sử dụng kỹ thuật Micro-Batching REST API để vượt qua giới hạn vùng của tài khoản Quốc tế.
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
        self._realtime_stt = None
        self._realtime_sample_rate = 16000

        self._loopback_device = None
        self._sample_rate = 44100

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

        for d in devices:
            name_lower = d["name"].lower()
            if "cable output (vb-audio virtual" in name_lower and d.get("channels", 0) >= 1:
                logger.info(f"Tìm thấy CABLE Output VB-Audio: {d['name']} (index={d['index']})")
                return d["index"]

        for d in devices:
            if "stereo mix" in d["name"].lower():
                try:
                    import sounddevice as sd
                    candidates = []
                    for i in range(sd.query_devices().__len__()):
                        info = sd.query_devices(i)
                        if "stereo mix" in info["name"].lower() and info["max_input_channels"] >= 2:
                            candidates.append(i)
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

        for d in devices:
            name_lower = d["name"].lower()
            if "wasapi loopback" in name_lower and any(k in name_lower for k in ["speakers", "headphones", "fxsound", "realtek", "output"]):
                logger.info(f"Tìm thấy WASAPI loopback: {d['name']} (index={d['index']})")
                return d["index"]

        logger.info(f"Dùng loopback device: {devices[0]['name']} (index={devices[0]['index']})")
        return devices[0]["index"]

    def set_on_result(self, callback: Callable[[str], None]):
        self._on_result = callback

    def _emit_result(self, text: str, is_final: bool = True):
        if not text or not text.strip() or not self._on_result:
            return
        try:
            self._on_result(text.strip(), is_final)
        except TypeError:
            self._on_result(text.strip())

    @staticmethod
    def _audio_to_pcm16_bytes(audio: np.ndarray, source_rate: int, target_rate: int = 16000) -> bytes:
        audio = np.asarray(audio, dtype=np.float32).flatten()
        if audio.size == 0:
            return b""

        source_rate = int(source_rate)
        target_rate = int(target_rate)
        if source_rate != target_rate:
            try:
                from scipy.signal import resample_poly

                divisor = gcd(source_rate, target_rate)
                audio = resample_poly(audio, target_rate // divisor, source_rate // divisor).astype(np.float32)
            except Exception:
                target_len = max(1, int(round(audio.size * target_rate / source_rate)))
                old_x = np.linspace(0.0, 1.0, num=audio.size, endpoint=False)
                new_x = np.linspace(0.0, 1.0, num=target_len, endpoint=False)
                audio = np.interp(new_x, old_x, audio).astype(np.float32)

        pcm = np.clip(audio, -1.0, 1.0)
        return (pcm * 32767.0).astype(np.int16).tobytes()

    def _start_realtime_stt(self) -> bool:
        mode = str(self.config.get("loopback_stt_mode", "realtime") if self.config else "realtime").lower()
        if mode == "rest":
            return False

        try:
            from src_minimal.qwen_realtime_stt import QwenRealtimeSTT

            self._realtime_sample_rate = int(
                self.config.get("loopback_realtime_sample_rate", 16000) if self.config else 16000
            )
            self._realtime_stt = QwenRealtimeSTT(self.config, on_text_received=self._emit_result)
            self._realtime_stt.start(sample_rate=self._realtime_sample_rate)
            logger.info("Loopback realtime STT enabled (sample_rate=%s)", self._realtime_sample_rate)
            return True
        except Exception as e:
            self._realtime_stt = None
            logger.warning("Loopback realtime STT unavailable, falling back to REST batches: %s", e)
            return False

    def start_capture(self):
        """Bắt đầu capture âm thanh từ loa."""
        if self._capturing:
            return

        device_index = self.find_best_loopback_device()
        if device_index is None:
            logger.error("❌ KHÔNG tìm thấy loopback device!")
            return

        self._capturing = True
        self._stop_event.clear()
        use_realtime = self._start_realtime_stt()
        self._thread = threading.Thread(
            target=self._capture_loop,
            args=(device_index,),
            daemon=True,
            name="Loopback-Capture"
        )
        if use_realtime:
            self._stt_threads = []
        else:
            self._stt_threads = [
                threading.Thread(target=self._stt_loop, daemon=True, name=f"Loopback-STT-{i+1}")
                for i in range(2)
            ]
        self._thread.start()
        for t in self._stt_threads:
            t.start()
        logger.info(f"Đã bắt đầu capture loopback (device={device_index})")

    def stop_capture(self):
        if not self._capturing:
            return
        self._capturing = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
            self._thread = None
        for t in self._stt_threads:
            if t.is_alive():
                t.join(timeout=3)
        self._stt_threads = []
        if self._realtime_stt:
            try:
                self._realtime_stt.stop()
            except Exception as e:
                logger.warning("Loopback realtime STT stop error: %s", e)
            self._realtime_stt = None
        logger.info("Đã dừng capture loopback")

    @property
    def is_capturing(self) -> bool:
        return self._capturing

    def _stt_has_energy(self, audio: np.ndarray, threshold: float = 0.002) -> bool:
        if audio is None or len(audio) == 0:
            return False
        rms = float(np.sqrt(np.mean(np.square(audio, dtype=np.float32))))
        return rms >= threshold

    def _capture_loop(self, device_index: int):
        if self._realtime_stt:
            self._capture_realtime_loop(device_index)
        else:
            self._capture_rest_loop(device_index)

    def _capture_realtime_loop(self, device_index: int):
        """Stream loopback frames to realtime ASR using continuous sounddevice InputStream."""
        import sounddevice as sd

        device_info = sd.query_devices(device_index)
        sample_rate = int(device_info.get("default_samplerate") or self._sample_rate)
        is_stereo = "stereo mix" in device_info["name"].lower()
        actual_channels = 2 if is_stereo else 1

        logger.info(
            "Bắt đầu loopback realtime stream InputStream (input=%sHz, asr=%sHz)...",
            sample_rate,
            self._realtime_sample_rate,
        )

        audio_q = queue.Queue()

        def callback(indata, frames, time_info, status):
            if status:
                logger.warning(f"InputStream status: {status}")
            audio_q.put(indata.copy())

        # Target ~100ms blocks
        block_size = int(sample_rate * 0.1)

        try:
            stream = sd.InputStream(
                device=device_index,
                channels=actual_channels,
                samplerate=sample_rate,
                dtype="float32",
                blocksize=block_size,
                callback=callback
            )
            with stream:
                while not self._stop_event.is_set() and self._capturing and self._realtime_stt:
                    try:
                        recording = audio_q.get(timeout=0.1)
                        if is_stereo:
                            recording = recording.mean(axis=1, keepdims=True)
                        
                        pcm = self._audio_to_pcm16_bytes(
                            recording.flatten(),
                            source_rate=sample_rate,
                            target_rate=self._realtime_sample_rate,
                        )
                        if pcm and self._realtime_stt:
                            self._realtime_stt.send_audio(pcm)
                    except queue.Empty:
                        continue
                    except Exception as e:
                        logger.error(f"Lỗi gửi audio realtime: {e}")
        except Exception as e:
            logger.error(f"Lỗi khởi động InputStream: {e}")

    def _capture_rest_loop(self, device_index: int):
        """
        Vòng lặp capture: ghi âm từng chunk 1.2 giây và đưa vào hàng đợi xử lý.
        """
        import sounddevice as sd
        
        sample_rate = self._sample_rate
        chunk_duration = 1.2
        overlap_duration = 0.4
        chunk_samples = int(sample_rate * chunk_duration)
        overlap_samples = int(sample_rate * overlap_duration)
        prev_tail = np.array([], dtype=np.float32)
        silence_skips = 0

        logger.info("Bắt đầu loopback capture (Qwen REST STT, chunk=1.2s, overlap=0.4s)...")

        while not self._stop_event.is_set() and self._capturing:
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
                if not self._stt_has_energy(audio_send, threshold=0.002):
                    silence_skips += 1
                    prev_tail = audio_mono[-overlap_samples:] if audio_mono.size > overlap_samples else audio_mono
                    continue
                
                silence_skips = 0
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

                prev_tail = audio_mono[-overlap_samples:] if audio_mono.size > overlap_samples else audio_mono

            except Exception as e:
                logger.error(f"Lỗi capture loopback: {e}")
                time.sleep(1)

    def _stt_loop(self):
        """Worker gửi REST ASR tách rời khỏi capture để tránh mất audio khi mạng chậm."""
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
                    self._emit_result(text, is_final=True)
            except Exception as e:
                logger.warning(f"Qwen STT request error: {e}")

    def capture_once(self, duration: int = 5) -> Optional[str]:
        """Ghi âm một lần (chế độ batch) để tương thích ngược."""
        import sounddevice as sd
        try:
            device_index = self.find_best_loopback_device()
            if device_index is None:
                return None
            device_info = sd.query_devices(device_index)
            sample_rate = int(device_info.get('default_samplerate') or 44100)
            actual_channels = 2 if "stereo mix" in device_info['name'].lower() else 1

            recording = sd.rec(
                int(sample_rate * duration),
                samplerate=sample_rate,
                channels=actual_channels,
                device=device_index,
                dtype='float32'
            )
            sd.wait()

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
