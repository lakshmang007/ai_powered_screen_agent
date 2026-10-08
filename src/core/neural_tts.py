"""
Neural text-to-speech (Microsoft Edge online voices via edge-tts) with an MP3
player built on the Windows MCI API, so playback can be stopped mid-sentence.

Default voice is en-GB-RyanNeural, a British male voice close to JARVIS in
Iron Man. Override with JARVIS_VOICE in .env (e.g. en-GB-ThomasNeural).
Synthesised audio is cached on disk, so repeated lines play instantly.
"""

import os
import re
import time
import ctypes
import asyncio
import hashlib
import logging
import threading
from pathlib import Path
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    edge_tts = None
    HAS_EDGE_TTS = False

CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "tts_cache"
DEFAULT_VOICE = "en-GB-RyanNeural"


def split_sentences(text: str) -> List[str]:
    """Split into sentences so the first one can play while the next is synthesised."""
    parts = re.split(r'(?<=[.!?;])\s+', text.strip())
    merged: List[str] = []
    for part in parts:
        # Keep very short fragments ("Done.") together with what follows
        if merged and len(merged[-1]) < 25:
            merged[-1] = f"{merged[-1]} {part}"
        else:
            merged.append(part)
    return [p for p in merged if p.strip()]


class NeuralVoice:
    def __init__(self, voice: Optional[str] = None, rate: Optional[str] = None, pitch: Optional[str] = None):
        self.voice = voice or os.getenv("JARVIS_VOICE", DEFAULT_VOICE)
        self.rate = rate or os.getenv("JARVIS_VOICE_RATE", "+8%")
        self.pitch = pitch or os.getenv("JARVIS_VOICE_PITCH", "-2Hz")
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._mci = ctypes.windll.winmm.mciSendStringW
        self._alias_counter = 0

    # ---------------------------------------------------------------- synthesis
    def _cache_path(self, text: str) -> Path:
        key = hashlib.sha1(f"{self.voice}|{self.rate}|{self.pitch}|{text}".encode("utf-8")).hexdigest()[:20]
        return CACHE_DIR / f"{key}.mp3"

    def synthesize(self, text: str, timeout: float = 8.0) -> Optional[Path]:
        """Return an MP3 file for `text` (from cache or freshly synthesised)."""
        path = self._cache_path(text)
        if path.exists() and path.stat().st_size > 0:
            return path
        tmp = path.with_suffix(".part")

        async def run():
            communicate = edge_tts.Communicate(text, self.voice, rate=self.rate, pitch=self.pitch)
            await asyncio.wait_for(communicate.save(str(tmp)), timeout=timeout)

        try:
            asyncio.run(run())
            os.replace(tmp, path)
            return path
        except Exception as e:
            logger.warning(f"Neural voice synthesis failed ({type(e).__name__}: {e})")
            try:
                tmp.unlink()
            except OSError:
                pass
            return None

    # ---------------------------------------------------------------- playback
    def _cmd(self, command: str) -> str:
        buf = ctypes.create_unicode_buffer(128)
        self._mci(command, buf, 128, 0)
        return buf.value

    def play(self, path: Path, should_stop: Callable[[], bool]) -> bool:
        """Play an MP3; returns False if stopped early."""
        self._alias_counter += 1
        alias = f"jarvis{self._alias_counter}"
        self._cmd(f'open "{path}" type mpegvideo alias {alias}')
        self._cmd(f"play {alias}")
        finished = True
        try:
            time.sleep(0.05)
            while self._cmd(f"status {alias} mode") == "playing":
                if should_stop():
                    self._cmd(f"stop {alias}")
                    finished = False
                    break
                time.sleep(0.03)
        finally:
            self._cmd(f"close {alias}")
        return finished

    def speak(self, text: str, should_stop: Callable[[], bool]) -> bool:
        """Speak `text` sentence by sentence, synthesising the next sentence while
        the current one plays. Returns False if synthesis failed (caller falls back)."""
        sentences = split_sentences(text)
        if not sentences:
            return True

        current = self.synthesize(sentences[0])
        if current is None:
            return False

        for i in range(len(sentences)):
            # Start synthesising the next sentence in the background
            upcoming = {}
            worker = None
            if i + 1 < len(sentences):
                worker = threading.Thread(
                    target=lambda s=sentences[i + 1]: upcoming.__setitem__("path", self.synthesize(s)),
                    daemon=True)
                worker.start()
            if current is None or not self.play(current, should_stop):
                return True  # stopped, or a later sentence failed: treat as handled
            if worker is None:
                break
            worker.join(timeout=10)
            current = upcoming.get("path")
        return True


def prune_cache(max_files: int = 400):
    """Keep the cache from growing without bound (oldest files go first)."""
    try:
        files = sorted(CACHE_DIR.glob("*.mp3"), key=lambda p: p.stat().st_mtime)
        for p in files[:-max_files]:
            p.unlink()
    except OSError:
        pass
