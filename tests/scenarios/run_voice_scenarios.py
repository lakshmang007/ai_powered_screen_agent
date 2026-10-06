"""
Voice end-to-end: synthesized speech -> real speech recognition -> real JARVIS.

Each "utterance" is rendered with a Windows voice and passed through the same
recognition path the microphone uses (Groq Whisper / Google + corrections),
then executed by JARVIS on the real desktop. Same safety patches as
run_jarvis_scenarios.py: WhatsApp sends are dry-run, URLs are recorded.

Usage:  python tests/scenarios/run_voice_scenarios.py [contact]
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_jarvis_scenarios as harness  # applies the safety patches
import stt_benchmark as bench
import speech_recognition as sr
import win32com.client

import jarvis
from main import register_default_handlers
from src.core.nlp_processor import NLPProcessor
from src.core.screen_agent import ScreenAgent
from src.automation.task_engine import TaskEngine
from src.automation.handlers.whatsapp_handler import WhatsAppHandler
from src.core.indian_english_voice_processor import IndianEnglishVoiceProcessor

CONTACT = sys.argv[1] if len(sys.argv) > 1 else "Mohith"
VOICE = win32com.client.Dispatch("SAPI.SpVoice").GetVoices().Item(0)


class SpokenVoice(harness.ScriptedVoice):
    """listen_once() returns what the real recognizer makes of synthesized speech."""

    def __init__(self):
        super().__init__()
        self.stt = IndianEnglishVoiceProcessor.__new__(IndianEnglishVoiceProcessor)
        self.stt.use_whisper = False
        self.stt.language = "en-IN"
        self.stt.recognizer = sr.Recognizer()
        self.stt._init_stt_settings()
        self.heard = []

    def recognize(self, phrase):
        audio = sr.AudioData(bench.synthesize(phrase, VOICE)[44:], 16000, 2)
        text = self.stt._recognize_with_fallback(audio)
        text = self.stt._apply_phonetic_corrections(text.strip()) if text else None
        self.heard.append((phrase, text))
        return text

    def listen_once(self, *args, **kwargs):
        return self.recognize(self.answers.pop(0)) if self.answers else None


def main():
    voice = SpokenVoice()
    print(f"Speech recognition: {voice.stt.stt_provider}")
    nlp = NLPProcessor(use_ai=True)
    agent = ScreenAgent()
    engine = TaskEngine(agent)
    register_default_handlers(engine, agent, whatsapp_confirm=jarvis.make_voice_confirm(voice))
    context = jarvis.ContextMemory()
    wa = lambda: WhatsAppHandler(agent)._whatsapp_window()

    scenarios = [
        ("open WhatsApp", [], lambda r: (r and wa() is not None, "WhatsApp window open")),
        ("close WhatsApp", [], lambda r: (r and wa() is None, "WhatsApp closed to tray")),
        ("open WhatsApp", [], lambda r: (r and wa() is not None, "WhatsApp back from tray")),
        (f"send yeah I am coming to {CONTACT} on WhatsApp", ["yes"],
         lambda r: (r and "dry run" in voice.spoken[-1].lower(), voice.spoken[-1])),
        (f"open WhatsApp go to {CONTACT} chat and type and send I will be late", ["yes"],
         lambda r: (r and "dry run" in voice.spoken[-1].lower(), voice.spoken[-1])),
        ("what are you doing", [], lambda r: (r and "listening" in voice.spoken[-1].lower(), voice.spoken[-1])),
        ("minimize all windows", [], lambda r: (r, "minimized")),
    ]

    passed = 0
    for utterance, answers, check in scenarios:
        voice.answers = list(answers)
        start = time.time()
        heard = voice.recognize(utterance)
        try:
            returned = jarvis.execute_jarvis_command(heard or "", nlp, engine, voice, None, context, None) if heard else False
            time.sleep(1.0)
            ok, detail = check(returned)
        except Exception as e:
            ok, detail = False, f"EXCEPTION {type(e).__name__}: {e}"
        passed += bool(ok)
        replies = [h for p, h in voice.heard[-len(answers):]] if answers else []
        print(f"{'PASS' if ok else 'FAIL'}  {time.time() - start:5.1f}s  said: {utterance!r}\n"
              f"        heard: {heard!r}{f'  answer heard: {replies}' if replies else ''}\n        {detail}")
    print(f"\n{passed}/{len(scenarios)} voice scenarios passed")
    return 0 if passed == len(scenarios) else 1


if __name__ == "__main__":
    sys.exit(main())
