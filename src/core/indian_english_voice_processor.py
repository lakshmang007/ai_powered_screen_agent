"""
Enhanced Voice Processor optimized for Indian English.
Features:
- Better recognition for Indian accents
- Longer listening duration (doesn't exit quickly)
- Multiple recognition engines with fallback
- Continuous listening with better timeout handling
"""

import os
import sys
import logging
from typing import Optional, Callable
import threading
import queue
import re
import time

# Speech recognition
try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False
    sr = None

# Text-to-speech
try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False
    pyttsx3 = None

# OpenAI for enhancement
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    OpenAI = None


class IndianEnglishVoiceProcessor:
    """
    Voice processor optimized for Indian English with:
    1. Better accent recognition
    2. Longer listening duration
    3. Multiple recognition engines
    4. Continuous listening without quick exits
    """
    
    def __init__(self,
                 openai_api_key: Optional[str] = None,
                 use_whisper: bool = False,
                 use_gpt_enhancement: bool = False,
                 wake_word: str = "byte",
                 language: str = "en-IN"):  # Indian English
        """
        Initialize Indian English voice processor.
        
        Args:
            openai_api_key: OpenAI API key (optional)
            use_whisper: Use OpenAI Whisper (needs credits)
            use_gpt_enhancement: Use GPT for enhancement (needs credits)
            wake_word: Wake word to activate
            language: Language code (en-IN for Indian English)
        """
        self.logger = logging.getLogger(__name__)
        self.wake_word = wake_word.lower()
        self.language = language
        self.use_whisper = use_whisper and HAS_OPENAI
        self.use_gpt_enhancement = use_gpt_enhancement and HAS_OPENAI
        self._init_stt_settings()
        
        # Setup OpenAI if available
        self.openai_client = None
        if HAS_OPENAI and (use_whisper or use_gpt_enhancement):
            api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
            if api_key:
                try:
                    self.openai_client = OpenAI(api_key=api_key)
                    self.logger.info("OpenAI client initialized")
                except Exception as e:
                    self.logger.warning(f"OpenAI initialization failed: {e}")
                    self.use_whisper = False
                    self.use_gpt_enhancement = False
        
        # Initialize speech recognition
        if HAS_SPEECH_RECOGNITION:
            self.recognizer = sr.Recognizer()

            # End-of-speech: 1.2s of silence ends a command. 2.0s made every command
            # feel slow; much below 1s cuts people off mid-sentence.
            self.recognizer.energy_threshold = 300  # Lower for softer speech
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = float(os.getenv("VOICE_PAUSE_SECONDS", "1.2"))
            self.recognizer.phrase_threshold = 0.2  # ignore clicks/pops shorter than this
            self.recognizer.non_speaking_duration = min(0.8, self.recognizer.pause_threshold)
            self._last_calibration = 0.0
            
            try:
                self.microphone = sr.Microphone()
                self.logger.info("Microphone initialized")

                # Try to calibrate for ambient noise (with timeout protection)
                try:
                    with self.microphone as source:
                        self.logger.info("Calibrating for ambient noise (2 seconds)...")
                        self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    self._last_calibration = time.time()
                    self.logger.info("Speech recognition initialized for Indian English")
                except Exception as calib_error:
                    self.logger.warning(f"Calibration failed (will use defaults): {calib_error}")
                    # Continue anyway - calibration is optional

            except Exception as e:
                self.logger.error(f"Microphone initialization failed: {e}")
                self.logger.error("Please check if microphone is connected and not in use by another application")
                self.microphone = None
        else:
            self.recognizer = None
            self.microphone = None
        
        # Text-to-speech runs on ONE dedicated thread that owns the engine.
        # COM objects (SAPI) and pyttsx3 engines are bound to the thread that created
        # them; calling them from the JARVIS/GUI worker threads used to fail silently.
        # Windows SAPI is preferred because it can be interrupted mid-sentence.
        self.tts_queue = queue.Queue()
        self.tts_thread = None
        self.tts_running = False
        self.tts_voice_id = None
        self.tts_rate = 160
        self.tts_volume = 0.9
        self.tts_engine = None          # "sapi" / "pyttsx3" once the worker is ready
        self.sapi_speaker = None        # kept for backwards compatibility (worker-owned)
        self._purge_requested = threading.Event()
        self._speaking = threading.Event()
        self._tts_ready = threading.Event()

        if sys.platform == "win32" or HAS_TTS:
            self.tts_running = True
            self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
            self.tts_thread.start()
            self._tts_ready.wait(timeout=5)
            if not self.tts_engine:
                self.logger.error("No text-to-speech engine available")
        
        # Continuous listening state
        self.listening = False
        self.listen_thread = None
        
        self.logger.info(f"Indian English Voice Processor initialized (Language: {language})")

    # ---- Internal utilities ----
    def _safe_print(self, message: str):
        """Print without causing Windows console Unicode errors (strips emojis)."""
        try:
            import re
            clean = re.sub(r'[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]', '', str(message))
            print(clean)
        except Exception:
            try:
                print(str(message).encode('utf-8', errors='ignore').decode('utf-8', errors='ignore'))
            except Exception:
                pass
    
    def listen_once(self,
                   enhance_prompt: bool = False,
                   timeout: int = 20,
                   phrase_time_limit: int = 30,
                   status_callback: Optional[Callable[[str], None]] = None) -> Optional[str]:
        """
        Listen for a single voice command with extended timeout.
        
        Args:
            enhance_prompt: Whether to enhance with GPT
            timeout: How long to wait for speech to start (seconds)
            phrase_time_limit: Maximum length of phrase (seconds)
            status_callback: Callback function to update status (e.g. on overlay)
            
        Returns:
            Recognized text or None
        """
        if not self.microphone or not self.recognizer:
            self.logger.error("Speech recognition not available")
            return None
        
        # Don't open the mic while we're still talking, or we transcribe ourselves
        self.wait_until_done(timeout=30)

        try:
            msg = "🎤 Listening... (speak now, I'll wait for you to finish)"
            self._safe_print(msg)
            if status_callback: status_callback(msg)
            
            with self.microphone as source:
                # Adjust for ambient noise - longer calibration
                msg = "🔧 Calibrating for your environment..."
                self._safe_print(msg)
                if status_callback: status_callback(msg)
                
                # Re-calibrate only every couple of minutes (room noise changes slowly);
                # dynamic_energy_threshold keeps adapting in between. Saves ~0.5s per command.
                if time.time() - self._last_calibration > 120:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    self._last_calibration = time.time()
                
                msg = "🎤 Ready - speak your FULL command..."
                self._safe_print(msg)
                if status_callback: status_callback(msg)
                
                self._safe_print("   💡 Tip: speak naturally; a short pause ends your command")

                # Listen with VERY extended timeout
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
            
            msg = "🔄 Processing speech..."
            self._safe_print(msg)
            if status_callback: status_callback(msg)
            
            # Try multiple recognition methods
            text = self._recognize_with_fallback(audio)
            
            if not text:
                return None
            
            text = text.strip()
            
            # Apply phonetic corrections for common misheard words
            text = self._apply_phonetic_corrections(text)
            
            self._safe_print(f"✅ Heard: '{text}'")
            if status_callback: status_callback(f"Heard: {text}")
            
            # Enhance if requested
            if enhance_prompt and self.use_gpt_enhancement and self.openai_client:
                enhanced = self._enhance_prompt(text)
                if enhanced and enhanced != text:
                    self._safe_print(f"🧠 Enhanced: '{enhanced}'")
                    return enhanced
            
            return text
            
        except sr.WaitTimeoutError:
            msg = f"⏱️  No speech detected (waited {timeout} seconds)"
            self._safe_print(msg)
            if status_callback: status_callback(msg)
            return None
        except Exception as e:
            self.logger.error(f"Error in listen_once: {e}")
            return None
    
    def _recognize_with_fallback(self, audio) -> Optional[str]:
        """
        Try multiple recognition engines with fallback.
        Priority: Whisper > Google (Indian English) > Google (US English)
        """
        # Try 0: Whisper on Groq (default when GROQ_API_KEY is set)
        if getattr(self, "stt_provider", "google") == "groq":
            try:
                start = time.time()
                text = self._transcribe_with_groq(audio)
                if text:
                    self.logger.info(f"Recognized with Groq Whisper in {time.time() - start:.2f}s: {text}")
                    return text
                self.logger.info("Groq Whisper heard no speech")
                return None  # silence/noise: don't let Google guess something
            except Exception as e:
                self.logger.warning(f"Groq Whisper failed, falling back to Google: {e}")

        # Try 1: OpenAI Whisper (best for accents)
        if self.use_whisper and self.openai_client:
            try:
                text = self._transcribe_with_whisper(audio)
                if text:
                    self.logger.info("Recognized with Whisper")
                    return text
            except Exception as e:
                self.logger.warning(f"Whisper failed: {e}")
        
        # Try 2: Google with Indian English
        try:
            text = self.recognizer.recognize_google(audio, language=self.language)
            if text:
                self.logger.info(f"Recognized with Google ({self.language})")
                return text
        except sr.UnknownValueError:
            self.logger.warning("Google (Indian English) could not understand")
        except sr.RequestError as e:
            self.logger.error(f"Google API error: {e}")
        
        # Try 3: Google with US English (fallback)
        try:
            text = self.recognizer.recognize_google(audio, language="en-US")
            if text:
                self.logger.info("Recognized with Google (en-US fallback)")
                return text
        except Exception as e:
            self.logger.error(f"All recognition methods failed: {e}")
        
        return None
    
    def _apply_phonetic_corrections(self, text: str) -> str:
        """
        Apply phonetic corrections for commonly misheard words.
        Fixes speech recognition errors for app names, actions, etc.
        """
        import re
        
        # Phonetic correction mappings (case-insensitive)
        corrections = {
            # App names
            r'\blinkdin\b': 'linkedin',
            r'\blink din\b': 'linkedin',
            r'\blinked in\b': 'linkedin',
            r'\blink in\b': 'linkedin',
            r'\bchrome\b': 'chrome',
            r'\bgoogle chrome\b': 'chrome',
            r'\bvs code\b': 'vscode',
            r'\bvisual studio code\b': 'vscode',
            r'\bv s code\b': 'vscode',
            r'\bgmail\b': 'gmail',
            r'\bg mail\b': 'gmail',
            r'\bgoogle mail\b': 'gmail',
            r'\bnotepad\b': 'notepad',
            r'\bnote pad\b': 'notepad',
            
            # Actions
            r'\bminimise\b': 'minimize',
            r'\bminimize\b': 'minimize',
            r'\bmaximise\b': 'maximize',
            r'\bmaximize\b': 'maximize',
            
            # Common phrases
            r'\bmacro\b': 'macro',
            r'\bmacros\b': 'macros',
            r'\brecording\b': 'recording',
            r'\brecordings\b': 'recordings',
            
            # Jarvis variations
            r'\bjarves\b': 'jarvis',
            r'\bjar vis\b': 'jarvis',
            r'\bjarvis\b': 'jarvis',

            # Seen in the speech benchmark (tests/scenarios/stt_benchmark.py)
            r'\b(?:wh?at+s?\s?app?|what\'s\s?app)\b': 'WhatsApp',
            r'\b(on|in|open|close|via|using|minimi[sz]e)\s+what\'?s\s?up\b': r'\1 WhatsApp',
            r'\b(?:get|git)\s?hub\b': 'GitHub',
            r'^sent\b,?': 'send',
            r'\bdolby (?:axis|axes|excess)\b': 'dolby access',
        }
        
        corrected = text
        for pattern, replacement in corrections.items():
            corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
        
        return corrected
    
    # Whisper "hears" these in silence or noise; drop them when nothing else was said
    WHISPER_HALLUCINATIONS = {
        "thank you", "thank you very much", "thanks for watching", "thank you for watching",
        "you", "bye", "bye bye", "okay", "so", "the end", "subscribe", "please subscribe",
    }

    def _init_stt_settings(self):
        """Pick the speech-to-text engine. STT_PROVIDER=groq|google (default: groq when
        GROQ_API_KEY is set, since Whisper handles Indian English far better)."""
        if not hasattr(self, "logger"):
            self.logger = logging.getLogger(__name__)
        key = os.getenv("GROQ_API_KEY", "").strip()
        provider = os.getenv("STT_PROVIDER", "").strip().lower() or ("groq" if key and not key.startswith("your_") else "google")
        self.stt_provider = provider
        self.groq_stt_model = os.getenv("GROQ_STT_MODEL", "whisper-large-v3-turbo")
        self._groq_stt_client = None
        if provider == "groq":
            try:
                from groq import Groq
                self._groq_stt_client = Groq(api_key=key, timeout=15)
            except Exception as e:
                self.logger.warning(f"Groq Whisper unavailable ({e}); using Google speech recognition")
                self.stt_provider = "google"
        self._vocabulary_prompt = self._build_vocabulary_prompt()

    @staticmethod
    def _build_vocabulary_prompt() -> str:
        """Words Whisper should expect: our wake word, apps, commands, contacts, macros."""
        from pathlib import Path
        import json
        root = Path(__file__).resolve().parents[2]
        words = ["JARVIS", "WhatsApp", "Mohith", "Notepad", "VS Code", "Chrome", "YouTube", "Gmail",
                 "LinkedIn", "Dolby Access", "Spotify", "macro", "minimize", "Windows key"]
        try:
            contacts = json.loads((root / "data" / "whatsapp_contacts.json").read_text(encoding="utf-8"))
            for alias, entry in contacts.items():
                words.append(entry.get("search", alias) if isinstance(entry, dict) else str(entry))
        except Exception:
            pass
        try:
            words += [p.stem for p in (root / "macros").glob("*.json") if not p.stem.lower().startswith(("macro_", "scroll_test", "test"))]
        except Exception:
            pass
        seen, unique = set(), []
        for w in words:
            if w.lower() not in seen:
                seen.add(w.lower())
                unique.append(w)
        # Whisper uses the prompt as preceding context; a short command-style sentence works best
        return ("Voice commands for a desktop assistant called JARVIS, e.g. 'open WhatsApp', "
                "'send I am coming to Mohith on WhatsApp', 'click type a message'. Words: " + ", ".join(unique[:60]) + ".")

    def _transcribe_with_groq(self, audio) -> Optional[str]:
        """Transcribe with Whisper on Groq (fast, free tier, robust to accents and noise)."""
        if self._groq_stt_client is None:
            return None
        wav = audio.get_wav_data(convert_rate=16000, convert_width=2)
        result = self._groq_stt_client.audio.transcriptions.create(
            file=("command.wav", wav),
            model=self.groq_stt_model,
            language="en",
            prompt=self._vocabulary_prompt,
            response_format="verbose_json",
            temperature=0.0,
        )
        text = (getattr(result, "text", "") or "").strip()
        segments = getattr(result, "segments", None) or []
        if segments:
            def seg(s, key, default):
                return s.get(key, default) if isinstance(s, dict) else getattr(s, key, default)
            # Every segment probably silence -> nothing was really said
            if all(seg(s, "no_speech_prob", 0) > 0.6 for s in segments):
                return None
        cleaned = re.sub(r"[^a-z ]", "", text.lower()).strip()
        if not cleaned or cleaned in self.WHISPER_HALLUCINATIONS:
            return None
        # Whisper copies the prompt back when the audio is unintelligible
        if "voice commands for a desktop assistant" in text.lower():
            return None
        return text.rstrip(".!?").strip()

    def _transcribe_with_whisper(self, audio) -> Optional[str]:
        """Transcribe with OpenAI Whisper."""
        try:
            import tempfile
            
            # Convert to WAV
            audio_data = audio.get_wav_data()
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_audio.write(audio_data)
                temp_path = temp_audio.name
            
            # Transcribe
            with open(temp_path, "rb") as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"  # Whisper auto-detects Indian English
                )
            
            os.unlink(temp_path)
            return transcript.text.strip() if transcript.text else ""
            
        except Exception as e:
            self.logger.error(f"Whisper transcription error: {e}")
            return None
    
    def _enhance_prompt(self, text: str) -> str:
        """Enhance prompt with GPT."""
        try:
            system_prompt = """You are a command enhancement AI for Indian English speakers.
Convert natural Indian English commands into specific automation instructions.

Common Indian English patterns:
- "open that Gmail only" → "open Gmail in Chrome browser"
- "search for Python tutorials na" → "search Google for Python tutorials"
- "do one thing, open VSCode" → "open VSCode"
- "kindly open LinkedIn" → "open LinkedIn in Chrome browser"

The system can:
- Open applications (Chrome, VSCode, Gmail, LinkedIn, etc.)
- Search Google
- Click elements
- Type text
- Scroll pages
- Create files/folders
- Send emails

Return only the enhanced command, nothing else."""

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Enhance: {text}"}
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            enhanced = response.choices[0].message.content.strip()
            return enhanced if enhanced else text
            
        except Exception as e:
            self.logger.error(f"Enhancement error: {e}")
            return text
    
    def stop_speaking(self):
        """Stop speaking immediately (safe to call from any thread)."""
        # Drop anything still queued, then ask the worker to purge the current sentence
        try:
            while True:
                self.tts_queue.get_nowait()
                self.tts_queue.task_done()
        except queue.Empty:
            pass
        if self._speaking.is_set():
            self._purge_requested.set()

    def is_speaking(self) -> bool:
        """True while speech is queued or playing."""
        return self._speaking.is_set() or not self.tts_queue.empty()

    def wait_until_done(self, timeout: float = 30.0):
        """Block until queued speech has finished (or timeout)."""
        deadline = time.time() + timeout
        while self.is_speaking() and time.time() < deadline:
            time.sleep(0.05)

    def speak(self, text: str, async_speech: bool = True):
        """
        Text-to-speech output.

        Args:
            text: Text to speak
            async_speech: If True, returns immediately (speech can be interrupted
                          with stop_speaking). If False, blocks until spoken.
        """
        if not self.tts_engine or not text:
            return

        done = threading.Event()
        self.tts_queue.put((str(text), done))
        if not async_speech:
            done.wait(timeout=60)

    def _tts_worker(self):
        """
        TTS worker thread: owns the speech engine for its whole life and speaks
        queued text one item at a time.
        """
        sapi = None
        engine = None

        if sys.platform == "win32":
            try:
                import pythoncom
                import win32com.client
                pythoncom.CoInitialize()
                sapi = win32com.client.Dispatch("SAPI.SpVoice")
                sapi.Rate = 1
                sapi.Volume = 90
                # JARVIS is British: prefer an en-GB voice for the offline fallback
                voices = sapi.GetVoices()
                for i in range(voices.Count):
                    if "Great Britain" in voices.Item(i).GetDescription() or "en-GB" in voices.Item(i).GetDescription():
                        sapi.Voice = voices.Item(i)
                        break
                self.sapi_speaker = sapi
                self.tts_engine = "sapi"
            except Exception as e:
                self.logger.warning(f"SAPI initialization failed, trying pyttsx3: {e}")
                sapi = None

        # Neural British voice (online); SAPI stays as the offline fallback
        neural = None
        if os.getenv("TTS_ENGINE", "neural").strip().lower() == "neural" and sys.platform == "win32":
            try:
                from .neural_tts import NeuralVoice, HAS_EDGE_TTS, prune_cache
                if HAS_EDGE_TTS:
                    neural = NeuralVoice()
                    prune_cache()
                    self.tts_engine = "neural"
            except Exception as e:
                self.logger.warning(f"Neural voice unavailable: {e}")
                neural = None

        if sapi is None and HAS_TTS:
            try:
                engine = pyttsx3.init()
                for voice in engine.getProperty('voices'):
                    if 'india' in voice.name.lower() or 'hindi' in voice.name.lower():
                        self.tts_voice_id = voice.id
                        engine.setProperty('voice', voice.id)
                        break
                engine.setProperty('rate', self.tts_rate)
                engine.setProperty('volume', self.tts_volume)
                self.tts_engine = "pyttsx3"
            except Exception as e:
                self.logger.error(f"TTS initialization failed: {e}")
                engine = None

        self._tts_ready.set()
        if sapi is None and engine is None and neural is None:
            return
        self.logger.info(f"TTS worker ready ({self.tts_engine})")

        def should_stop():
            return self._purge_requested.is_set() or not self.tts_running

        while self.tts_running:
            try:
                text, done = self.tts_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            self._purge_requested.clear()
            self._speaking.set()
            try:
                if neural is not None and neural.speak(text, should_stop):
                    pass  # spoken (or interrupted) with the neural voice
                elif sapi is not None:
                    sapi.Speak(text, 1)  # 1 = SVSFlagsAsync, so we can poll for purge
                    while not sapi.WaitUntilDone(50):
                        if self._purge_requested.is_set() or not self.tts_running:
                            sapi.Speak("", 2)  # 2 = SVSFPurgeBeforeSpeak: stop now
                            break
                else:
                    engine.say(text)
                    engine.runAndWait()
            except Exception as e:
                self.logger.error(f"TTS speak error: {e}")
            finally:
                self._speaking.clear()
                done.set()
                self.tts_queue.task_done()

        try:
            if engine is not None:
                engine.stop()
            if sapi is not None:
                import pythoncom
                pythoncom.CoUninitialize()
        except Exception:
            pass

    def calibrate_microphone(self):
        """Recalibrate microphone for ambient noise."""
        if not self.microphone or not self.recognizer:
            return

        try:
            print("🔧 Calibrating microphone for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("✅ Calibration complete!")
        except Exception as e:
            self.logger.error(f"Calibration error: {e}")

    def listen(self, timeout: int = 10, phrase_time_limit: int = 15) -> Optional[str]:
        """Compatibility alias used by SmartAppOpener and older callers."""
        return self.listen_once(timeout=timeout, phrase_time_limit=phrase_time_limit)

    def stop_continuous_listening(self):
        """This processor listens on demand only; kept so callers can stop it uniformly."""
        self.listening = False

    def cleanup(self):
        """Cleanup resources."""
        self.stop_speaking()

        # Stop TTS worker
        self.tts_running = False
        if self.tts_thread:
            self.tts_thread.join(timeout=2)

        # Stop listening
        if self.listening:
            self.stop_continuous_listening()
