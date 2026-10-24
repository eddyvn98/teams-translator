"""Qwen Speech-to-Text via DashScope OpenAI-compatible chat/completions."""
import io
import json
import base64
import logging
import os
import wave

import numpy as np
import requests

logger = logging.getLogger(__name__)
"""Qwen Speech-to-Text via DashScope OpenAI-compatible chat/completions."""
import io
import json
import base64
import logging
import os
import wave

import numpy as np
import requests

logger = logging.getLogger(__name__)


class QwenSTT:
    def __init__(self, config_manager=None):
        self.config = config_manager

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

    def _model(self) -> str:
        if self.config:
            cfg_model = str(self.config.get("qwen_stt_model", "")).strip()
            if cfg_model:
                return cfg_model
        return os.getenv("QWEN_STT_MODEL", "iic/SenseVoiceSmall")

    @staticmethod
    def has_energy(audio: np.ndarray, threshold: float = 0.005) -> bool:
        if audio is None or len(audio) == 0:
            return False
        rms = float(np.sqrt(np.mean(np.square(audio, dtype=np.float32))))
        return rms >= threshold

    @staticmethod
    def _to_wav_bytes(audio: np.ndarray, sample_rate: int) -> bytes:
        pcm = np.clip(audio, -1.0, 1.0)
        pcm16 = (pcm * 32767.0).astype(np.int16)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(int(sample_rate))
            wf.writeframes(pcm16.tobytes())
        return buf.getvalue()

    def transcribe_audio(self, audio: np.ndarray, sample_rate: int, language: str = "en") -> str:
        wav_bytes = self._to_wav_bytes(audio.astype(np.float32, copy=False), sample_rate)
        url = f"{self._base_url()}/audio/transcriptions"
        headers = {}
        key = self._api_key()
        if key:
            headers["Authorization"] = f"Bearer {key}"

        lang = language
        if language:
            lang = "vi" if language.lower().startswith("vi") else "en"

        files = {
            "file": ("audio.wav", wav_bytes, "audio/wav")
        }
        data = {
            "model": self._model(),
            "language": lang,
        }

        logger.info(f"[ASR_STT] calling endpoint={url} model={data['model']} language={data['language']}")
        try:
            resp = requests.post(url, headers=headers, files=files, data=data, timeout=20)
            if resp.status_code >= 400:
                raise RuntimeError(f"ASR Server error {resp.status_code}: {resp.text}")
            obj = resp.json()
            return obj.get("text", "").strip()
        except Exception as e:
            logger.error(f"ASR transcription request failed: {e}")
            raise e

    def summarize_text(self, text: str) -> str:
        key = self._api_key()
        if not key or not text or not text.strip():
            return ""
        url = f"{self._base_url()}/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "qwen-omni-turbo",
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Tom tat transcript cuoc hop bang tieng Viet, ngan gon, de doc nhanh. "
                        "Tra ve 3-6 gach dau dong: van de chinh, quyet dinh, hanh dong tiep theo."
                    ),
                },
                {
                    "role": "user",
                    "content": text[-8000:],
                },
            ],
            "temperature": 0.2,
            "max_tokens": 300,
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=45)
            if resp.status_code >= 400:
                return ""
            obj = resp.json()
            return ((obj.get("choices", [{}])[0].get("message", {}) or {}).get("content", "") or "").strip()
        except Exception:
            return ""
