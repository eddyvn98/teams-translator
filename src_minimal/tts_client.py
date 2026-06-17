import json
import logging
import threading
import time
import websocket

logger = logging.getLogger(__name__)

class TtsClient:
    def __init__(self, config_manager=None, callback=None):
        self.config = config_manager
        self.callback = callback
        self._is_running = False
        self._thread = None
        self._ws = None

    def _get_ws_url(self) -> str:
        # Default fallback url
        base_url = "http://127.0.0.1:8000"
        if self.config:
            # Get ASR Server URL configured in App Windows settings
            base_url = str(self.config.get("qwen_asr_url", "http://127.0.0.1:8000")).strip()
        
        # Parse http/https protocols to ws/wss protocols
        if base_url.startswith("https://"):
            ws_url = "wss://" + base_url[8:].rstrip("/")
        elif base_url.startswith("http://"):
            ws_url = "ws://" + base_url[7:].rstrip("/")
        else:
            ws_url = "ws://" + base_url.rstrip("/")
            
        # Append specific Windows stream endpoint
        if not ws_url.endswith("/windows/stream"):
            # Ensure it ends with /windows/stream (clean v1 path compatibility)
            if ws_url.endswith("/v1"):
                ws_url = ws_url[:-3]
            ws_url = f"{ws_url.rstrip('/')}/windows/stream"
            
        return ws_url

    def start(self):
        if self._is_running:
            return
        self._is_running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="TTS-WebSocket-Client")
        self._thread.start()
        logger.info("[TTS Client] WebSocket client thread started.")

    def stop(self):
        self._is_running = False
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None
        if self._thread:
            # We don't join strictly with blocking because websocket timeout might delay it
            self._thread = None
        logger.info("[TTS Client] WebSocket client thread stopped.")

    def _run_loop(self):
        while self._is_running:
            ws_url = self._get_ws_url()
            logger.info(f"[TTS Client] Connecting to: {ws_url}")
            try:
                # Create a persistent websocket connection
                self._ws = websocket.create_connection(ws_url, timeout=10)
                logger.info("[TTS Client] Connected to TTS Server successfully.")
                
                # Maintain connection and receive messages
                while self._is_running and self._ws:
                    try:
                        message = self._ws.recv()
                        if not message:
                            continue
                        
                        # Parse message from server
                        data = json.loads(message)
                        event = data.get("event")
                        text = data.get("text", "").strip()
                        
                        if event == "speak" and text:
                            logger.info(f"[TTS Client] Received broadcast speech request: '{text}'")
                            if self.callback:
                                self.callback(text)
                    except websocket.WebSocketConnectionClosedException:
                        logger.warning("[TTS Client] Connection closed by server.")
                        break
                    except Exception as e:
                        # Prevent loop crash on parse errors
                        logger.error(f"[TTS Client] Error in message loop: {e}")
                        time.sleep(0.5)
                        
            except Exception as e:
                logger.warning(f"[TTS Client] Failed to connect or connection lost: {e}. Reconnecting in 5 seconds...")
                if self._ws:
                    try:
                        self._ws.close()
                    except Exception:
                        pass
                    self._ws = None
                
                # Wait for 5 seconds, checking running state to exit quickly on shutdown
                for _ in range(5):
                    if not self._is_running:
                        break
                    time.sleep(1.0)
                    
        logger.info("[TTS Client] Connection loop terminated.")
