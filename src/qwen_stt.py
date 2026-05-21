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
        key = os.getenv("QWEN_API_KEY", "").strip()
        if not key:
            key = os.getenv("DASHSCOPE_API_KEY", "").strip()
        if not key and self.config:
            key = str(self.config.get("qwen_api_key", "")).strip()
        return key

    def _base_url(self) -> str:
        if self.config:
            cfg_url = str(self.config.get("qwen_base_url", "")).strip()
            if cfg_url:
                return cfg_url.rstrip("/")
        return os.getenv(
            "QWEN_BASE_URL",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        ).rstrip("/")

    def _model(self) -> str:
        if self.config:
            cfg_model = str(self.config.get("qwen_stt_model", "")).strip()
            if cfg_model:
                return cfg_model
        return os.getenv("QWEN_STT_MODEL", "qwen3-asr-flash-realtime")

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

    @staticmethod
    def _fallback_model(model: str, status_code: int, body_text: str) -> str | None:
        if status_code == 500 and "internal_error" in (body_text or ""):
            if model == "qwen3-asr-flash-realtime":
                return "qwen3-asr-flash"
        return None

    def transcribe_audio(self, audio: np.ndarray, sample_rate: int, language: str = "en") -> str:
        key = self._api_key()
        if not key:
            raise RuntimeError("Thi?u QWEN_API_KEY (env ho?c config).")

        wav_bytes = self._to_wav_bytes(audio.astype(np.float32, copy=False), sample_rate)
        url = f"{self._base_url()}/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

        b64 = base64.b64encode(wav_bytes).decode("ascii")

        model_chain = [self._model()]
        if model_chain[0] != "qwen3-asr-flash":
            model_chain.append("qwen3-asr-flash")

        last_error = None
        for model in model_chain:
            logger.info(f"[QWEN_STT] calling model={model} endpoint={url}")
            payload = {
                "model": model,
                "stream": True,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_audio",
                                "input_audio": {
                                    "data": f"data:audio/wav;base64,{b64}",
                                    "format": "wav",
                                },
                            }
                        ],
                    }
                ],
                "modalities": ["text"],
                "translation_options": {
                    "source_lang": "en",
                    "target_lang": "vi",
                },
            }

            text_parts = []
            with requests.post(url, headers=headers, json=payload, timeout=20, stream=True) as resp:
                if resp.status_code >= 400:
                    body = resp.text[:400]
                    fallback = self._fallback_model(model, resp.status_code, body)
                    if fallback and fallback not in model_chain:
                        model_chain.append(fallback)
                        logger.warning(f"[QWEN_STT] model={model} l?i {resp.status_code}, fallback -> {fallback}")
                        continue
                    last_error = RuntimeError(f"Qwen STT l?i {resp.status_code}: {body}")
                    continue

                for raw_line in resp.iter_lines(decode_unicode=True):
                    if not raw_line:
                        continue
                    line = raw_line.strip()
                    if not line.startswith("data:"):
                        continue
                    chunk_data = line[5:].strip()
                    if chunk_data == "[DONE]":
                        break
                    try:
                        obj = json.loads(chunk_data)
                    except Exception:
                        continue
                    for choice in obj.get("choices", []):
                        delta = choice.get("delta", {}) or {}
                        content = delta.get("content")
                        if content:
                            text_parts.append(content)

            return "".join(text_parts).strip()

        if last_error:
            raise last_error
        raise RuntimeError("Qwen STT l?i kh?ng x?c ??nh.")

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
