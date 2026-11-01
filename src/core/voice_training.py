"""
Voice enrollment ("training") for JARVIS speech recognition.

Whisper itself can't be fine-tuned here, so we personalise everything around it
from ~20 phrases the user reads aloud:

1. Microphone calibration  - noise floor vs. speech level -> energy threshold
2. Speaking rhythm         - longest natural pause inside a sentence -> pause threshold
3. Vocabulary              - the user's contacts / app names go into Whisper's prompt
4. Learned corrections     - words Whisper repeatedly mishears *for this speaker*
                             (only for vocabulary words, so normal English is never rewritten)

Accuracy is reported before vs. after using leave-one-out evaluation: each
recording is corrected only with rules learned from the *other* recordings.

The profile is saved to data/voice_profile.json and loaded by the voice processor.
Recordings are kept locally in data/voice_samples/ (git-ignored).
"""

import os
import re
import json
import time
import wave
import difflib
import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "data" / "voice_profile.json"
SAMPLES_DIR = ROOT / "data" / "voice_samples"

BASE_VOCABULARY = ["JARVIS", "WhatsApp", "Notepad", "VS Code", "Chrome", "YouTube", "Gmail", "LinkedIn",
                   "Spotify", "Dolby Access", "GitHub", "macro", "minimize", "Windows key"]

PHRASE_TEMPLATES = [
    "JARVIS",
    "JARVIS, status report",
    "open WhatsApp",
    "close WhatsApp",
    "send I am coming to {name1} on WhatsApp",
    "open WhatsApp and go to {name1} chat",
    "message {name2} on WhatsApp that I will be late",
    "click type a message",
    "open notepad and type hello world",
    "search for Python tutorials on YouTube",
    "minimize all windows",
    "press the Windows key",
    "go to GitHub dot com",
    "open Visual Studio Code",
    "what is fifteen percent of two hundred and forty",
    "what are you doing",
    "stop",
    "that's all",
    "yes send it",
    "goodbye JARVIS",
]

_NUMBER_WORDS = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
                 "seven": "7", "eight": "8", "nine": "9", "ten": "10", "fifteen": "15", "forty": "40",
                 "two hundred and forty": "240", "two hundred forty": "240"}


# --------------------------------------------------------------------------- text utils
def normalize(text: str) -> List[str]:
    """Lower-case words for comparison; ignores punctuation, casing, I'm/I am, number words."""
    text = (text or "").lower()
    text = text.replace("i'm", "i am").replace("that's", "that is").replace("what's", "what is")
    text = text.replace("visual studio code", "vs code").replace("vscode", "vs code")
    text = re.sub(r"\bdot com\b", ".com", text).replace(".com", " com")
    for words, digits in sorted(_NUMBER_WORDS.items(), key=lambda kv: -len(kv[0])):
        text = re.sub(rf"\b{words}\b", digits, text)
    text = text.replace("%", " percent")
    return re.findall(r"[a-z0-9]+", text)


def word_error_rate(reference: str, hypothesis: str) -> float:
    ref, hyp = normalize(reference), normalize(hypothesis)
    d = np.zeros((len(ref) + 1, len(hyp) + 1), dtype=int)
    d[:, 0] = range(len(ref) + 1)
    d[0, :] = range(len(hyp) + 1)
    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (ref[i - 1] != hyp[j - 1]))
    return float(d[len(ref), len(hyp)]) / max(len(ref), 1)


def build_phrases(names: List[str]) -> List[str]:
    names = [n.strip() for n in names if n.strip()] or ["Mohith"]
    name1, name2 = names[0], names[1] if len(names) > 1 else names[0]
    phrases = [p.format(name1=name1, name2=name2) for p in PHRASE_TEMPLATES]
    for extra in names[2:5]:
        phrases.insert(6, f"open WhatsApp and go to {extra} chat")
    return phrases


def vocabulary_for(names: List[str], extra: List[str] = ()) -> List[str]:
    seen, out = set(), []
    for w in [*BASE_VOCABULARY, *names, *extra]:
        if w and w.lower() not in seen:
            seen.add(w.lower())
            out.append(w)
    return out


def learn_corrections(samples: List[Dict], vocabulary: List[str]) -> Dict[str, str]:
    """Map misheard word sequences -> intended vocabulary words.

    Only learns when the intended words contain a vocabulary term (a name, an app),
    so it never rewrites ordinary English like "to" -> "two"."""
    vocab_words = {w.lower() for term in vocabulary for w in term.split()}
    vocab_casing = {w.lower(): w for term in vocabulary for w in term.split()}
    corrections: Dict[str, str] = {}
    for s in samples:
        if not s.get("heard"):
            continue
        ref_raw = re.findall(r"[A-Za-z0-9']+", s["phrase"])
        hyp_raw = re.findall(r"[A-Za-z0-9']+", s["heard"])
        ref, hyp = [w.lower() for w in ref_raw], [w.lower() for w in hyp_raw]
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=hyp, b=ref, autojunk=False).get_opcodes():
            if tag != "replace" or (i2 - i1) > 3 or (j2 - j1) > 3:
                continue
            wrong, right = hyp[i1:i2], ref[j1:j2]
            if not any(w in vocab_words for w in right):
                continue
            if any(w in vocab_words for w in wrong) and normalize(" ".join(wrong)) != normalize(" ".join(right)):
                continue  # don't turn one known word into another
            if normalize(" ".join(wrong)) == normalize(" ".join(right)):
                continue  # only casing/punctuation differs
            corrections[" ".join(wrong)] = " ".join(vocab_casing.get(w, w) for w in right)
    return corrections


def apply_corrections(text: str, corrections: Dict[str, str]) -> str:
    for wrong, right in sorted(corrections.items(), key=lambda kv: -len(kv[0])):
        text = re.sub(rf"\b{re.escape(wrong)}\b", right, text, flags=re.IGNORECASE)
    return text


# --------------------------------------------------------------------------- audio utils
def audio_to_array(audio) -> Tuple[np.ndarray, int]:
    raw = audio.get_raw_data(convert_rate=16000, convert_width=2)
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32), 16000


def frame_rms(samples: np.ndarray, rate: int, frame_ms: int = 30) -> np.ndarray:
    n = int(rate * frame_ms / 1000)
    usable = len(samples) // n * n
    if usable == 0:
        return np.zeros(0)
    frames = samples[:usable].reshape(-1, n)
    return np.sqrt(np.mean(frames ** 2, axis=1))


def longest_internal_pause(samples: np.ndarray, rate: int, threshold: float) -> float:
    """Longest silence (seconds) between the first and last speech frame."""
    rms = frame_rms(samples, rate)
    speech = np.where(rms > threshold)[0]
    if len(speech) < 2:
        return 0.0
    gaps = np.diff(speech) - 1
    return float(gaps.max()) * 0.03 if len(gaps) else 0.0


def save_wav(path: Path, audio):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(audio.get_raw_data(convert_rate=16000, convert_width=2))


# --------------------------------------------------------------------------- the trainer
class VoiceTrainer:
    """Drives one enrollment session. UI-agnostic: a GUI or a test feeds it audio."""

    def __init__(self, names: List[str], transcribe: Callable, extra_vocabulary: List[str] = ()):
        """
        Args:
            names: contact names the user will say (e.g. ["Mohith", "Rahul"])
            transcribe: fn(audio, prompt) -> text  (Whisper with a given vocabulary prompt)
        """
        self.names = [n.strip() for n in names if n.strip()]
        self.phrases = build_phrases(self.names)
        self.vocabulary = vocabulary_for(self.names, list(extra_vocabulary))
        self.transcribe = transcribe
        self.samples: List[Dict] = []
        self.noise_rms: Optional[float] = None
        self.session_dir = SAMPLES_DIR / datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # The prompt the app used before training vs. after (with the user's names)
    @staticmethod
    def default_prompt() -> str:
        from .indian_english_voice_processor import IndianEnglishVoiceProcessor
        return IndianEnglishVoiceProcessor._build_vocabulary_prompt(include_profile=False)

    def personal_prompt(self) -> str:
        return ("Voice commands for a desktop assistant called JARVIS, e.g. 'open WhatsApp', "
                f"'send I am coming to {self.names[0] if self.names else 'Mohith'} on WhatsApp', "
                "'click type a message'. Words: " + ", ".join(self.vocabulary[:60]) + ".")

    def set_noise_sample(self, audio):
        samples, _ = audio_to_array(audio)
        rms = frame_rms(samples, 16000)
        self.noise_rms = float(np.percentile(rms, 90)) if len(rms) else 50.0

    def add_sample(self, index: int, audio) -> Dict:
        """Record the result for phrase `index`; returns the sample (incl. what was heard)."""
        phrase = self.phrases[index]
        path = self.session_dir / f"{index:02d}.wav"
        save_wav(path, audio)
        samples, rate = audio_to_array(audio)
        rms = frame_rms(samples, rate)
        try:
            heard = self.transcribe(audio, self.default_prompt()) or ""
        except Exception as e:
            heard = ""
            print(f"Transcription failed: {e}")
        sample = {
            "index": index, "phrase": phrase, "heard": heard, "wav": str(path),
            "wer": word_error_rate(phrase, heard),
            "speech_rms": float(np.percentile(rms, 90)) if len(rms) else 0.0,
            "duration": len(samples) / rate,
        }
        self.samples = [s for s in self.samples if s["index"] != index] + [sample]
        self.samples.sort(key=lambda s: s["index"])
        return sample

    def finish(self, retranscribe: bool = True, progress: Callable[[int, int], None] = None) -> Dict:
        """Compute the profile and the before/after report."""
        import speech_recognition as sr
        usable = [s for s in self.samples if s.get("heard") is not None]

        # 1. Mic calibration
        noise = self.noise_rms or 50.0
        speech = float(np.median([s["speech_rms"] for s in usable])) if usable else 1000.0
        # Between the room noise and the speaking level, leaning towards noise so soft words still count
        energy = float(np.clip(noise * 1.8 + (speech - noise) * 0.08, noise * 1.3, max(speech * 0.5, noise * 1.5)))

        # 2. Speaking rhythm
        pauses = []
        for s in usable:
            with wave.open(s["wav"], "rb") as w:
                data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
            pauses.append(longest_internal_pause(data, 16000, energy))
        typical_pause = float(np.percentile(pauses, 90)) if pauses else 0.6
        pause_threshold = float(np.clip(typical_pause + 0.45, 0.8, 2.0))

        # 3+4. Re-transcribe with the personal vocabulary, then leave-one-out corrections
        prompt = self.personal_prompt()
        if retranscribe and prompt != self.default_prompt():
            for n, s in enumerate(usable, 1):
                with wave.open(s["wav"], "rb") as w:
                    audio = sr.AudioData(w.readframes(w.getnframes()), 16000, 2)
                try:
                    s["heard_personal"] = self.transcribe(audio, prompt) or ""
                except Exception:
                    s["heard_personal"] = s["heard"]
                if progress:
                    progress(n, len(usable))
        for s in usable:
            s.setdefault("heard_personal", s["heard"])

        rows = []
        for s in usable:
            others = [{"phrase": o["phrase"], "heard": o["heard_personal"]} for o in usable if o is not s]
            loo = learn_corrections(others, self.vocabulary)
            after = apply_corrections(s["heard_personal"], loo)
            rows.append({"phrase": s["phrase"], "before": s["heard"], "after": after,
                         "wer_before": word_error_rate(s["phrase"], s["heard"]),
                         "wer_after": word_error_rate(s["phrase"], after)})

        corrections = learn_corrections([{"phrase": s["phrase"], "heard": s["heard_personal"]} for s in usable],
                                        self.vocabulary)
        n = max(len(rows), 1)
        report = {
            "samples": len(rows),
            "wer_before": sum(r["wer_before"] for r in rows) / n,
            "wer_after": sum(r["wer_after"] for r in rows) / n,
            "exact_before": int(sum(r["wer_before"] == 0 for r in rows)),
            "exact_after": int(sum(r["wer_after"] == 0 for r in rows)),
            "noise_rms": noise, "speech_rms": speech,
            "energy_threshold": energy, "pause_threshold": pause_threshold,
            "typical_pause": typical_pause,
            "corrections": corrections,
            "rows": rows,
        }
        self.profile = {
            "created": datetime.datetime.now().isoformat(timespec="seconds"),
            "energy_threshold": round(energy, 1),
            "pause_threshold": round(pause_threshold, 2),
            "vocabulary": self.vocabulary,
            "names": self.names,
            "corrections": corrections,
            "stats": {k: report[k] for k in ("samples", "wer_before", "wer_after", "exact_before", "exact_after")},
        }
        self.report = report
        return report

    def save(self, path: Path = PROFILE_PATH) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.profile, indent=2, ensure_ascii=False), encoding="utf-8")
        (self.session_dir / "report.json").write_text(json.dumps(self.report, indent=2, ensure_ascii=False),
                                                      encoding="utf-8")
        return path


def load_profile(path: Path = PROFILE_PATH) -> Optional[Dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
