"""
Real-time Speech-to-Text using direct WebSockets connection to custom ASR server.
Provides sub-second latency streaming transcription.
"""
import logging
import queue
import threading
import os
import json
from typing import Callable, Optional
import websocket

logger = logging.getLogger(__name__)


class QwenRealtimeSTT:
    def __init__(self, config_manager=None, on_text_received: Optional[Callable[[str, bool], None]] = None):
        """
        Args:
            config_manager: Configuration manager.
            on_text_received: Callback function signature (text: str, is_final: bool)
        """
        self.config = config_manager
        self.on_text_received = on_text_received
        self._is_running = False
        self._audio_queue = queue.Queue()
        self._ws = None
        self._worker_thread: Optional[threading.Thread] = None
        self._receiver_thread: Optional[threading.Thread] = None

    def _api_key(self) -> str:
        key = os.getenv("ASR_API_KEY", "").strip()
        if not key:
            key = os.getenv("QWEN_API_KEY", "").strip()
        if not key:
            key = os.getenv("DASHSCOPE_API_KEY", "").strip()
        if not key and self.config:
            key = str(self.config.get("qwen_api_key", "")).strip()
        return key

    def _base_url(self) -> str:
        base_url = os.getenv("ASR_BASE_URL", "").strip()
        if not base_url and self.config:
            base_url = str(self.config.get("qwen_base_url", "")).strip()
        if not base_url:
            base_url = "https://dich.vivutrade.io.vn/v1"
        return base_url.rstrip("/")

    def _websocket_url(self) -> str:
        # Convert http/https to ws/wss
        base_url = self._base_url()
        if base_url.startswith("https://"):
            ws_url = "wss://" + base_url[8:]
        elif base_url.startswith("http://"):
            ws_url = "ws://" + base_url[7:]
        else:
            ws_url = base_url
        return ws_url

    def _model(self) -> str:
        if self.config:
            cfg_model = str(self.config.get("qwen_stt_model", "")).strip()
            if cfg_model:
                return cfg_model
        return os.getenv("QWEN_STT_MODEL", "iic/SenseVoiceSmall")

    def _language(self) -> str:
        if self.config:
            language = str(self.config.get("loopback_realtime_language", "en")).strip().lower()
            if language:
                return language
        return "en"

    def start(self, sample_rate: int = 16000):
        if self._is_running:
            return

        ws_base = self._websocket_url()
        model = self._model()
        language = self._language()
        
        # Build WebSocket URL
        lang = "vi" if language.lower().startswith("vi") else "en"
        ws_url = f"{ws_base}/audio/stream?model={model}&language={lang}&client=windows"
        logger.info(f"Connecting to ASR WebSocket: {ws_url}")

        headers = {}
        api_key = self._api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            self._ws = websocket.create_connection(ws_url, header=headers, timeout=10)
            self._ws.settimeout(None)  # Remove timeout for recv operations so it doesn't drop during silence
            self._is_running = True
        except Exception as e:
            logger.error(f"Failed to connect to ASR WebSocket at {ws_url}: {e}")
            raise e

        # Clear any stale audio data
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break

        # Start streaming worker threads
        self._worker_thread = threading.Thread(target=self._stream_worker, daemon=True, name="ASR-Streamer")
        self._receiver_thread = threading.Thread(target=self._receiver_worker, daemon=True, name="ASR-Receiver")
        
        self._worker_thread.start()
        self._receiver_thread.start()
        logger.info("[QwenRealtimeSTT] Real-time ASR started.")

    def send_audio(self, pcm_bytes: bytes):
        """Buffer raw PCM bytes to be streamed asynchronously."""
        if self._is_running:
            self._audio_queue.put(pcm_bytes)

    def _stream_worker(self):
        logger.info("ASR WebSocket streamer thread started.")
        while self._is_running and self._ws:
            try:
                frame = self._audio_queue.get(timeout=0.1)
                if frame and self._is_running and self._ws:
                    self._ws.send_binary(frame)
            except queue.Empty:
                continue
            except Exception as e:
                if self._is_running:
                    logger.error(f"Error sending audio frame: {e}")
                    self._is_running = False
                break
        logger.info("ASR WebSocket streamer thread stopped.")

    def _receiver_worker(self):
        import socket
        logger.info("ASR WebSocket receiver thread started.")
        while self._is_running and self._ws:
            try:
                message = self._ws.recv()
                if not message:
                    continue
                data = json.loads(message)
                if data.get("event") == "result":
                    text = data.get("text", "")
                    is_final = data.get("is_final", False)
                    if self.on_text_received:
                        self.on_text_received(text, is_final)
            except (websocket.WebSocketTimeoutException, socket.timeout):
                # Simply ignore timeouts and wait again
                continue
            except Exception as e:
                if self._is_running:
                    logger.error(f"Error receiving ASR WebSocket message: {e}")
                    self._is_running = False
                break
        logger.info("ASR WebSocket receiver thread stopped.")

    def stop(self):
        if not self._is_running:
            return
        
        self._is_running = False
        
        if self._ws:
            try:
                self._ws.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")
            self._ws = None

        if self._worker_thread:
            self._worker_thread.join(timeout=1.0)
            self._worker_thread = None

        if self._receiver_thread:
            self._receiver_thread.join(timeout=1.0)
            self._receiver_thread = None

        logger.info("[QwenRealtimeSTT] Real-time ASR stopped.")
