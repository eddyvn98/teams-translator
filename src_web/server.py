"""
FastAPI Server for Teams Translator Web (Google AI Studio Live Translate style)
Provides real-time WebSocket audio streaming, translation, meeting history, and AI reply assistant.
"""

import asyncio
import base64
import json
import logging
import os
import sys
import time
import uuid
from collections import OrderedDict
from pathlib import Path
from typing import Optional

import urllib.parse
import urllib.request

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config_manager import ConfigManager
from src.translator import Translator
from src.qwen_stt import QwenSTT
from src.reply_assistant import ReplyAssistant
from src.meeting_store import MeetingStore
from src.text_to_speech import TextToSpeech
from src.tts_client import TtsClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("TeamsTranslatorWeb")

app = FastAPI(title="Teams Translator Web API", version="2.0.0")

# CORS setup for Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core singletons
config_mgr = ConfigManager()
translator = Translator(config_mgr)
qwen_stt = QwenSTT(config_mgr)
reply_assistant = ReplyAssistant(config_mgr)
tts_engine = TextToSpeech(config_mgr)

# Active web connections tracking
active_web_clients: set[WebSocket] = set()
main_event_loop: Optional[asyncio.AbstractEventLoop] = None


def _on_web_tts_client_speak(text: str, audio_bytes: bytes = None):
    """Callback triggered when mobile speech arrives via dich.vivutrade.io.vn."""
    logger.info(f"[Web Server TTS] Received speech request: text='{text}', has_audio={bool(audio_bytes)}")
    # If running on a machine with local audio hardware, play locally as well
    if audio_bytes:
        try:
            tts_engine.play_wav_bytes(audio_bytes, wait=False)
        except Exception as e:
            logger.debug(f"[Web Server TTS] Local play_wav_bytes skipped: {e}")
    elif text:
        try:
            tts_engine.speak(text, wait=False)
        except Exception as e:
            logger.debug(f"[Web Server TTS] Local speak skipped: {e}")

    if (text or audio_bytes) and main_event_loop and main_event_loop.is_running():
        asyncio.run_coroutine_threadsafe(_notify_web_clients(text, audio_bytes=audio_bytes), main_event_loop)


async def _notify_web_clients(text: str, audio_bytes: bytes = None):
    """Notify active browser tabs about incoming speech from phone, including audio payload and Vietnamese translation."""
    try:
        clean_text = (text or "").strip()
        audio_b64 = None
        if audio_bytes:
            try:
                audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
            except Exception as e:
                logger.warning(f"[Web Server TTS] Failed to base64 encode audio: {e}")

        translated_text = ""
        if clean_text:
            loop = asyncio.get_event_loop()
            try:
                translated_text = await loop.run_in_executor(
                    None, lambda: translator.translate(clean_text, dest="vi", src="en")
                )
            except Exception as tr_err:
                logger.warning(f"[Web Server TTS] Remote speech translation error: {tr_err}")
                translated_text = ""

            meeting_store.append_transcript(
                source_lang="en",
                source_text=f"📱 {clean_text}",
                translated_text=translated_text,
            )

        msg = {
            "type": "remote_speech",
            "id": str(uuid.uuid4())[:8],
            "source": f"📱 {clean_text}" if clean_text else "",
            "translated": translated_text,
            "src_lang": "en",
            "target_lang": "vi",
            "is_final": True,
            "timestamp": time.time(),
            "audio_base64": audio_b64,
        }

        for ws in list(active_web_clients):
            try:
                await ws.send_json(msg)
            except Exception:
                pass
    except Exception as e:
        logger.error(f"[Web Server TTS] Error broadcasting to web clients: {e}")


tts_client = TtsClient(config_manager=config_mgr, callback=_on_web_tts_client_speak)


@app.on_event("startup")
async def on_startup():
    global main_event_loop
    main_event_loop = asyncio.get_event_loop()
    logger.info("[Web Server] Starting TTS WebSocket client connected to ASR server...")
    tts_client.start()


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("[Web Server] Stopping TTS WebSocket client...")
    tts_client.stop()


# Active meeting store
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
current_meeting_id = f"meeting_{int(time.time())}"
meeting_store = MeetingStore(DATA_DIR, current_meeting_id)
meeting_store.register_session(meeting_id=current_meeting_id, display_name="Live Session")


# Models for REST API
class ConfigUpdateRequest(BaseModel):
    target_language: Optional[str] = None
    source_language: Optional[str] = None
    asr_base_url: Optional[str] = None
    asr_api_key: Optional[str] = None
    qwen_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    system_instruction: Optional[str] = None
    model_name: Optional[str] = None


class ReplyRequest(BaseModel):
    context: str
    instruction: Optional[str] = ""


class SummarizeRequest(BaseModel):
    text: str


class TranslateRequest(BaseModel):
    text: str
    source_lang: Optional[str] = "en"
    target_lang: Optional[str] = "vi"


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "time": time.time(),
        "meeting_id": meeting_store.meeting_id,
        "asr_url": qwen_stt._base_url(),
    }


@app.get("/api/config")
async def get_config():
    return {
        "target_language": config_mgr.get("target_language", "vi"),
        "source_language": config_mgr.get("source_language", "en"),
        "asr_base_url": qwen_stt._base_url(),
        "asr_api_key_masked": (qwen_stt._api_key()[:6] + "..." + qwen_stt._api_key()[-4:]) if qwen_stt._api_key() else "",
        "google_api_key_masked": (translator._get_google_api_key()[:6] + "...") if translator._get_google_api_key() else "",
        "model": qwen_stt._model(),
        "system_instruction": config_mgr.get("system_instruction", "Dịch chính xác theo ngữ cảnh hội thoại, tự nhiên, chuẩn văn phong hội họp."),
        "echo_target_language": config_mgr.get("echo_target_language", False),
    }


@app.post("/api/config")
async def update_config(req: ConfigUpdateRequest):
    if req.target_language is not None:
        config_mgr.set("target_language", req.target_language)
    if req.source_language is not None:
        config_mgr.set("source_language", req.source_language)
    if req.asr_base_url is not None:
        config_mgr.set("qwen_base_url", req.asr_base_url)
        os.environ["ASR_BASE_URL"] = req.asr_base_url
    if req.asr_api_key is not None and req.asr_api_key.strip():
        config_mgr.set("qwen_api_key", req.asr_api_key.strip())
        os.environ["ASR_API_KEY"] = req.asr_api_key.strip()
    if req.google_api_key is not None and req.google_api_key.strip():
        config_mgr.set("google_api_key", req.google_api_key.strip())
        os.environ["GOOGLE_API_KEY"] = req.google_api_key.strip()
    if req.system_instruction is not None:
        config_mgr.set("system_instruction", req.system_instruction)
    if req.model_name is not None:
        config_mgr.set("qwen_stt_model", req.model_name)
    config_mgr.save()
    return {"status": "ok", "message": "Settings updated"}


@app.post("/api/translate")
async def translate_text(req: TranslateRequest):
    if not req.text.strip():
        return {"original": "", "translated": ""}
    translated = translator.translate(req.text, dest=req.target_lang or "vi", src=req.source_lang or "en")
    return {
        "original": req.text,
        "translated": translated,
        "source_lang": req.source_lang,
        "target_lang": req.target_lang,
    }


def _split_text_for_tts(text: str, max_chars: int = 150) -> list[str]:
    """Split long text into sentence/clause chunks under max_chars for Google TTS."""
    clean = text.strip()
    if len(clean) <= max_chars:
        return [clean]

    import re
    raw_sentences = re.split(r"([.?!;\n]+)", clean)
    merged_sentences = []
    i = 0
    while i < len(raw_sentences):
        part = raw_sentences[i]
        punct = raw_sentences[i + 1] if i + 1 < len(raw_sentences) else ""
        full_sentence = (part + punct).strip()
        if full_sentence:
            merged_sentences.append(full_sentence)
        i += 2

    chunks = []
    current = ""
    for sentence in merged_sentences:
        if len(current) + len(sentence) + (1 if current else 0) <= max_chars:
            current = f"{current} {sentence}".strip() if current else sentence
        else:
            if current:
                chunks.append(current)
                current = ""
            if len(sentence) > max_chars:
                words = sentence.split()
                sub = ""
                for w in words:
                    if len(w) > max_chars:
                        if sub:
                            chunks.append(sub)
                            sub = ""
                        for j in range(0, len(w), max_chars):
                            chunks.append(w[j : j + max_chars])
                    elif len(sub) + len(w) + 1 <= max_chars:
                        sub = f"{sub} {w}".strip() if sub else w
                    else:
                        if sub:
                            chunks.append(sub)
                        sub = w
                if sub:
                    current = sub
            else:
                current = sentence
    if current.strip():
        chunks.append(current.strip())

    return [c for c in chunks if any(char.isalnum() for char in c)] or [clean[:max_chars]]


@app.get("/api/tts")
async def text_to_speech(text: str = "", lang: str = "en"):
    """Generate high-quality natural TTS audio (MP3) for English or Vietnamese."""
    text = text.strip()
    if not text:
        return Response(status_code=400, content="Empty text")
    if len(text) > 1000:
        return Response(status_code=400, content="Text exceeds maximum length of 1000 characters")

    tl = "en" if lang.lower().startswith("en") else ("vi" if lang.lower().startswith("vi") else lang)

    cache_key = (text, tl)
    if hasattr(app.state, "tts_cache") and cache_key in app.state.tts_cache:
        app.state.tts_cache.move_to_end(cache_key)
        return Response(content=app.state.tts_cache[cache_key], media_type="audio/mpeg")

    try:
        chunks = _split_text_for_tts(text, max_chars=150)
        loop = asyncio.get_event_loop()

        def _fetch_all_chunks() -> bytes:
            audio_buffer = bytearray()
            for chunk in chunks:
                url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={urllib.parse.quote(chunk)}&tl={tl}&client=tw-ob"
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Referer": "https://translate.google.com/",
                    },
                )
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    audio_buffer.extend(resp.read())
            return bytes(audio_buffer)

        audio_bytes = await loop.run_in_executor(None, _fetch_all_chunks)

        if not hasattr(app.state, "tts_cache"):
            app.state.tts_cache = OrderedDict()
        if len(app.state.tts_cache) >= 200:
            app.state.tts_cache.popitem(last=False)
        app.state.tts_cache[cache_key] = audio_bytes

        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"TTS generation error: {e}")
        return Response(status_code=502, content=f"TTS service unavailable: {e}")


@app.post("/api/reply-assistant")
async def get_reply_suggestions(req: ReplyRequest):
    if not req.context.strip():
        return {"suggestions": []}
    try:
        context_items = [{"source": req.context, "translated": ""}]
        reply = reply_assistant.generate_context_reply(
            context_items=context_items,
            custom_instruction=req.instruction or "Gợi ý 3 câu trả lời lịch sự, thông minh, ngắn gọn."
        )
        # Parse suggestions into list of lines
        lines = [line.strip().lstrip("-*0123456789. ") for line in (reply or "").split("\n") if line.strip()]
        return {"suggestions": lines[:4] if lines else [reply]}
    except Exception as e:
        logger.error(f"Reply Assistant error: {e}")
        return {"suggestions": [], "error": str(e)}


@app.post("/api/summarize")
async def summarize_meeting(req: SummarizeRequest):
    if not req.text.strip():
        return {"summary": "Không có nội dung để tóm tắt."}
    try:
        summary = qwen_stt.summarize_text(req.text)
        return {"summary": summary or "Chưa thể tóm tắt đoạn hội thoại này."}
    except Exception as e:
        logger.error(f"Summarize error: {e}")
        return {"summary": f"Lỗi khi tóm tắt: {e}"}


@app.get("/api/history")
async def get_meeting_history():
    recent = meeting_store.get_recent_transcripts(limit=100)
    return {"transcripts": recent, "meeting_id": meeting_store.meeting_id}


@app.post("/api/session/new")
async def new_session():
    global current_meeting_id
    current_meeting_id = f"meeting_{int(time.time())}"
    meeting_store.set_meeting(current_meeting_id)
    meeting_store.register_session(meeting_id=current_meeting_id, display_name=f"Session {time.strftime('%H:%M %d/%m')}")
    return {"status": "ok", "meeting_id": current_meeting_id}


# Real-time WebSocket streaming with QwenRealtimeSTT (Same as src_minimal/start_minimal.bat)
class AudioStreamManager:
    """
    Manages audio streaming using QwenRealtimeSTT (WebSocket direct to ASR server),
    matching the exact caption creation and translation pipeline of start_minimal.bat.
    """
    def __init__(self, ws: WebSocket, loop: asyncio.AbstractEventLoop):
        self.ws = ws
        self.loop = loop
        self.source_lang = "en"
        self.target_lang = "vi"
        self.current_sentence_id = str(uuid.uuid4())[:8]

        # Connect to QwenRealtimeSTT directly
        self.realtime_stt = None
        self._init_realtime_stt()

        # Fallback buffer state if realtime unavailable
        self.audio_buffer = bytearray()
        self.sample_rate = 16000
        self.bytes_per_sample = 2
        self.chunk_threshold = int(self.sample_rate * self.bytes_per_sample * 2.2)
        self.overlap_bytes = int(self.sample_rate * self.bytes_per_sample * 0.3)
        self.prev_overlap = bytearray()
        self.is_processing = False
        self._lock = asyncio.Lock()
        self.active_sentence_words = []
        self.last_partial_translate_at = 0.0
        self.last_partial_translation = ""
        self.last_partial_source = ""

    def _init_realtime_stt(self):
        try:
            try:
                from src_minimal.qwen_realtime_stt import QwenRealtimeSTT
            except ImportError:
                from src.qwen_realtime_stt import QwenRealtimeSTT

            self.realtime_stt = QwenRealtimeSTT(
                config_mgr,
                on_text_received=self._on_realtime_stt_result
            )
            self.realtime_stt.start(sample_rate=16000)
            logger.info("[AudioStreamManager] QwenRealtimeSTT connected successfully (100% parity with start_minimal)!")
        except Exception as e:
            logger.warning(f"[AudioStreamManager] Realtime STT unavailable, using smart REST fallback: {e}")
            self.realtime_stt = None

    def _on_realtime_stt_result(self, text: str, is_final: bool):
        if not text or not text.strip():
            return
        clean_text = text.strip()
        # Schedule async coroutine on main event loop
        asyncio.run_coroutine_threadsafe(
            self._handle_realtime_text(clean_text, is_final),
            self.loop
        )

    async def _handle_realtime_text(self, text: str, is_final: bool):
        try:
            if not is_final:
                # Store partial streaming transcription in source language
                self.last_partial_source = text
                now = time.time()
                if len(text.split()) >= 3 and (now - self.last_partial_translate_at > 0.4):
                    self.last_partial_translate_at = now
                    try:
                        part_trans = await self.loop.run_in_executor(
                            None,
                            translator.translate,
                            text,
                            self.target_lang,
                            self.source_lang
                        )
                        if part_trans:
                            self.last_partial_translation = part_trans
                    except Exception:
                        pass

                # Live draft interim
                await self.ws.send_json({
                    "type": "sentence",
                    "id": self.current_sentence_id,
                    "source": text,
                    "translated": self.last_partial_translation,
                    "src_lang": self.source_lang,
                    "target_lang": self.target_lang,
                    "is_final": False,
                    "timestamp": time.time(),
                })
            else:
                self.last_partial_translate_at = 0.0
                self.last_partial_translation = ""
                prev_source = getattr(self, "last_partial_source", "").strip()
                self.last_partial_source = ""

                # When sentence is finalized:
                # The custom ASR server (with client=windows) sends the Vietnamese translation directly in `text`
                detected = translator.detect_language(text)

                if self.source_lang == "en" and detected == "vi":
                    # Remote ASR server returned the Vietnamese translation directly
                    translated = text
                    # The English source was streamed in partial chunks
                    if prev_source and translator.detect_language(prev_source) != "vi":
                        source_text = prev_source
                    else:
                        # Fallback if no partial was captured: translate Vietnamese back to English
                        source_text = await self.loop.run_in_executor(
                            None,
                            translator.translate,
                            text,
                            "en",
                            "vi"
                        )
                elif self.source_lang == "vi" and detected == "en":
                    translated = text
                    if prev_source and translator.detect_language(prev_source) == "vi":
                        source_text = prev_source
                    else:
                        source_text = await self.loop.run_in_executor(
                            None,
                            translator.translate,
                            text,
                            "vi",
                            "en"
                        )
                else:
                    source_text = text
                    translated = await self.loop.run_in_executor(
                        None,
                        translator.translate,
                        text,
                        self.target_lang,
                        self.source_lang
                    )

                if source_text:
                    source_text = source_text[0].upper() + source_text[1:]
                if translated:
                    translated = translated[0].upper() + translated[1:]

                logger.info(f"[MINIMAL PARITY FINAL] {self.source_lang}: '{source_text}' -> {self.target_lang}: '{translated}'")
                await self.ws.send_json({
                    "type": "sentence",
                    "id": self.current_sentence_id,
                    "source": source_text,
                    "translated": translated or "",
                    "src_lang": self.source_lang,
                    "target_lang": self.target_lang,
                    "is_final": True,
                    "timestamp": time.time(),
                })
                meeting_store.append_transcript(
                    source_lang=self.source_lang,
                    source_text=source_text,
                    translated_text=translated or "",
                )
                # Advance to next sentence
                self.current_sentence_id = str(uuid.uuid4())[:8]
        except Exception as e:
            logger.error(f"Error in realtime text handler: {e}")

    async def feed_pcm(self, pcm_bytes: bytes):
        if self.realtime_stt and self.realtime_stt._is_running:
            self.realtime_stt.send_audio(pcm_bytes)
            return

        # Fallback to smart REST chunking if WebSocket ASR is unavailable
        self.audio_buffer.extend(pcm_bytes)
        if len(self.audio_buffer) >= self.chunk_threshold and not self.is_processing:
            asyncio.create_task(self._process_chunk())

    def stop(self):
        if self.realtime_stt:
            try:
                self.realtime_stt.stop()
            except Exception:
                pass
            self.realtime_stt = None

    async def _process_chunk(self):
        async with self._lock:
            if len(self.audio_buffer) < int(self.sample_rate * self.bytes_per_sample * 0.8):
                return

            raw_bytes = bytes(self.prev_overlap) + bytes(self.audio_buffer)
            # Keep overlap for next slice
            if len(self.audio_buffer) > self.overlap_bytes:
                self.prev_overlap = bytearray(self.audio_buffer[-self.overlap_bytes:])
            else:
                self.prev_overlap = bytearray()
            self.audio_buffer.clear()

        # Convert to numpy float32 for energy & STT
        audio_int16 = np.frombuffer(raw_bytes, dtype=np.int16)
        audio_float = audio_int16.astype(np.float32) / 32768.0

        # Voice Activity Detection (RMS threshold)
        has_voice = QwenSTT.has_energy(audio_float, threshold=0.003)
        if not has_voice:
            self.silence_count += 1
            # If silence for > 1.2s and we have an ongoing sentence, finalize it!
            if self.silence_count >= 2 and self.active_sentence_words:
                await self._finalize_active_sentence()
            return

        self.silence_count = 0
        self.last_speech_time = time.time()

        try:
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                None,
                qwen_stt.transcribe_audio,
                audio_float,
                self.sample_rate,
                self.source_lang
            )

            if not text or not text.strip():
                return

            clean_chunk = text.strip()
            # Ignore lone fillers like 'uh', 'um', 'ah'
            if clean_chunk.lower() in ["uh", "um", "ah", "hmm", "er", "oh"]:
                return

            logger.info(f"Chunk STT: '{clean_chunk}'")

            # Append chunk to active sentence words
            # Deduplicate overlap at boundary if needed
            self._append_chunk_to_sentence(clean_chunk)
            full_sentence = " ".join(self.active_sentence_words).strip()
            if not full_sentence:
                return

            # Capitalize first letter
            full_sentence = full_sentence[0].upper() + full_sentence[1:]

            # Check if sentence is complete:
            # 1. Ends with punctuation (. ? !)
            # 2. Or reached 14+ words
            word_count = len(full_sentence.split())
            ends_with_punct = full_sentence[-1] in [".", "?", "!", ":", ";"]
            is_final = ends_with_punct or (word_count >= 14)

            # Translate accumulated sentence so far
            translated = await loop.run_in_executor(
                None,
                translator.translate,
                full_sentence,
                self.target_lang,
                self.source_lang
            )

            # Emit sentence update to WebSocket
            await self.ws.send_json({
                "type": "sentence",
                "id": self.current_sentence_id,
                "source": full_sentence,
                "translated": translated or "",
                "src_lang": self.source_lang,
                "target_lang": self.target_lang,
                "is_final": is_final,
                "timestamp": time.time(),
            })

            if is_final:
                # Store finalized sentence to meeting database
                meeting_store.append_transcript(
                    source_lang=self.source_lang,
                    source_text=full_sentence,
                    translated_text=translated or "",
                )
                logger.info(f"[FINAL SENTENCE] EN: '{full_sentence}' -> VI: '{translated}'")
                # Reset for next sentence
                self.active_sentence_words = []
                self.current_sentence_id = str(uuid.uuid4())[:8]

        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            await self.ws.send_json({"type": "error", "message": str(e)})

    def _append_chunk_to_sentence(self, chunk: str):
        new_words = chunk.split()
        if not self.active_sentence_words:
            self.active_sentence_words.extend(new_words)
            return

        # Check for 1-3 word overlap at boundary
        overlap_found = 0
        for k in range(min(4, len(new_words), len(self.active_sentence_words)), 0, -1):
            tail = [w.lower().strip(".,?!") for w in self.active_sentence_words[-k:]]
            head = [w.lower().strip(".,?!") for w in new_words[:k]]
            if tail == head:
                overlap_found = k
                break

        if overlap_found > 0:
            self.active_sentence_words.extend(new_words[overlap_found:])
        else:
            self.active_sentence_words.extend(new_words)

    async def _finalize_active_sentence(self):
        if not self.active_sentence_words:
            return
        full_sentence = " ".join(self.active_sentence_words).strip()
        self.active_sentence_words = []
        old_id = self.current_sentence_id
        self.current_sentence_id = str(uuid.uuid4())[:8]

        if not full_sentence:
            return
        full_sentence = full_sentence[0].upper() + full_sentence[1:]
        if full_sentence[-1] not in [".", "?", "!"]:
            full_sentence += "."

        loop = asyncio.get_event_loop()
        translated = await loop.run_in_executor(
            None,
            translator.translate,
            full_sentence,
            self.target_lang,
            self.source_lang
        )

        logger.info(f"[PAUSE FINALIZED] EN: '{full_sentence}' -> VI: '{translated}'")
        await self.ws.send_json({
            "type": "sentence",
            "id": old_id,
            "source": full_sentence,
            "translated": translated or "",
            "src_lang": self.source_lang,
            "target_lang": self.target_lang,
            "is_final": True,
            "timestamp": time.time(),
        })
        meeting_store.append_transcript(
            source_lang=self.source_lang,
            source_text=full_sentence,
            translated_text=translated or "",
        )


@app.websocket("/ws/stream")
async def websocket_stream_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_web_clients.add(websocket)
    logger.info("WebSocket client connected")
    loop = asyncio.get_event_loop()
    manager = AudioStreamManager(websocket, loop)

    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                logger.info("WebSocket client disconnected cleanly")
                break
            if "bytes" in message and message["bytes"]:
                # Binary audio chunk received (16kHz 16-bit mono PCM)
                await manager.feed_pcm(message["bytes"])
            elif "text" in message and message["text"]:
                try:
                    data = json.loads(message["text"])
                    msg_type = data.get("type")
                    if msg_type == "config":
                        manager.source_lang = data.get("source_lang", "en")
                        manager.target_lang = data.get("target_lang", "vi")
                        logger.info(f"Stream configured: src={manager.source_lang} -> tgt={manager.target_lang}")
                        await websocket.send_json({
                            "type": "status",
                            "message": f"Configured {manager.source_lang} -> {manager.target_lang}"
                        })
                    elif msg_type == "text_input":
                        # User typed text directly to simulate input
                        input_text = data.get("text", "").strip()
                        if input_text:
                            loop = asyncio.get_event_loop()
                            translated = await loop.run_in_executor(
                                None,
                                translator.translate,
                                input_text,
                                manager.target_lang,
                                manager.source_lang
                            )
                            await websocket.send_json({
                                "type": "sentence",
                                "id": str(uuid.uuid4())[:8],
                                "source": input_text,
                                "translated": translated,
                                "src_lang": manager.source_lang,
                                "target_lang": manager.target_lang,
                                "is_final": True,
                                "timestamp": time.time(),
                            })
                            await websocket.send_json({
                                "type": "transcript",
                                "text": input_text,
                                "lang": manager.source_lang,
                                "timestamp": time.time(),
                            })
                            await websocket.send_json({
                                "type": "translation",
                                "original": input_text,
                                "translated": translated,
                                "src_lang": manager.source_lang,
                                "target_lang": manager.target_lang,
                                "timestamp": time.time(),
                            })
                            meeting_store.append_transcript(
                                source_lang=manager.source_lang,
                                source_text=input_text,
                                translated_text=translated,
                            )
                except json.JSONDecodeError:
                    pass
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket unexpected error: {e}")
    finally:
        active_web_clients.discard(websocket)
        manager.stop()


# Serve compiled frontend if exists
dist_path = PROJECT_ROOT / "web" / "dist"
if dist_path.exists():
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src_web.server:app", host="127.0.0.1", port=8000, reload=True)
