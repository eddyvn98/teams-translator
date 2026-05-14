"""
Translator module — Google Translate Anh ↔ Việt
"""
import logging
import re

logger = logging.getLogger(__name__)


class Translator:
    """Dịch Anh-Việt 2 chiều bằng Google Translate API (free, không cần key)."""

    def __init__(self, config_manager=None):
        self._translator = None
        self._fallback = None  # Tự fallback nếu Google lỗi
        self.config = config_manager
        self._missing_deep_translator_logged = False

    def _get_translator(self):
        """Lazy init translator — dùng deep-translator (tương thích httpx mới)."""
        if self._translator is None:
            try:
                from deep_translator import GoogleTranslator
                self._translator = GoogleTranslator
            except Exception as e:
                if not self._missing_deep_translator_logged:
                    logger.info(f"deep-translator chưa có ({e}), dùng requests fallback")
                    self._missing_deep_translator_logged = True
                self._translator = None
        return self._translator

    def _google_translate_via_requests(self, text: str, dest: str = "vi", src: str = "auto") -> str:
        """Dịch trực tiếp qua Google Translate bằng requests."""
        import requests
        import re
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": src,
                "tl": dest,
                "dt": "t",
                "q": text,
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                translated = "".join(seg[0] for seg in data[0] if seg[0])
                if translated:
                    return translated
            logger.warning(f"Google Translate API trả về status {resp.status_code}")
        except Exception as e:
            logger.warning(f"Google Translate via requests lỗi: {e}")
        return None

    def detect_language(self, text: str) -> str:
        """Phát hiện ngôn ngữ của text. Trả về 'vi', 'en', hoặc 'unknown'."""
        if not text or not text.strip():
            return "unknown"

        # Đếm ký tự có dấu tiếng Việt
        vi_chars = len(re.findall(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', text.lower()))
        # Đếm từ tiếng Anh phổ biến
        en_words = len(re.findall(r'\b(the|is|are|was|were|have|has|had|do|does|did|can|could|will|would|shall|should|may|might|this|that|these|those|with|from|about|there|their|what|when|where|why|how|which)\b', text.lower()))

        # Nếu text dưới 3 từ, dùng từ điển dấu
        if len(text.split()) < 5:
            if vi_chars >= 1:
                return "vi"
            return "en"

        # Với text dài hơn, so tỷ lệ
        total_words = max(len(text.split()), 1)
        if vi_chars / total_words > 0.03:  # >3% ký tự có dấu
            return "vi"
        return "en"

    def translate(self, text: str, dest: str = "vi", src: str = "auto") -> str:
        """
        Dịch text.

        Args:
            text: Văn bản cần dịch
            dest: Ngôn ngữ đích ('vi' hoặc 'en')
            src: Ngôn ngữ nguồn ('auto' để tự phát hiện)

        Returns:
            str: Văn bản đã dịch
        """
        if not text or not text.strip():
            return ""

        # Nếu text quá ngắn (1 từ), không cần dịch
        if len(text.strip().split()) <= 1 and len(text.strip()) <= 3:
            return text

        translator_cls = self._get_translator()
        if translator_cls:
            try:
                result = translator_cls(source=src, target=dest).translate(text)
                return result if result else text
            except Exception as e:
                logger.warning(f"Lỗi deep-translator: {e}, thử fallback requests")

        # Fallback: dùng requests trực tiếp
        result = self._google_translate_via_requests(text, dest=dest, src=src)
        if result:
            return result

        # No translation available — return original
        return text

    def _fallback_translate(self, text: str, dest: str) -> str:
        """Fallback translation using libre or other free source."""
        try:
            # Cố gắng dùng API miễn phí khác
            import requests
            # Thử LibreTranslate public instance
            url = "https://libretranslate.com/translate"
            payload = {
                "q": text,
                "source": "auto",
                "target": dest,
                "format": "text"
            }
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "translatedText" in data:
                    return data["translatedText"]
        except Exception as e:
            logger.warning(f"Fallback translate lỗi: {e}")

        return text  # Cuối cùng trả về text gốc

    def translate_bidirectional(self, text: str, direction: str = "auto") -> dict:
        """
        Dịch 2 chiều, phát hiện ngôn ngữ tự động.

        Args:
            text: Văn bản cần dịch
            direction: 'auto', 'en2vi', 'vi2en'

        Returns:
            dict: { 'source_text': str, 'target_text': str, 'source_lang': str,
                    'display_text': str (text hiển thị trên caption) }
        """
        if not text or not text.strip():
            return {"source_text": "", "target_text": "", "source_lang": "unknown", "display_text": ""}

        if direction == "en2vi":
            src_lang = "en"
            dest_lang = "vi"
        elif direction == "vi2en":
            src_lang = "vi"
            dest_lang = "en"
        else:
            # Auto-detect
            src_lang = self.detect_language(text)
            if src_lang == "vi":
                dest_lang = "en"
            else:
                dest_lang = "vi"

        if src_lang == dest_lang:
            # Không cần dịch
            return {
                "source_text": text,
                "target_text": text,
                "source_lang": src_lang,
                "display_text": f"[{src_lang}] {text}"
            }

        try:
            translated = self.translate(text, dest=dest_lang)
        except Exception as e:
            logger.error(f"Lỗi dịch: {e}")
            translated = text

        return {
            "source_text": text,
            "target_text": translated,
            "source_lang": src_lang,
            "display_text": translated
        }
