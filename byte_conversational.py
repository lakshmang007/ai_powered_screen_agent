#!/usr/bin/env python3
"""
Byte - Your Conversational AI Assistant

Fully conversational AI assistant with JARVIS-like functionality.
Conversational, intelligent, and always ready to help.

Wake word: "byte"
"""

import sys
import os
import random
import time
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))


class JARVIS:
    """Byte - Your conversational AI assistant."""

    def __init__(self):
        """Initialize Byte."""
        # Personality
        self.name = "Byte"
        self.sir_name = ""  # What Byte calls you (empty for casual)
        
        # Greetings
        self.greetings = [
            "Hello! How can I help you?",
            "Hey! What can I do for you?",
            "Hi there! What do you need?",
            "Yes! What's up?",
            "I'm here! What can I do?"
        ]

        # Acknowledgments
        self.acknowledgments = [
            "Got it!",
            "Sure thing!",
            "On it!",
            "Okay!",
            "Working on it!"
        ]

        # Success messages
        self.success_messages = [
            "Done!",
            "Complete!",
            "Finished!",
            "All done!",
            "Success!"
        ]
        
        # Conversational responses
        self.conversational = {
            "how are you": [
                "I'm doing great! Thanks for asking.",
                "All good here! How about you?",
                "Doing well! What can I help you with?"
            ],
            "what are you doing": [
                "Just waiting for your commands!",
                "Standing by, ready to help!",
                "Ready to assist you with anything!"
            ],
            "thank you": [
                "You're welcome!",
                "No problem!",
                "Happy to help!",
                "Anytime!"
            ],
            "good morning": [
                "Good morning! Ready to start?",
                "Good morning! What can I do for you today?"
            ],
            "good night": [
                "Good night! Sleep well!",
                "Good night! I'll be here when you need me!"
            ],
            "who are you": [
                "I'm Byte, your AI assistant!",
                "I'm Byte! Here to help you with tasks.",
                "I'm Byte, your personal assistant!"
            ],
            "what can you do": [
                "I can open apps, search the web, send WhatsApp messages, play YouTube videos, and chat with you!",
                "I can help with web automation using Selenium, send WhatsApp messages with PyWhatKit, and much more!",
                "I can do lots of things! Open apps, search Google, play YouTube, send WhatsApp, and more!"
            ]
        }
        
        # Initialize components
        self.init_components()
    
    def init_components(self):
        """Initialize voice and automation components."""
        try:
            from src.core.indian_english_voice_processor import IndianEnglishVoiceProcessor
            from src.core.nlp_processor import NLPProcessor
            from src.automation.task_engine import TaskEngine
            from src.core.screen_agent import ScreenAgent
            from src.automation.handlers import VSCodeHandler, GmailHandler, LinkedInHandler, BrowserHandler
            from src.automation.handlers.selenium_handler import SeleniumHandler
            from src.automation.handlers.pywhatkit_handler import PyWhatKitHandler
            from src.core.nlp_processor import ApplicationType
            from src.core.intelligent_assistant import IntelligentAssistant
            
            # Voice processor
            self.voice = IndianEnglishVoiceProcessor(
                wake_word="byte",
                language="en-IN",
                use_whisper=False,
                use_gpt_enhancement=False
            )

            # Set Byte voice
            self._set_byte_voice()
            
            # NLP and automation
            self.nlp = NLPProcessor()
            self.screen_agent = ScreenAgent()
            self.engine = TaskEngine(self.screen_agent)
            self.intelligent = IntelligentAssistant(self.voice, self.nlp)
            
            # Register handlers
            vscode_handler = VSCodeHandler(self.screen_agent)
            gmail_handler = GmailHandler(self.screen_agent)
            linkedin_handler = LinkedInHandler(self.screen_agent)
            browser_handler = BrowserHandler(self.screen_agent)
            selenium_handler = SeleniumHandler(self.screen_agent)
            pywhatkit_handler = PyWhatKitHandler(self.screen_agent)

            # Import new handlers
            from src.automation.handlers.youtube_handler import YouTubeHandler
            from src.automation.handlers.keyboard_handler import KeyboardHandler

            youtube_handler = YouTubeHandler(self.screen_agent)
            keyboard_handler = KeyboardHandler(self.screen_agent)

            self.engine.register_app_handler(ApplicationType.VSCODE, vscode_handler.handle_command)
            self.engine.register_app_handler(ApplicationType.GMAIL, gmail_handler.handle_command)
            self.engine.register_app_handler(ApplicationType.LINKEDIN, linkedin_handler.handle_command)
            self.engine.register_app_handler(ApplicationType.CHROME, browser_handler.handle_command)
            self.engine.register_app_handler(ApplicationType.SELENIUM, selenium_handler.handle_command)
            self.engine.register_app_handler(ApplicationType.GOOGLE, selenium_handler.handle_command)
            self.engine.register_app_handler(ApplicationType.YOUTUBE, youtube_handler.handle_command)
            self.engine.register_app_handler(ApplicationType.WHATSAPP, pywhatkit_handler.handle_command)
            self.engine.register_app_handler(ApplicationType.PYWHATKIT, pywhatkit_handler.handle_command)
            self.engine.register_app_handler(ApplicationType.KEYBOARD, keyboard_handler.handle_command)

            # Store handlers for cleanup
            self.selenium_handler = selenium_handler
            self.pywhatkit_handler = pywhatkit_handler
            self.youtube_handler = youtube_handler
            self.keyboard_handler = keyboard_handler
            
            print("✅ Byte initialized successfully!")

        except Exception as e:
            print(f"❌ Error initializing Byte: {e}")
            raise

    def _set_byte_voice(self):
        """Set Byte voice settings."""
        if not self.voice.tts_engine:
            return

        try:
            # Set rate and volume for natural voice
            self.voice.tts_engine.setProperty('rate', 160)
            self.voice.tts_engine.setProperty('volume', 0.9)
        except Exception as e:
            print(f"⚠️  Could not set voice: {e}")

    def speak(self, text):
        """Speak with Byte voice."""
        print(f"\n🤖 Byte: {text}")
        self.voice.speak(text)
        # Wait for TTS to finish speaking
        time.sleep(len(text) * 0.05 + 0.5)  # Estimate based on text length
    
    def listen(self, timeout=20):
        """Listen for user input."""
        return self.voice.listen_once(timeout=timeout, phrase_time_limit=30)
    
    def get_conversational_response(self, text):
        """Get conversational response for casual queries."""
        text_lower = text.lower().strip()
        
        for key, responses in self.conversational.items():
            if key in text_lower:
                return random.choice(responses)
        
        return None
    
    def run(self):
        """Run Byte main loop."""
        self.print_header()

        # Initial greeting
        greeting = random.choice(self.greetings)
        self.speak(greeting)

        is_awake = True
        task_count = 0

        try:
            while True:
                print("\n" + "-" * 70)

                if is_awake:
                    # Listen for command
                    print("🎤 Listening...")
                    command = self.listen()

                    if not command:
                        continue

                    cmd_lower = command.lower().strip()
                    print(f"📝 You: {command}")

                    # Check for exit
                    if self.is_exit_command(cmd_lower):
                        self.speak("Goodbye! See you later!")
                        break

                    # Check for sleep
                    if self.is_sleep_command(cmd_lower):
                        is_awake = False
                        self.speak("Going to sleep. Say 'Byte' to wake me!")
                        continue

                    # Check for wake word (new conversation)
                    if self.is_wake_word(cmd_lower):
                        greeting = random.choice(self.greetings)
                        self.speak(greeting)
                        continue

                    # Check for conversational query
                    conv_response = self.get_conversational_response(cmd_lower)
                    if conv_response:
                        self.speak(conv_response)
                        continue

                    # Execute task
                    success = self.execute_task(command)
                    if success:
                        task_count += 1

                    # Continue conversation
                    time.sleep(0.5)
                    self.speak("Anything else?")

                else:
                    # Sleep mode - only wake on wake word
                    print("😴 Byte is sleeping... Say 'Byte' to wake")
                    command = self.listen(timeout=60)

                    if command and self.is_wake_word(command.lower()):
                        is_awake = True
                        self.speak("I'm here! What do you need?")

        except KeyboardInterrupt:
            self.speak(f"Shutting down. Completed {task_count} tasks. Goodbye!")
            self.voice.cleanup()
    
    def execute_task(self, command):
        """Execute a task with JARVIS personality."""
        # Acknowledge
        ack = random.choice(self.acknowledgments)
        self.speak(ack)
        
        try:
            # Parse command
            parsed = self.nlp.parse_command(command)
            action_str = parsed.action.value.lower()
            app_str = parsed.application.value.lower()
            
            # Handle with intelligence
            if action_str == "open" and app_str == "unknown":
                app_name = self.extract_app_name(command)
                if app_name:
                    return self.handle_open_with_intelligence(app_name)
            
            elif action_str == "search":
                query = parsed.parameters.get("query", command)
                return self.handle_search_with_intelligence(query)
            
            # Execute normally
            result = self.engine.execute_command(parsed)
            
            if result.status.value == 'completed':
                success_msg = random.choice(self.success_messages)
                self.speak(success_msg)
                return True
            else:
                self.speak(f"I'm afraid that didn't work, {self.sir_name}. {result.message}")
                return False
        
        except Exception as e:
            self.speak(f"I encountered an error, {self.sir_name}. {str(e)}")
            return False
    
    def handle_open_with_intelligence(self, app_name):
        """Handle open command with intelligence."""
        exists, app_path = self.intelligent.check_application_exists(app_name)

        if exists:
            self.speak(f"I found {app_name}! Opening it now.")
            try:
                subprocess.Popen([app_path])
                self.speak(random.choice(self.success_messages))
                return True
            except Exception as e:
                self.speak(f"Having trouble opening that.")
                return False
        else:
            self.speak(f"Couldn't find {app_name} installed. Should I open it in a browser?")
            response = self.listen(timeout=15)

            if response and self.is_positive(response.lower()):
                self.speak("Which browser? Chrome, Firefox, or Edge?")
                browser_response = self.listen(timeout=15)

                browser = "chrome"
                if browser_response:
                    if "firefox" in browser_response.lower():
                        browser = "firefox"
                    elif "edge" in browser_response.lower():
                        browser = "edge"

                url = self.intelligent._get_web_url(app_name)
                try:
                    subprocess.Popen(["start", browser, url], shell=True)
                    self.speak(f"Opening {app_name} in {browser}!")
                    return True
                except:
                    self.speak("Having trouble with that.")
                    return False
            else:
                self.speak("Okay, no problem!")
                return False

    def handle_search_with_intelligence(self, query):
        """Handle search with intelligence."""
        self.speak(f"Searching for {query}...")

        try:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            subprocess.Popen(["start", "chrome", url], shell=True)
            self.speak(random.choice(self.success_messages))
            return True
        except:
            self.speak("Having trouble with that search.")
            return False
    
    def extract_app_name(self, command):
        """Extract app name from command."""
        words_to_remove = ["open", "launch", "start", "run", "please", "jarvis", "can", "you"]
        words = command.lower().split()
        app_words = [w for w in words if w not in words_to_remove]
        return " ".join(app_words) if app_words else None
    
    def is_wake_word(self, text):
        """Check for wake word."""
        return any(word in text for word in ["byte", "bite", "bait"])

    def is_sleep_command(self, text):
        """Check for sleep command."""
        return any(word in text for word in ["sleep", "rest", "standby", "so ja"])

    def is_exit_command(self, text):
        """Check for exit command."""
        return any(word in text for word in ["exit", "quit", "goodbye", "shut down", "shutdown", "stop executing"])

    def is_positive(self, text):
        """Check for positive response."""
        return any(word in text for word in ["yes", "yeah", "sure", "ok", "okay", "haan"])

    def print_header(self):
        """Print Byte header."""
        print("\n" + "=" * 70)
        print("🤖 BYTE - Your Conversational AI Assistant".center(70))
        print("=" * 70)
        print("\nFeatures:")
        print("  ✅ Fully conversational - chat naturally!")
        print("  ✅ Intelligent task execution")
        print("  ✅ Always speaking (TTS fixed!)")
        print("  ✅ Optimized for Indian English")
        print("\nWake word: 'Byte'")
        print("Sleep: 'Sleep' or 'Standby'")
        print("Exit: 'Goodbye' or 'Stop executing'")
        print("\n" + "=" * 70 + "\n")


def main():
    """Main entry point."""
    try:
        byte = JARVIS()  # Class name stays JARVIS internally
        byte.run()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

