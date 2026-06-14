import unittest

import numpy as np

from src.loopback_capture import LoopbackCapture


class LoopbackRealtimeTests(unittest.TestCase):
    def test_audio_to_pcm16_bytes_resamples_to_target_rate(self):
        capture = LoopbackCapture()
        audio = np.linspace(-0.5, 0.5, 4410, dtype=np.float32)

        pcm = capture._audio_to_pcm16_bytes(audio, source_rate=44100, target_rate=16000)

        self.assertIsInstance(pcm, bytes)
        self.assertEqual(len(pcm), 1600 * 2)

    def test_emit_result_preserves_interim_and_final_flag(self):
        capture = LoopbackCapture()
        seen = []
        capture.set_on_result(lambda text, is_final=True: seen.append((text, is_final)))

        capture._emit_result("hello", is_final=False)
        capture._emit_result("hello world", is_final=True)

        self.assertEqual(seen, [("hello", False), ("hello world", True)])


if __name__ == "__main__":
    unittest.main()
