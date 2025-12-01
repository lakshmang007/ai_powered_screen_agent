"""
Enhanced Voice Processor optimized for Indian English.
Features:
- Better recognition for Indian accents
- Longer listening duration (doesn't exit quickly)
- Multiple recognition engines with fallback
- Continuous listening with better timeout handling
"""

import os
import logging
from typing import Optional, Callable
import threading
import queue
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

            # Optimized settings for Indian English - VERY PATIENT
            self.recognizer.energy_threshold = 300  # Lower for softer speech
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 2.0  # MUCH longer pauses - won't cut off mid-sentence
            self.recognizer.phrase_threshold = 0.1  # Very sensitive to start of speech
            self.recognizer.non_speaking_duration = 1.5  # Wait 1.5 seconds of silence before stopping
            
            try:
                self.microphone = sr.Microphone()
                self.logger.info("Microphone initialized")

                # Try to calibrate for ambient noise (with timeout protection)
                try:
                    with self.microphone as source:
                        self.logger.info("Calibrating for ambient noise (2 seconds)...")
                        self.recognizer.adjust_for_ambient_noise(source, duration=1)  # Reduced to 1 second
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
        
        # Initialize SAPI speaker for Windows (allows interruption)
        self.sapi_speaker = None
        try:
            import sys
            if sys.platform == "win32":
                import win32com.client
                self.sapi_speaker = win32com.client.Dispatch("SAPI.SpVoice")
                self.sapi_speaker.Rate = 1
                self.sapi_speaker.Volume = 90
        except Exception as e:
            self.logger.warning(f"SAPI initialization failed: {e}")

        # Initialize TTS with queue to prevent "run loop already started" error
        self.tts_queue = queue.Queue()
        self.tts_thread = None
        self.tts_running = False
        self.tts_lock = threading.Lock()
        self.tts_voice_id = None  # Store voice ID for worker thread
        self.tts_rate = 160
        self.tts_volume = 0.9

        if HAS_TTS:
            try:
                # Create temporary engine to get voice settings
                temp_engine = pyttsx3.init()
                voices = temp_engine.getProperty('voices')
                for voice in voices:
                    if 'india' in voice.name.lower() or 'hindi' in voice.name.lower():
                        self.tts_voice_id = voice.id
                        break
                temp_engine.stop()
                del temp_engine

                # Mark that TTS is available
                self.tts_engine = True  # Just a flag, actual engine created in worker

                # Start TTS worker thread (will create its own engine)
                self.tts_running = True
                self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
                self.tts_thread.start()
            except Exception as e:
                self.logger.error(f"TTS initialization failed: {e}")
                self.tts_engine = None
        else:
            self.tts_engine = None
        
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
        
        try:
            msg = "🎤 Listening... (speak now, I'll wait for you to finish)"
            self._safe_print(msg)
            if status_callback: status_callback(msg)
            
            with self.microphone as source:
                # Adjust for ambient noise - longer calibration
                msg = "🔧 Calibrating for your environment..."
                self._safe_print(msg)
                if status_callback: status_callback(msg)
                
                self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
                
                msg = "🎤 Ready - speak your FULL command..."
                self._safe_print(msg)
                if status_callback: status_callback(msg)
                
                self._safe_print("   💡 Tip: Speak naturally, I'll wait 2 seconds of silence before stopping")

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
            msg = "⏱️  No speech detected (waited 15 seconds)"
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
        }
        
        corrected = text
        for pattern, replacement in corrections.items():
            corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
        
        return corrected
    
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
        """Stop speaking immediately."""
        if self.sapi_speaker:
            try:
                # 2 = SVSFPurgeBeforeSpeak (stops current speech)
                self.sapi_speaker.Speak("", 2)
            except Exception as e:
                self.logger.error(f"Error stopping speech: {e}")

    def speak(self, text: str, async_speech: bool = True):
        """
        Text-to-speech output using Windows SAPI directly.

        Args:
            text: Text to speak
            async_speech: If True, speaks asynchronously (allows interruption)
        """
        if not self.tts_engine:
            return

        try:
            # Use Windows SAPI directly (more reliable than pyttsx3 threading)
            if self.sapi_speaker:
                try:
                    flags = 1 if async_speech else 0  # 1 = SVSFlagsAsync
                    self.sapi_speaker.Speak(text, flags)
                    return
                except Exception as e:
                    self.logger.error(f"SAPI speak error: {e}")
                    # Fallback to pyttsx3

            # Fallback: Use pyttsx3 (may have threading issues)
            import pyttsx3
            engine = pyttsx3.init()

            # Apply settings
            if self.tts_voice_id:
                try:
                    engine.setProperty('voice', self.tts_voice_id)
                except:
                    pass
            engine.setProperty('rate', self.tts_rate)
            engine.setProperty('volume', self.tts_volume)

            # Speak
            engine.say(text)
            engine.runAndWait()

            # Cleanup
            engine.stop()
            del engine

        except Exception as e:
            self.logger.error(f"TTS error: {e}")

    def _tts_worker(self):
        """
        TTS worker thread that processes speech queue.
        This prevents "run loop already started" errors by creating
        its own pyttsx3 engine in this thread.
        """
        # Create TTS engine in THIS thread (important!)
        try:
            engine = pyttsx3.init()

            # Apply settings
            if self.tts_voice_id:
                engine.setProperty('voice', self.tts_voice_id)
            engine.setProperty('rate', self.tts_rate)
            engine.setProperty('volume', self.tts_volume)

            self.logger.info("TTS worker engine initialized")
        except Exception as e:
            self.logger.error(f"TTS worker engine init failed: {e}")
            return

        # Process queue
        while self.tts_running:
            try:
                # Get text from queue (wait up to 1 second)
                text = self.tts_queue.get(timeout=1)

                # Speak using the engine
                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e:
                    self.logger.error(f"TTS speak error: {e}")

                self.tts_queue.task_done()
            except queue.Empty:
                # No text to speak, continue waiting
                continue
            except Exception as e:
                self.logger.error(f"TTS worker error: {e}")

        # Cleanup
        try:
            engine.stop()
        except:
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

    def cleanup(self):
        """Cleanup resources."""
        # Stop TTS worker
        self.tts_running = False
        if self.tts_thread:
            self.tts_thread.join(timeout=2)

        # Stop listening
        if self.listening:
            self.stop_continuous_listening()

