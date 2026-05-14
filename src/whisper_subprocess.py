"""
Whisper Subprocess Server — Chạy faster-whisper trong process riêng
để tránh crash với PyQt5.

Giao thức: stdin nhận audio bytes (raw float32 mono), stdout trả text.
"""
import sys
import numpy as np
import json
import os

def main():
    import logging
    logging.basicConfig(level=logging.WARNING)

    backend = os.environ.get("STT_BACKEND", "faster_whisper").strip().lower()
    model = None
    speech_client = None
    speech = None

    if backend == "google_cloud":
        try:
            from google.cloud import speech as gspeech
            speech = gspeech
            speech_client = gspeech.SpeechClient()
            logging.warning("Using Google Cloud Speech-to-Text backend")
        except Exception as e:
            logging.warning(f"Google Cloud STT unavailable, fallback faster-whisper: {e}")
            backend = "faster_whisper"

    if backend == "faster_whisper":
        from faster_whisper import WhisperModel
        model_name = os.environ.get("FW_MODEL", "base.en")
        model = WhisperModel(model_name, device="cpu", compute_type="int8")

    while True:
        try:
            # Đọc header: 4 bytes cho sample_rate, 4 bytes cho num_samples
            header = sys.stdin.buffer.read(8)
            if not header or len(header) < 8:
                break
            sample_rate = int.from_bytes(header[:4], 'little')
            num_samples = int.from_bytes(header[4:8], 'little')

            # Đọc audio data
            audio_bytes = sys.stdin.buffer.read(num_samples * 4)  # float32 = 4 bytes
            if not audio_bytes or len(audio_bytes) < num_samples * 4:
                break

            audio = np.frombuffer(audio_bytes, dtype=np.float32)
            if audio.size == 0:
                result = json.dumps({"text": "", "ok": True})
                sys.stdout.buffer.write(len(result).to_bytes(4, 'little'))
                sys.stdout.buffer.write(result.encode('utf-8'))
                sys.stdout.buffer.flush()
                continue

            # Chuẩn hóa biên độ để tăng ổn định khi âm lượng loopback nhỏ.
            peak = float(np.max(np.abs(audio)))
            if peak > 1e-6:
                audio = np.clip(audio / peak, -1.0, 1.0).astype(np.float32, copy=False)

            if backend == "google_cloud" and speech_client is not None and speech is not None:
                # Google Cloud STT expects LINEAR16 PCM; resample to 16k for accuracy/cost.
                target_sr = 16000
                if sample_rate != target_sr:
                    try:
                        from scipy.signal import resample_poly
                        audio16 = resample_poly(audio, target_sr, sample_rate).astype(np.float32, copy=False)
                    except Exception:
                        # Lightweight fallback resample
                        x_old = np.linspace(0, 1, num=len(audio), endpoint=False)
                        x_new = np.linspace(0, 1, num=int(len(audio) * target_sr / sample_rate), endpoint=False)
                        audio16 = np.interp(x_new, x_old, audio).astype(np.float32, copy=False)
                else:
                    audio16 = audio

                pcm16 = np.clip(audio16, -1.0, 1.0)
                pcm16 = (pcm16 * 32767.0).astype(np.int16).tobytes()

                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=target_sr,
                    language_code="en-US",
                    model="latest_long",
                    enable_automatic_punctuation=True,
                    use_enhanced=True,
                )
                audio_req = speech.RecognitionAudio(content=pcm16)
                resp = speech_client.recognize(config=config, audio=audio_req)
                text = " ".join([r.alternatives[0].transcript for r in resp.results if r.alternatives]).strip()
            else:
                segments, info = model.transcribe(
                    audio,
                    language="en",
                    beam_size=5,
                    best_of=5,
                    vad_filter=True,
                    vad_parameters=dict(
                        min_silence_duration_ms=500,
                        threshold=0.35,
                    ),
                    condition_on_previous_text=False,
                    no_speech_threshold=0.4,
                    temperature=0.0,
                )
                text = " ".join(s.text for s in segments).strip()

            # Trả kết quả
            result = json.dumps({"text": text, "ok": True})
            sys.stdout.buffer.write(len(result).to_bytes(4, 'little'))
            sys.stdout.buffer.write(result.encode('utf-8'))
            sys.stdout.buffer.flush()

        except (BrokenPipeError, EOFError):
            break
        except Exception as e:
            try:
                result = json.dumps({"text": "", "ok": False, "error": str(e)})
                sys.stdout.buffer.write(len(result).to_bytes(4, 'little'))
                sys.stdout.buffer.write(result.encode('utf-8'))
                sys.stdout.buffer.flush()
            except:
                break

if __name__ == "__main__":
    main()
