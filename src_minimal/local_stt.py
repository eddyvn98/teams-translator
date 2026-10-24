"""
Local Speech-to-Text — dùng faster-whisper chạy trên GPU (CUDA)
Thay thế Google Web Speech API, giảm độ trễ từ ~7s xuống ~1-2s

Model: tiny.en (nhẹ, ~1GB VRAM, chính xác tốt cho họp hành)
Có thể đổi sang base.en / small.en nếu muốn chính xác hơn (tốn VRAM hơn)
"""

import logging
import numpy as np
from typing import Optional, Callable

logger = logging.getLogger(__name__)

# Lazy-load model singleton
_model = None
_model_name = None


def _get_model(model_name: str = "tiny.en", device: str = "cpu", compute_type: str = "int8"):
    """
    Load faster-whisper model (singleton).
    Model sẽ được cache sau lần load đầu tiên.
    """
    global _model, _model_name
    if _model is not None and _model_name == model_name:
        return _model

    logger.info(f"⏳ Đang tải mô hình faster-whisper '{model_name}'...")
    from faster_whisper import WhisperModel

    # auto: dùng CUDA nếu có, fallback CPU
    _model = WhisperModel(model_name, device=device, compute_type=compute_type)
    _model_name = model_name
    logger.info(f"✅ faster-whisper '{model_name}' đã sẵn sàng!")
    return _model


def transcribe(
    audio: np.ndarray,
    sample_rate: int = 16000,
    language: str = "en",
    model_name: str = "tiny.en",
) -> Optional[str]:
    """
    Nhận dạng giọng nói từ audio numpy array.

    Args:
        audio: numpy array float32, range [-1, 1], mono
        sample_rate: sample rate của audio (sẽ được resample nếu cần)
        language: mã ngôn ngữ ('en', 'vi', None = auto-detect)
        model_name: tên model ('tiny.en', 'base.en', 'small.en')

    Returns:
        text nếu nhận dạng được, None nếu không
    """
    try:
        model = _get_model(model_name)

        # faster-whisper xử lý audio float32, sample_rate 16000
        # Nếu sample_rate khác, nó tự resample internally
        segments, info = model.transcribe(
            audio,
            language=language,
            beam_size=1,          # Beam=1 cho tốc độ tối đa
            vad_filter=True,      # Bỏ qua khoảng im lặng
            vad_parameters=dict(
                min_silence_duration_ms=300,   # Im lặng 300ms = hết câu
                threshold=0.5,                  # Ngưỡng VAD
            ),
            condition_on_previous_text=False,  # Không dùng context để tránh lặp
            no_speech_threshold=0.6,            # Bỏ qua tạp âm
            temperature=0.0,                    # Deterministic
        )

        text = " ".join(seg.text for seg in segments).strip()
        if text:
            logger.debug(f"faster-whisper: '{text}' (lang={info.language}, prob={info.language_probability:.2f})")
            return text
        return None

    except Exception as e:
        logger.warning(f"faster-whisper lỗi: {e}")
        return None


def has_energy(audio: np.ndarray, threshold: float = 0.005) -> bool:
    """
    VAD đơn giản: kiểm tra xem audio có năng lượng không (có người nói không).
    """
    if len(audio) == 0:
        return False
    rms = np.sqrt(np.mean(audio ** 2))
    return rms > threshold
