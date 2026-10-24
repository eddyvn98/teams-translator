"""
Translator module — Google Translate Anh ↔ Việt
"""
import html
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
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
        })

    def _get_google_api_key(self) -> str:
        key = os.getenv("GOOGLE_API_KEY", "").strip() or os.getenv("GOOGLE_TRANSLATE_API_KEY", "").strip()
        if not key and self.config:
            key = str(self.config.get("google_api_key", "")).strip()
        return key

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

    def _google_translate_official(self, text: str, dest: str = "vi", src: str = "auto") -> str | None:
        """Dịch bằng Google Cloud Translation API chính thức nếu có API key."""
        key = self._get_google_api_key()
        if not key:
            return None
        try:
            import html
            url = "https://translation.googleapis.com/language/translate/v2"
            params = {
                "key": key,
                "q": text,
                "target": dest,
                "format": "text"
            }
            if src and src != "auto":
                params["source"] = src
            resp = self._session.post(url, data=params, timeout=self._timeout("translation_google_timeout", 3.0))
            if resp.status_code == 200:
                data = resp.json()
                translated = data.get("data", {}).get("translations", [{}])[0].get("translatedText", "")
                if translated:
                    translated = html.unescape(translated.strip())
                    logger.info("[MT] backend=google-cloud-official src=%s dest=%s", src, dest)
                    return translated
            logger.warning("Google Cloud Translation API trả về status %s: %s", resp.status_code, resp.text[:200])
        except Exception as e:
            logger.warning("Google Cloud Translation API lỗi: %s", e)
        return None

    def _google_translate_chrome_ext(self, text: str, dest: str = "vi", src: str = "auto") -> str | None:
        """Dịch bằng Google Chrome Extension endpoint (rất ít bị rate limit 429)."""
        try:
            import html
            url = "https://clients5.google.com/translate_a/t"
            params = {
                "client": "dict-chrome-ex",
                "sl": src,
                "tl": dest,
                "q": text,
            }
            resp = self._session.get(
                url,
                params=params,
                timeout=self._timeout("translation_google_timeout", 2.2),
            )
            if resp.status_code == 200:
                resp.encoding = "utf-8"
                data = resp.json()
                translated = ""
                if isinstance(data, list) and len(data) > 0:
                    if isinstance(data[0], list) and len(data[0]) > 0:
                        translated = "".join(str(seg[0]) for seg in data if isinstance(seg, list) and len(seg) > 0)
                    elif isinstance(data[0], str):
                        translated = "".join(data)
                elif isinstance(data, str):
                    translated = data
                if translated and translated.strip():
                    translated = html.unescape(translated.strip())
                    logger.info("[MT] backend=google-chrome-ext src=%s dest=%s", src, dest)
                    return translated
            elif resp.status_code == 429:
                logger.warning("Google Chrome-ext endpoint trả về status 429")
        except Exception as e:
            logger.debug("Google Chrome-ext lỗi: %s", e)
        return None

    def _google_translate_gtx(self, text: str, dest: str = "vi", src: str = "auto") -> str | None:
        """Dịch qua Google Translate GTX endpoint."""
        try:
            import html
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": src,
                "tl": dest,
                "dt": "t",
                "q": text,
            }
            resp = self._session.get(
                url,
                params=params,
                timeout=self._timeout("translation_google_timeout", 2.0),
            )
            if resp.status_code == 200:
                resp.encoding = "utf-8"
                data = resp.json()
                translated = "".join(seg[0] for seg in data[0] if seg[0])
                if translated:
                    translated = html.unescape(translated.strip())
                    logger.info("[MT] backend=google-gtx src=%s dest=%s", src, dest)
                    return translated
            elif resp.status_code == 429:
                logger.warning("Google Translate API trả về status 429")
        except Exception as e:
            logger.debug("Google Translate GTX lỗi: %s", e)
        return None

    def _google_translate_mobile_web(self, text: str, dest: str = "vi", src: str = "auto") -> str | None:
        """Dịch qua Google Translate mobile web (không phụ thuộc vào API endpoint bị 429)."""
        try:
            import html
            url = "https://translate.google.com/m"
            params = {
                "sl": src,
                "tl": dest,
                "q": text,
            }
            resp = self._session.get(
                url,
                params=params,
                timeout=self._timeout("translation_google_timeout", 2.5),
            )
            if resp.status_code == 200:
                resp.encoding = "utf-8"
                match = re.search(r'<div[^>]*class=["\']result-container["\'][^>]*>(.*?)</div>', resp.text, re.DOTALL)
                if match:
                    translated = html.unescape(match.group(1).strip())
                    if translated:
                        logger.info("[MT] backend=google-mobile-web src=%s dest=%s", src, dest)
                        return translated
        except Exception as e:
            logger.debug("Google Mobile Web lỗi: %s", e)
        return None

    def _deep_translator_translate(self, text: str, dest: str = "vi", src: str = "auto") -> str | None:
        """Dịch bằng deep-translator library."""
        translator_cls = self._get_translator()
        if translator_cls:
            try:
                result = translator_cls(source=src, target=dest).translate(text)
                if result and result.strip():
                    logger.info("[MT] backend=google-deep-translator src=%s dest=%s", src, dest)
                    return result.strip()
            except Exception as e:
                logger.debug("deep-translator lỗi: %s", e)
        return None

    def _google_translate_via_requests(self, text: str, dest: str = "vi", src: str = "auto") -> str | None:
        """Fallback tương thích hàm cũ: thử chrome-ext rồi gtx rồi mobile-web."""
        return (
            self._google_translate_chrome_ext(text, dest=dest, src=src)
            or self._google_translate_gtx(text, dest=dest, src=src)
            or self._google_translate_mobile_web(text, dest=dest, src=src)
        )

    def _qwen_translate_en_vi(self, text: str) -> str | None:
        """Translate English -> Vietnamese via Qwen MT (Disabled)."""
        return None

    def _get_deepseek_api_key(self) -> str:
        key = os.getenv("DEEPSEEK_API_KEY", "").strip() or os.getenv("DEEPSEEK_KEY", "").strip()
        if not key and self.config:
            key = str(self.config.get("deepseek_api_key", "")).strip()
        if not key:
            local_env = Path(__file__).resolve().parent.parent / ".env"
            if local_env.exists():
                try:
                    for line in local_env.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if line.startswith("DEEPSEEK_API_KEY=") or line.startswith("DEEPSEEK_KEY="):
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if val:
                                return val
                except Exception:
                    pass
        return key

    def _deepseek_translate(self, text: str, dest: str = "vi", src: str = "auto") -> str | None:
        """Dịch văn bản qua DeepSeek Chat API."""
        api_key = self._get_deepseek_api_key()
        if not api_key:
            return None

        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
        url = f"{base_url}/chat/completions"

        if src == "vi" and dest == "en":
            system_prompt = (
                "You are a real-time speech translator. "
                "Translate spoken Vietnamese into natural, everyday conversational American English. "
                "Use common colloquial American expressions, natural rhythm, and everyday phrasing (e.g. natural contractions like 'can't', 'it's', 'I'm'). "
                "Avoid stiff, formal, or textbook phrasing. "
                "Output ONLY the translated spoken English. Do not add quotes, brackets, or notes."
            )
        elif src in ("en", "auto") and dest == "vi":
            system_prompt = (
                "You are a real-time speech translator. "
                "Translate spoken English into natural, everyday conversational Vietnamese (văn nói tự nhiên, đời thường, thông dụng, dễ hiểu). "
                "Output ONLY the translated spoken Vietnamese. Do not add quotes, brackets, or notes."
            )
        else:
            sl_name = "Vietnamese" if src == "vi" else ("English" if src == "en" else src)
            tl_name = "American English" if dest == "en" else ("Vietnamese" if dest == "vi" else dest)
            system_prompt = f"Translate spoken text directly from {sl_name} to natural conversational {tl_name}. Output ONLY direct translation."

        model = os.getenv("DEEPSEEK_MODEL", "deepseek-flash").strip() or "deepseek-flash"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            "thinking": {"type": "disabled"},
            "temperature": 0.2,
            "max_tokens": 300,
        }
        try:
            resp = self._session.post(
                url,
                json=payload,
                headers=headers,
                timeout=self._timeout("translation_deepseek_timeout", 4.0),
            )
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices")
                if not choices or not isinstance(choices, list):
                    logger.warning("DeepSeek API returned empty or invalid choices list")
                    return None
                message = choices[0].get("message", {})
                content = message.get("content", "").strip()
                if content.startswith('"') and content.endswith('"') and len(content) > 2:
                    content = content[1:-1].strip()
                if content:
                    logger.info("[MT] backend=deepseek-api src=%s dest=%s", src, dest)
                    return content
            else:
                logger.warning("DeepSeek API status=%s: %s", resp.status_code, resp.text[:200])
        except Exception as e:
            logger.debug("DeepSeek API error: %s", e)
        return None

    def _mymemory_translate(self, text: str, dest: str = "vi", src: str = "auto") -> str | None:
        """Dịch qua MyMemory làm phương án dự phòng miễn phí."""
        try:
            from deep_translator import MyMemoryTranslator
            s_code = "vi-VN" if src == "vi" else ("en-GB" if src == "en" else src)
            t_code = "en-GB" if dest == "en" else ("vi-VN" if dest == "vi" else dest)
            result = MyMemoryTranslator(source=s_code, target=t_code).translate(text)
            if result and result.strip() and not result.lower().startswith("invalid"):
                logger.info("[MT] backend=mymemory src=%s dest=%s", src, dest)
                return result.strip()
        except Exception as e:
            logger.debug("MyMemory translation error: %s", e)
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
        """Translate text with cache, official Google API (if key), fast Google endpoints, then Qwen fallback."""
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

        # 1. Thử Google Cloud Translation API chính thức nếu người dùng cung cấp API key
        if self._get_google_api_key():
            result = self._google_translate_official(text, dest=dest, src=src)
            if result:
                self._cache_set(cache_key, result)
                return result

        # 2. Thử Google Chrome-ext (Dict-Chrome-Ex) - endpoint này hoạt động độc lập, rất hiếm khi bị 429
        result = self._google_translate_chrome_ext(text, dest=dest, src=src)
        if result:
            self._cache_set(cache_key, result)
            return result

        # 3. Thử Google GTX endpoint
        result = self._google_translate_gtx(text, dest=dest, src=src)
        if result:
            self._cache_set(cache_key, result)
            return result

        # 4. Thử Google Mobile Web scraping endpoint (không bị rate-limit như API)
        result = self._google_translate_mobile_web(text, dest=dest, src=src)
        if result:
            self._cache_set(cache_key, result)
            return result

        # 5. Thử DeepSeek API (Fallback thông minh, văn nói đời thường chuẩn tiếng Anh Mỹ / tiếng Việt)
        if self._get_deepseek_api_key():
            result = self._deepseek_translate(text, dest=dest, src=src)
            if result:
                self._cache_set(cache_key, result)
                return result

        # 6. Thử deep-translator library
        result = self._deep_translator_translate(text, dest=dest, src=src)
        if result:
            self._cache_set(cache_key, result)
            return result

        # 7. MyMemory fallback (miễn phí không qua Google)
        result = self._mymemory_translate(text, dest=dest, src=src)
        if result:
            self._cache_set(cache_key, result)
            return result

        # 8. Qwen MT fallback nếu dịch sang tiếng Việt
        if dest == "vi" and src in ("en", "auto"):
            qwen_result = self._qwen_translate_en_vi(text)
            if qwen_result:
                self._cache_set(cache_key, qwen_result)
                return qwen_result

        logger.warning("[MT] Tất cả các backend dịch Google/DeepSeek/MyMemory đều không thành công cho: '%s'", text[:60])
        return ""

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
            translated = ""

        final_translated = translated if translated else text
        return {
            "source_text": text,
            "target_text": final_translated,
            "source_lang": src_lang,
            "display_text": final_translated
        }

