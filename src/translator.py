"""
Translator module — Google Translate Anh ↔ Việt
"""
import logging
import os
import re
from collections import OrderedDict
import requests

logger = logging.getLogger(__name__)


class Translator:
    """Dịch Anh-Việt 2 chiều bằng Google Translate API (free, không cần key)."""

    def __init__(self, config_manager=None):
        self._translator = None
        self._fallback = None  # Tự fallback nếu Google lỗi
        self.config = config_manager
        self._missing_deep_translator_logged = False

        self._cache = OrderedDict()

    def _config_value(self, key: str, default=None):
        return self.config.get(key, default) if self.config else default

    def _timeout(self, key: str, default: float) -> float:
        try:
            return max(0.5, float(self._config_value(key, default)))
        except (TypeError, ValueError):
            return default

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").strip())

    def _cache_get(self, key: tuple) -> str | None:
        value = self._cache.get(key)
        if value is not None:
            self._cache.move_to_end(key)
        return value

    def _cache_set(self, key: tuple, value: str) -> None:
        if not value:
            return
        self._cache[key] = value
        self._cache.move_to_end(key)
        try:
            max_size = int(self._config_value("translation_cache_size", 256))
        except (TypeError, ValueError):
            max_size = 256
        while len(self._cache) > max(16, max_size):
            self._cache.popitem(last=False)

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
            resp = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=self._timeout("translation_google_timeout", 1.8),
            )
            if resp.status_code == 200:
                resp.encoding = "utf-8"
                data = resp.json()
                translated = "".join(seg[0] for seg in data[0] if seg[0])
                if translated:
                    logger.info("[MT] backend=google-gtx src=%s dest=%s", src, dest)
                    return translated
            logger.warning(f"Google Translate API trả về status {resp.status_code}")
        except Exception as e:
            logger.warning(f"Google Translate via requests lỗi: {e}")
        return None

    def _qwen_translate_en_vi(self, text: str) -> str | None:
        """Translate English -> Vietnamese via Qwen MT."""
        if not text or not text.strip():
            return ""

        key = os.getenv("QWEN_API_KEY", "").strip() or os.getenv("DASHSCOPE_API_KEY", "").strip()
        if not key and self.config:
            key = str(self.config.get("qwen_api_key", "")).strip()
        if not key:
            return None

        base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        if self.config:
            cfg_url = str(self.config.get("qwen_base_url", "")).strip()
            if cfg_url:
                base_url = cfg_url.rstrip("/")

        model = "qwen-mt-flash"
        if self.config:
            cfg_model = str(self.config.get("qwen_mt_model", "")).strip()
            if cfg_model:
                model = cfg_model
        model = os.getenv("QWEN_MT_MODEL", model).strip() or "qwen-mt-flash"

        payload = {
            "model": model,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": "Translate English to Vietnamese only. Return translation text only.",
                },
                {
                    "role": "user",
                    "content": text.strip(),
                },
            ],
            "temperature": 0.0,
        }

        try:
            resp = requests.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json=payload,
                timeout=self._timeout("translation_qwen_timeout", 4.0),
            )
            if resp.status_code >= 400:
                logger.warning("Qwen MT API status=%s body=%s", resp.status_code, resp.text[:300])
                return None
            obj = resp.json()
            translated = ((obj.get("choices", [{}])[0].get("message", {}) or {}).get("content", "") or "").strip()
            if translated:
                logger.info("[MT] backend=qwen model=%s src=en dest=vi", model)
            return translated or None
        except Exception as e:
            logger.warning("Qwen MT request lỗi: %s", e)
            return None

    def qwen_translate_stream(self, text: str, dest: str = "vi", src: str = "en"):
        """Translate text via Qwen MT in streaming mode (generator)."""
        if not text or not text.strip():
            yield ""
            return

        key = self._api_key()
        if not key:
            yield text
            return

        base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        if self.config:
            cfg_url = str(self.config.get("qwen_base_url", "")).strip()
            if cfg_url:
                base_url = cfg_url.rstrip("/")

        model = "qwen-mt-flash"
        if self.config:
            cfg_model = str(self.config.get("qwen_mt_model", "")).strip()
            if cfg_model:
                model = cfg_model
        model = os.getenv("QWEN_MT_MODEL", model).strip() or "qwen-mt-flash"

        src_full = "English" if src.lower() == "en" else "Vietnamese"
        dest_full = "Vietnamese" if dest.lower() == "vi" else "English"

        payload = {
            "model": model,
            "stream": True,
            "messages": [
                {
                    "role": "system",
                    "content": f"Translate {src_full} to {dest_full} only. Return translation text only.",
                },
                {
                    "role": "user",
                    "content": text.strip(),
                },
            ],
            "temperature": 0.0,
        }

        try:
            import json
            resp = requests.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json=payload,
                stream=True,
                timeout=self._timeout("translation_qwen_timeout", 4.0),
            )
            if resp.status_code >= 400:
                logger.warning("Qwen MT Stream API status=%s body=%s", resp.status_code, resp.text[:300])
                yield text
                return

            accumulated = ""
            for line in resp.iter_lines():
                if not line:
                    continue
                line_str = line.decode("utf-8").strip()
                if not line_str.startswith("data:"):
                    continue
                data_content = line_str[5:].strip()
                if data_content == "[DONE]":
                    break
                try:
                    obj = json.loads(data_content)
                    delta = obj.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if delta:
                        accumulated += delta
                        yield accumulated
                except Exception:
                    continue
            if not accumulated:
                yield text
        except Exception as e:
            logger.warning("Qwen MT Stream request error: %s", e)
            yield text

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
        """Translate text with cache, fast Google path, then Qwen fallback for EN->VI."""
        text = self._normalize_text(text)
        if not text:
            return ""

        if len(text.split()) <= 1 and len(text) <= 3:
            return text

        cache_key = (src, dest, text.lower())
        cached = self._cache_get(cache_key)
        if cached is not None:
            logger.info("[MT] backend=cache src=%s dest=%s", src, dest)
            return cached

        result = self._google_translate_via_requests(text, dest=dest, src=src)
        if result:
            self._cache_set(cache_key, result)
            return result

        translator_cls = self._get_translator()
        if translator_cls:
            try:
                result = translator_cls(source=src, target=dest).translate(text)
                if result:
                    logger.info("[MT] backend=google-deep-translator src=%s dest=%s", src, dest)
                    self._cache_set(cache_key, result)
                    return result
            except Exception as e:
                logger.warning(f"Lỗi deep-translator: {e}, thử Qwen fallback")

        if dest == "vi" and src in ("en", "auto"):
            qwen_result = self._qwen_translate_en_vi(text)
            if qwen_result:
                self._cache_set(cache_key, qwen_result)
                return qwen_result

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
            translated = self.translate(text, dest=dest_lang, src=src_lang)
        except Exception as e:
            logger.error(f"Lỗi dịch: {e}")
            translated = text

        return {
            "source_text": text,
            "target_text": translated,
            "source_lang": src_lang,
            "display_text": translated
        }

