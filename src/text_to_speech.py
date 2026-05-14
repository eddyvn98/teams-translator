"""
Text-to-Speech module — Đọc to văn bản qua loa
"""
import logging
import threading
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class TextToSpeech:
    """
    Đọc văn bản thành giọng nói.
    Khi nhận text tiếng Việt → đọc bằng giọng Anh (vì output là tiếng Anh).
    """

    def __init__(self, config_manager=None):
        self.config = config_manager
        self._engine = None
        self._speaking = False
        self._lock = threading.Lock()
        self._on_done: Optional[Callable] = None

    def _get_engine(self):
        """Lazy init engine."""
        if self._engine is None:
            try:
                import pyttsx3
                self._engine = pyttsx3.init()
                self._apply_config()
            except Exception as e:
                logger.error(f"Không thể khởi tạo TTS engine: {e}")
                raise
        return self._engine

    def _apply_config(self):
        """Áp dụng cấu hình voice."""
        if not self._engine or not self.config:
            return

        try:
            rate = self.config.get("tts_rate", 180)
            volume = self.config.get("tts_volume", 1.0)
            self._engine.setProperty("rate", rate)
            self._engine.setProperty("volume", volume)

            # Chọn giọng Anh
            voices = self._engine.getProperty("voices")
            voice_choice = self.config.get("tts_voice", "english")

            if voice_choice == "english":
                # Tìm giọng Anh (female/male)
                for v in voices:
                    if "english" in v.name.lower() or "en_" in v.id.lower() or "david" in v.name.lower() or "zira" in v.name.lower():
                        self._engine.setProperty("voice", v.id)
                        logger.info(f"Đã chọn giọng: {v.name}")
                        break
                else:
                    logger.info(f"Không tìm thấy giọng Anh, dùng mặc định. Có: {[v.name for v in voices]}")
            else:
                # Giọng Việt (nếu có)
                for v in voices:
                    if "vietnamese" in v.name.lower() or "vi_" in v.id.lower():
                        self._engine.setProperty("voice", v.id)
                        break
        except Exception as e:
            logger.warning(f"Lỗi cấu hình TTS: {e}")

    def speak(self, text: str, wait: bool = False):
        """
        Đọc văn bản.

        Args:
            text: Văn bản cần đọc
            wait: True = đợi đọc xong, False = đọc bất đồng bộ
        """
        if not text or not text.strip():
            return

        def _do_speak():
            with self._lock:
                try:
                    engine = self._get_engine()
                    self._speaking = True
                    engine.say(text)
                    engine.runAndWait()
                    self._speaking = False
                    if self._on_done:
                        self._on_done()
                except Exception as e:
                    logger.error(f"Lỗi TTS: {e}")
                    self._speaking = False

        if wait:
            _do_speak()
        else:
            threading.Thread(target=_do_speak, daemon=True, name="TTS-Thread").start()

    def stop(self):
        """Dừng đọc ngay lập tức."""
        if self._engine and self._speaking:
            try:
                self._engine.stop()
            except Exception:
                pass
        self._speaking = False

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    def set_on_done(self, callback: Callable):
        self._on_done = callback
