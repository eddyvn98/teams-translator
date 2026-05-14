"""
Text-to-Speech module — Đọc to văn bản qua loa
"""
import logging
import threading
import time
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class TextToSpeech:
    """
    Đọc văn bản thành giọng nói.
    Khi nhận text tiếng Việt → đọc bằng giọng Anh (vì output là tiếng Anh).
    """

    def __init__(self, config_manager=None):
        self.config = config_manager
        self._speaking = False
        self._lock = threading.Lock()
        self._on_done: Optional[Callable] = None

    def speak(self, text: str, wait: bool = False):
        """
        Đọc văn bản.
        Sử dụng một thread mới cho mỗi lần đọc để đảm bảo không chặn UI
        và tránh lỗi COM thread context trên Windows.
        """
        if not text or not text.strip():
            return

        def _do_speak():
            with self._lock:
                engine = None
                try:
                    import pyttsx3
                    # Khởi tạo engine ngay trong thread này để tránh lỗi COM
                    engine = pyttsx3.init()
                    self._apply_config(engine)
                    
                    self._speaking = True
                    engine.say(text)
                    engine.runAndWait()
                    self._speaking = False
                    
                    if self._on_done:
                        self._on_done()
                except ImportError:
                    logger.error("Lỗi TTS: Thư viện 'pyttsx3' chưa được cài đặt.")
                except Exception as e:
                    logger.error(f"Lỗi TTS: {e}")
                finally:
                    self._speaking = False
                    # Giải phóng engine
                    if engine:
                        try:
                            engine.stop()
                            del engine
                        except:
                            pass

        if wait:
            _do_speak()
        else:
            threading.Thread(target=_do_speak, daemon=True, name="TTS-Thread").start()

    def _apply_config(self, engine):
        """Áp dụng cấu hình voice vào engine được truyền vào."""
        if not engine or not self.config:
            return

        try:
            rate = self.config.get("tts_rate", 180)
            volume = self.config.get("tts_volume", 1.0)
            engine.setProperty("rate", rate)
            engine.setProperty("volume", volume)

            # Chọn giọng Anh
            voices = engine.getProperty("voices")
            voice_choice = self.config.get("tts_voice", "english")

            if voice_choice == "english":
                # Tìm giọng Anh (female/male)
                for v in voices:
                    v_name = v.name.lower()
                    v_id = v.id.lower()
                    if "english" in v_name or "en_" in v_id or "david" in v_name or "zira" in v_name:
                        engine.setProperty("voice", v.id)
                        logger.info(f"Đã chọn giọng TTS: {v.name}")
                        break
                else:
                    logger.info(f"Không tìm thấy giọng Anh, dùng mặc định. Có: {[v.name for v in voices]}")
            else:
                # Giọng Việt (nếu có)
                for v in voices:
                    if "vietnamese" in v.name.lower() or "vi_" in v.id.lower():
                        engine.setProperty("voice", v.id)
                        break
        except Exception as e:
            logger.warning(f"Lỗi cấu hình TTS: {e}")

    def stop(self):
        """Dừng đọc. Lưu ý: Với cách init trong thread, việc stop từ bên ngoài khó hơn."""
        self._speaking = False

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    def set_on_done(self, callback: Callable):
        self._on_done = callback
