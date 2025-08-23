"""
Voice processing module for speech-to-text and text-to-speech functionality.
"""

try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False
    sr = None

try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False
    pyttsx3 = None
import threading
import queue
import logging
from typing import Optional, Callable
import time

class VoiceProcessor:
    """Handles voice input and output processing."""
    
    def __init__(self,
                 timeout: int = 5,
                 phrase_timeout: float = 1.0,
                 energy_threshold: int = 300):
        """
        Initialize the Voice Processor.

        Args:
            timeout: Seconds to wait for speech input
            phrase_timeout: Seconds to wait for phrase completion
            energy_threshold: Minimum audio energy to consider as speech
        """
        self.timeout = timeout
        self.phrase_timeout = phrase_timeout
        self.energy_threshold = energy_threshold

        # Initialize logger first
        self.logger = logging.getLogger(__name__)

        # Initialize speech recognition if available
        if HAS_SPEECH_RECOGNITION:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()

                # Voice recognition settings
                self.recognizer.energy_threshold = energy_threshold
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 0.8

                # Calibrate microphone
                self._calibrate_microphone()
            except Exception as e:
                self.logger.error(f"Error initializing speech recognition: {e}")
                self.recognizer = None
                self.microphone = None
        else:
            self.recognizer = None
            self.microphone = None

        # Text-to-speech engine
        if HAS_TTS:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 150)  # Speed of speech
                self.tts_engine.setProperty('volume', 0.8)  # Volume level
            except Exception as e:
                self.logger.error(f"Error initializing TTS: {e}")
                self.tts_engine = None
        else:
            self.tts_engine = None

        # Threading for continuous listening
        self.listening = False
        self.listen_thread = None
        self.command_queue = queue.Queue()
    
    def _calibrate_microphone(self):
        """Calibrate microphone for ambient noise."""
        if not self.microphone or not self.recognizer:
            return
        try:
            with self.microphone as source:
                self.logger.info("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                self.logger.info("Microphone calibrated successfully")
        except Exception as e:
            self.logger.error(f"Error calibrating microphone: {e}")
    
    def listen_once(self, language: str = "en-US") -> Optional[str]:
        """
        Listen for a single voice command.

        Args:
            language: Language code for recognition

        Returns:
            Recognized text or None if no speech detected
        """
        if not self.microphone or not self.recognizer:
            self.logger.warning("Speech recognition not available")
            return None

        try:
            with self.microphone as source:
                self.logger.info("Listening for command...")
                audio = self.recognizer.listen(source,
                                             timeout=self.timeout,
                                             phrase_time_limit=self.phrase_timeout)

            self.logger.info("Processing speech...")
            text = self.recognizer.recognize_google(audio, language=language)
            self.logger.info(f"Recognized: {text}")
            return text.lower().strip()

        except sr.WaitTimeoutError:
            self.logger.warning("No speech detected within timeout")
            return None
        except sr.UnknownValueError:
            self.logger.warning("Could not understand audio")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Error with speech recognition service: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in speech recognition: {e}")
            return None
    
    def start_continuous_listening(self, callback: Callable[[str], None], language: str = "en-US"):
        """
        Start continuous listening for voice commands.
        
        Args:
            callback: Function to call when command is recognized
            language: Language code for recognition
        """
        if self.listening:
            self.logger.warning("Already listening")
            return
        
        self.listening = True
        self.listen_thread = threading.Thread(
            target=self._continuous_listen_worker,
            args=(callback, language),
            daemon=True
        )
        self.listen_thread.start()
        self.logger.info("Started continuous listening")
    
    def stop_continuous_listening(self):
        """Stop continuous listening."""
        self.listening = False
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=2)
        self.logger.info("Stopped continuous listening")
    
    def _continuous_listen_worker(self, callback: Callable[[str], None], language: str):
        """Worker thread for continuous listening."""
        while self.listening:
            try:
                with self.microphone as source:
                    # Listen for audio with shorter timeout for responsiveness
                    audio = self.recognizer.listen(source, 
                                                 timeout=1, 
                                                 phrase_time_limit=self.phrase_timeout)
                
                # Process in separate thread to avoid blocking
                threading.Thread(
                    target=self._process_audio,
                    args=(audio, callback, language),
                    daemon=True
                ).start()
                
            except sr.WaitTimeoutError:
                # Normal timeout, continue listening
                continue
            except Exception as e:
                self.logger.error(f"Error in continuous listening: {e}")
                time.sleep(0.1)  # Brief pause before retrying
    
    def _process_audio(self, audio, callback: Callable[[str], None], language: str):
        """Process audio in separate thread."""
        try:
            text = self.recognizer.recognize_google(audio, language=language)
            text = text.lower().strip()
            if text:
                self.logger.info(f"Recognized: {text}")
                callback(text)
        except sr.UnknownValueError:
            # Could not understand audio - this is normal, ignore
            pass
        except sr.RequestError as e:
            self.logger.error(f"Error with speech recognition service: {e}")
        except Exception as e:
            self.logger.error(f"Error processing audio: {e}")
    
    def speak(self, text: str, async_speech: bool = False):
        """
        Convert text to speech.
        
        Args:
            text: Text to speak
            async_speech: Whether to speak asynchronously
        """
        try:
            if async_speech:
                threading.Thread(
                    target=self._speak_worker,
                    args=(text,),
                    daemon=True
                ).start()
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
    
    def set_voice_properties(self, rate: int = None, volume: float = None, voice_id: int = None):
        """
        Set voice properties for text-to-speech.
        
        Args:
            rate: Speech rate (words per minute)
            volume: Volume level (0.0 to 1.0)
            voice_id: Voice ID (0 for male, 1 for female typically)
        """
        try:
            if rate is not None:
                self.tts_engine.setProperty('rate', rate)
            
            if volume is not None:
                self.tts_engine.setProperty('volume', max(0.0, min(1.0, volume)))
            
            if voice_id is not None:
                voices = self.tts_engine.getProperty('voices')
                if voices and 0 <= voice_id < len(voices):
                    self.tts_engine.setProperty('voice', voices[voice_id].id)
                    
        except Exception as e:
            self.logger.error(f"Error setting voice properties: {e}")
    
    def get_available_voices(self) -> list:
        """
        Get list of available voices.
        
        Returns:
            List of available voice information
        """
        try:
            voices = self.tts_engine.getProperty('voices')
            voice_info = []
            for i, voice in enumerate(voices):
                voice_info.append({
                    'id': i,
                    'name': voice.name,
                    'language': getattr(voice, 'languages', ['Unknown']),
                    'gender': getattr(voice, 'gender', 'Unknown')
                })
            return voice_info
        except Exception as e:
            self.logger.error(f"Error getting available voices: {e}")
            return []
    
    def is_listening(self) -> bool:
        """Check if currently listening for voice commands."""
        return self.listening
    
    def test_microphone(self) -> bool:
        """
        Test if microphone is working.
        
        Returns:
            True if microphone is working, False otherwise
        """
        try:
            with self.microphone as source:
                self.logger.info("Testing microphone...")
                audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=1)
                return True
        except Exception as e:
            self.logger.error(f"Microphone test failed: {e}")
            return False
    
    def get_microphone_list(self) -> list:
        """
        Get list of available microphones.
        
        Returns:
            List of microphone names
        """
        try:
            return sr.Microphone.list_microphone_names()
        except Exception as e:
            self.logger.error(f"Error getting microphone list: {e}")
            return []
    
    def set_microphone(self, device_index: int):
        """
        Set specific microphone device.
        
        Args:
            device_index: Index of microphone device
        """
        try:
            self.microphone = sr.Microphone(device_index=device_index)
            self._calibrate_microphone()
            self.logger.info(f"Microphone set to device index: {device_index}")
        except Exception as e:
            self.logger.error(f"Error setting microphone: {e}")
