"""
Enhanced Voice Processor with OpenAI Whisper and GPT-4 integration.
Provides automatic prompt enhancement and better voice recognition.
"""

import os
import logging
from typing import Optional, Callable
import threading
import queue
import time

# OpenAI for Whisper (voice) and GPT-4 (prompt enhancement)
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    openai = None

# Fallback to speech_recognition
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


class EnhancedVoiceProcessor:
    """
    Enhanced voice processor with:
    1. OpenAI Whisper for better voice recognition
    2. GPT-4 for automatic prompt enhancement
    3. Continuous listening with wake word support
    4. Selenium-compatible automation
    """
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 use_whisper: bool = True,
                 use_gpt_enhancement: bool = True,
                 wake_word: str = "computer"):
        """
        Initialize enhanced voice processor.
        
        Args:
            openai_api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            use_whisper: Use OpenAI Whisper for voice recognition
            use_gpt_enhancement: Use GPT-4 for prompt enhancement
            wake_word: Wake word to activate voice commands
        """
        self.logger = logging.getLogger(__name__)
        self.wake_word = wake_word.lower()
        self.use_whisper = use_whisper and HAS_OPENAI
        self.use_gpt_enhancement = use_gpt_enhancement and HAS_OPENAI
        
        # Setup OpenAI
        if HAS_OPENAI:
            openai.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
            if not openai.api_key:
                self.logger.warning("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
                self.use_whisper = False
                self.use_gpt_enhancement = False
        
        # Initialize speech recognition (fallback or for audio capture)
        if HAS_SPEECH_RECOGNITION:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            self.recognizer.energy_threshold = 4000
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
        else:
            self.recognizer = None
            self.microphone = None
        
        # Initialize TTS
        if HAS_TTS:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 175)
                self.tts_engine.setProperty('volume', 0.9)
            except Exception as e:
                self.logger.error(f"Error initializing TTS: {e}")
                self.tts_engine = None
        else:
            self.tts_engine = None
        
        # Continuous listening state
        self.listening = False
        self.listen_thread = None
        self.command_queue = queue.Queue()
        
        self.logger.info(f"Enhanced Voice Processor initialized (Whisper: {self.use_whisper}, GPT: {self.use_gpt_enhancement})")
    
    def listen_once(self, enhance_prompt: bool = True) -> Optional[str]:
        """
        Listen for a single voice command and optionally enhance it.
        
        Args:
            enhance_prompt: Whether to enhance the prompt with GPT-4
            
        Returns:
            Enhanced command text or None
        """
        if not self.microphone or not self.recognizer:
            self.logger.error("Speech recognition not available")
            return None
        
        try:
            print("🎤 Listening... (speak now)")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("🎤 Ready - speak your command...")
                
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
            
            print("🔄 Processing speech...")
            
            # Use Whisper if available, otherwise Google
            if self.use_whisper:
                text = self._transcribe_with_whisper(audio)
            else:
                text = self.recognizer.recognize_google(audio)
            
            if not text:
                return None
            
            text = text.strip()
            print(f"✅ Heard: '{text}'")
            
            # Enhance prompt with GPT-4
            if enhance_prompt and self.use_gpt_enhancement:
                enhanced_text = self._enhance_prompt(text)
                if enhanced_text and enhanced_text != text:
                    print(f"🧠 Enhanced: '{enhanced_text}'")
                    return enhanced_text
            
            return text
            
        except sr.WaitTimeoutError:
            print("⏱️ No speech detected")
            return None
        except Exception as e:
            self.logger.error(f"Error in listen_once: {e}")
            return None
    
    def _transcribe_with_whisper(self, audio) -> Optional[str]:
        """
        Transcribe audio using OpenAI Whisper API.

        Args:
            audio: Audio data from speech_recognition

        Returns:
            Transcribed text or None
        """
        try:
            # Convert audio to WAV format
            audio_data = audio.get_wav_data()

            # Save temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_audio.write(audio_data)
                temp_path = temp_audio.name

            # Transcribe with Whisper (new API v2.x)
            from openai import OpenAI
            client = OpenAI(api_key=openai.api_key)

            with open(temp_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )

            # Cleanup
            os.unlink(temp_path)

            return transcript.text.strip() if transcript.text else ""

        except Exception as e:
            self.logger.error(f"Error with Whisper transcription: {e}")
            # Fallback to Google
            try:
                return self.recognizer.recognize_google(audio)
            except:
                return None
    
    def _enhance_prompt(self, text: str) -> str:
        """
        Enhance vague prompts into detailed, executable commands using GPT-4.

        Args:
            text: Original voice command

        Returns:
            Enhanced command text
        """
        try:
            system_prompt = """You are a command enhancement AI for a screen automation system.
Your job is to convert vague or general voice commands into specific, detailed automation instructions.

The system can:
- Open applications (Chrome, VSCode, Gmail, LinkedIn, etc.)
- Click on elements
- Type text
- Search for things
- Scroll pages
- Create files/folders
- Send emails
- Post on LinkedIn

Examples:
User: "open that email thing"
Enhanced: "open Gmail in Chrome browser"

User: "send a message to John"
Enhanced: "open Gmail and compose email to John"

User: "post something on social media"
Enhanced: "open LinkedIn and create a new post"

User: "find python tutorials"
Enhanced: "open Chrome and search Google for python tutorials"

Only return the enhanced command, nothing else. Keep it concise but specific."""

            # Use new OpenAI API v2.x
            from openai import OpenAI
            client = OpenAI(api_key=openai.api_key)

            # Use gpt-3.5-turbo (cheaper and more widely available than gpt-4)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Enhance this command: {text}"}
                ],
                temperature=0.3,
                max_tokens=100
            )

            enhanced = response.choices[0].message.content.strip()
            return enhanced if enhanced else text

        except Exception as e:
            self.logger.error(f"Error enhancing prompt: {e}")
            return text
    
    def start_continuous_listening(self, 
                                   callback: Callable[[str], None],
                                   use_wake_word: bool = True,
                                   enhance_prompts: bool = True):
        """
        Start continuous listening with optional wake word activation.
        
        Args:
            callback: Function to call with recognized commands
            use_wake_word: Require wake word before processing commands
            enhance_prompts: Enhance prompts with GPT-4
        """
        if self.listening:
            self.logger.warning("Already listening")
            return
        
        self.listening = True
        self.listen_thread = threading.Thread(
            target=self._continuous_listen_worker,
            args=(callback, use_wake_word, enhance_prompts),
            daemon=True
        )
        self.listen_thread.start()
        
        wake_msg = f" (say '{self.wake_word}' first)" if use_wake_word else ""
        print(f"🎤 Continuous listening started{wake_msg}")
        self.logger.info("Started continuous listening")
    
    def _continuous_listen_worker(self, callback, use_wake_word, enhance_prompts):
        """Worker thread for continuous listening."""
        wake_word_detected = not use_wake_word  # If not using wake word, always active
        
        while self.listening:
            try:
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=15)
                
                # Transcribe
                if self.use_whisper:
                    text = self._transcribe_with_whisper(audio)
                else:
                    try:
                        text = self.recognizer.recognize_google(audio)
                    except:
                        continue
                
                if not text:
                    continue
                
                text = text.lower().strip()
                
                # Check for wake word
                if use_wake_word and not wake_word_detected:
                    if self.wake_word in text:
                        wake_word_detected = True
                        print(f"👂 Wake word detected! Listening for command...")
                        if self.tts_engine:
                            self.speak("Yes?", async_speech=True)
                    continue
                
                # Process command
                if wake_word_detected:
                    # Enhance if needed
                    if enhance_prompts and self.use_gpt_enhancement:
                        text = self._enhance_prompt(text)
                    
                    print(f"📝 Command: {text}")
                    callback(text)
                    
                    # Reset wake word detection
                    if use_wake_word:
                        wake_word_detected = False
                
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in continuous listening: {e}")
                time.sleep(0.1)
    
    def stop_continuous_listening(self):
        """Stop continuous listening."""
        self.listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=2)
        self.logger.info("Stopped continuous listening")
    
    def speak(self, text: str, async_speech: bool = False):
        """
        Convert text to speech.
        
        Args:
            text: Text to speak
            async_speech: Whether to speak asynchronously
        """
        if not self.tts_engine:
            return
        
        try:
            if async_speech:
                threading.Thread(target=self._speak_worker, args=(text,), daemon=True).start()
            else:
                self._speak_worker(text)
        except Exception as e:
            self.logger.error(f"Error in text-to-speech: {e}")
    
    def _speak_worker(self, text: str):
        """Worker method for text-to-speech."""
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            self.logger.error(f"Error in TTS worker: {e}")

