import json
import logging
import os
from typing import Dict, List

import requests

logger = logging.getLogger(__name__)


class ReplyAssistant:
    def __init__(self, config_manager=None):
        self.config = config_manager

    def _api_key(self) -> str:
        key = os.getenv("QWEN_API_KEY", "").strip() or os.getenv("DASHSCOPE_API_KEY", "").strip()
        if not key and self.config:
            key = str(self.config.get("qwen_api_key", "")).strip()
        return key

    def _base_url(self) -> str:
        if self.config:
            cfg_url = str(self.config.get("qwen_base_url", "")).strip()
            if cfg_url:
                return cfg_url.rstrip("/")
        return "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

    def _model(self) -> str:
        if self.config:
            model = str(self.config.get("qwen_reply_model", "")).strip()
            if model:
                return model
        return "qwen-omni-turbo"

    def _chat(self, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 450) -> str:
        key = self._api_key()
        if not key:
            return ""
        url = f"{self._base_url()}/chat/completions"
        payload = {
            "model": self._model(),
            "stream": False,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=45)
            if resp.status_code >= 400:
                logger.warning("ReplyAssistant chat failed: %s", resp.text[:300])
                return ""
            obj = resp.json()
            return (((obj.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
        except Exception as ex:
            logger.warning("ReplyAssistant chat exception: %s", ex)
            return ""

    def generate_context_reply(
        self,
        latest_question: str,
        summaries: List[str],
        transcript_lines: List[str],
        user_role: str = "professional meeting participant",
    ) -> Dict[str, str]:
        summary_block = "\n".join(f"- {s}" for s in summaries if s.strip()) or "- No summary yet."
        transcript_block = "\n".join(transcript_lines[-20:]) or "(empty transcript)"
        prompt = (
            "You are a real-time meeting assistant.\n"
            f"Role: {user_role}\n"
            f"Latest question: {latest_question}\n"
            "Recent summaries:\n"
            f"{summary_block}\n"
            "Recent transcript excerpt:\n"
            f"{transcript_block}\n\n"
            "Return strict JSON with keys: english_reply, vietnamese_translation, speaking_script.\n"
            "english_reply must be concise, polite, professional (2-4 sentences).\n"
            "vietnamese_translation must preserve meaning.\n"
            "speaking_script is optional but natural for TTS."
        )
        content = self._chat(
            [
                {"role": "system", "content": "You only return JSON, no markdown."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.25,
            max_tokens=500,
        )
        if not content:
            return {"english_reply": "", "vietnamese_translation": "", "speaking_script": ""}

        try:
            cleaned = content.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`")
                cleaned = cleaned.replace("json", "", 1).strip()
            data = json.loads(cleaned)
            return {
                "english_reply": str(data.get("english_reply", "")).strip(),
                "vietnamese_translation": str(data.get("vietnamese_translation", "")).strip(),
                "speaking_script": str(data.get("speaking_script", "")).strip(),
            }
        except Exception:
            return {"english_reply": content, "vietnamese_translation": "", "speaking_script": ""}

