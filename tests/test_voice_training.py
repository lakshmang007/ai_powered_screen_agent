"""Voice training: learning, leave-one-out scoring and profile use (no microphone/API)."""

import json
import unittest
from unittest.mock import patch

import numpy as np
import speech_recognition as sr

from src.core import voice_training as vt


def fake_audio(seconds=1.0, level=2000, gap=None):
    """Tone with an optional silent gap (start, length) in seconds."""
    rate = 16000
    t = np.arange(int(rate * seconds))
    samples = (np.sin(t * 2 * np.pi * 220 / rate) * level)
    if gap:
        start, length = gap
        samples[int(start * rate):int((start + length) * rate)] = 0
    return sr.AudioData(samples.astype(np.int16).tobytes(), rate, 2)


class TestVoiceTraining(unittest.TestCase):
    def setUp(self):
        # A speaker whose "Mohith" Whisper hears as "Mohit", and "WhatsApp" sometimes as "what's up"
        def transcribe(audio, prompt):
            phrase = self.current
            heard = phrase.replace("Mohith", "Mohit")
            if "close" in phrase or "message" in phrase:
                heard = heard.replace("WhatsApp", "what's up")
            return heard
        self.trainer = vt.VoiceTrainer(["Mohith", "Rahul"], transcribe)
        self.tmp = vt.SAMPLES_DIR / "_unittest"
        self.trainer.session_dir = self.tmp
        self.trainer.set_noise_sample(fake_audio(level=40))
        for i, phrase in enumerate(self.trainer.phrases):
            self.current = phrase
            self.trainer.add_sample(i, fake_audio(level=3000, gap=(0.3, 0.4)))

    def test_learns_speaker_specific_corrections(self):
        report = self.trainer.finish(retranscribe=False)
        self.assertEqual(report["corrections"].get("mohit"), "Mohith")
        self.assertEqual(report["corrections"].get("what's up"), "WhatsApp")

    def test_leave_one_out_improves_accuracy(self):
        report = self.trainer.finish(retranscribe=False)
        self.assertLess(report["wer_after"], report["wer_before"])
        self.assertGreater(report["exact_after"], report["exact_before"])

    def test_calibration(self):
        report = self.trainer.finish(retranscribe=False)
        self.assertGreater(report["energy_threshold"], report["noise_rms"])
        self.assertLess(report["energy_threshold"], report["speech_rms"])
        self.assertAlmostEqual(report["typical_pause"], 0.4, delta=0.1)
        self.assertGreaterEqual(report["pause_threshold"], 0.8)

    def test_never_rewrites_ordinary_english(self):
        samples = [{"phrase": "send it to Rahul", "heard": "send it two Rahul"}]
        self.assertEqual(vt.learn_corrections(samples, vt.vocabulary_for(["Rahul"])), {})

    def test_profile_is_saved_and_applied(self):
        self.trainer.finish(retranscribe=False)
        path = self.tmp / "profile.json"
        self.trainer.save(path)
        profile = json.loads(path.read_text(encoding="utf-8"))
        from src.core.indian_english_voice_processor import IndianEnglishVoiceProcessor as V
        v = V.__new__(V)
        v.voice_profile = profile
        self.assertEqual(v._apply_phonetic_corrections("send hi to Mohit on what's up"),
                         "send hi to Mohith on WhatsApp")


if __name__ == "__main__":
    unittest.main()
