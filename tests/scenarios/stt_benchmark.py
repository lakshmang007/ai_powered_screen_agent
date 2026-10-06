"""
Speech-to-text benchmark: Google (free web API) vs Groq Whisper.

Synthesises command phrases with the installed Windows voices (no microphone
needed), adds background noise, and compares word error rate and latency.

Usage:  python tests/scenarios/stt_benchmark.py
"""

import os
import io
import re
import sys
import time
import wave
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

import speech_recognition as sr

PHRASES = [
    "close WhatsApp",
    "send yeah I am coming to Mohith on WhatsApp",
    "open WhatsApp go to Mohith chat and type and send I will be late",
    "click type a message",
    "open notepad and type hello world",
    "search for python tutorials on YouTube",
    "minimize all windows",
    "what are you doing",
    "go to github dot com",
    "play macro dolby atmos",
    "Jarvis open Visual Studio Code",
    "message Rahul on WhatsApp that the meeting is at five",
]


def synthesize(text, voice, rate=0):
    """Render `text` to 16 kHz mono WAV bytes with a SAPI voice."""
    import win32com.client
    path = os.path.join(tempfile.gettempdir(), "stt_bench.wav")
    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    fmt = win32com.client.Dispatch("SAPI.SpAudioFormat")
    fmt.Type = 18  # SAFT16kHz16BitMono
    stream.Format = fmt
    stream.Open(path, 3)
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    speaker.Voice = voice
    speaker.Rate = rate
    speaker.AudioOutputStream = stream
    speaker.Speak(text)
    stream.Close()
    with open(path, "rb") as f:
        return f.read()


def add_noise(wav_bytes, snr_db=15):
    """Mix in background noise (fan/room hum) at the given signal-to-noise ratio."""
    with wave.open(io.BytesIO(wav_bytes)) as w:
        params = w.getparams()
        samples = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
    rng = np.random.default_rng(0)
    noise = rng.normal(0, 1, len(samples)) + 0.5 * np.sin(np.arange(len(samples)) * 2 * np.pi * 120 / 16000)
    signal_power = np.mean(samples ** 2) or 1
    noise *= np.sqrt(signal_power / (10 ** (snr_db / 10)) / np.mean(noise ** 2))
    mixed = np.clip(samples + noise, -32768, 32767).astype(np.int16)
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setparams(params)
        w.writeframes(mixed.tobytes())
    return out.getvalue()


def norm(text):
    text = (text or "").lower().replace("visual studio code", "vscode").replace("vs code", "vscode")
    text = text.replace("dot com", ".com").replace("github.com", "github .com").replace("i'm", "i am")
    text = re.sub(r"\bfive\b", "5", text)
    return re.findall(r"[a-z0-9]+", text)


def wer(ref, hyp):
    r, h = norm(ref), norm(hyp)
    d = np.zeros((len(r) + 1, len(h) + 1), dtype=int)
    d[:, 0] = range(len(r) + 1)
    d[0, :] = range(len(h) + 1)
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (r[i - 1] != h[j - 1]))
    return d[len(r), len(h)] / max(len(r), 1)


def main():
    import win32com.client
    voices = win32com.client.Dispatch("SAPI.SpVoice").GetVoices()
    voice_list = [voices.Item(i) for i in range(voices.Count)]
    print("Voices:", ", ".join(v.GetDescription() for v in voice_list))

    from src.core.indian_english_voice_processor import IndianEnglishVoiceProcessor
    recognizer = sr.Recognizer()
    groq = IndianEnglishVoiceProcessor.__new__(IndianEnglishVoiceProcessor)  # use its STT helpers only
    groq._init_stt_settings()

    engines = {
        "google en-IN": lambda a: recognizer.recognize_google(a, language="en-IN"),
        "groq whisper": lambda a: groq._transcribe_with_groq(a),
    }
    totals = {name: [0.0, 0.0, 0, 0] for name in engines}  # wer sum, time sum, count, exact

    for voice in voice_list:
        for noisy in (False, True):
            for phrase in PHRASES:
                wav = synthesize(phrase, voice, rate=1)
                if noisy:
                    wav = add_noise(wav)
                audio = sr.AudioData(wav[44:], 16000, 2)
                row = []
                for name, fn in engines.items():
                    start = time.time()
                    try:
                        hyp = fn(audio) or ""
                    except sr.UnknownValueError:
                        hyp = ""
                    except Exception as e:
                        hyp = f"<error {type(e).__name__}>"
                    elapsed = time.time() - start
                    score = wer(phrase, hyp)
                    t = totals[name]
                    t[0] += score; t[1] += elapsed; t[2] += 1; t[3] += score == 0
                    row.append(f"{name}: {hyp!r} ({score:.0%})")
                if any("(0%)" not in r for r in row):
                    tag = f"{voice.GetDescription().split(' - ')[0]}{' +noise' if noisy else ''}"
                    print(f"  [{tag}] {phrase!r}\n      " + "\n      ".join(row))

    print("\nRESULTS")
    for name, (w, t, n, exact) in totals.items():
        print(f"  {name:13}  word error rate {w / n:6.1%}   exact {exact}/{n}   avg latency {t / n:.2f}s")


if __name__ == "__main__":
    main()
