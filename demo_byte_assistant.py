#!/usr/bin/env python3
"""
Byte - Your Interactive Indian English Voice Assistant

Features:
- Wake word: "byte"
- Interactive responses and feedback
- Asks for confirmation after tasks
- Sleep mode when you say "sleep"
- Optimized for Indian English
"""

import sys
import os
import random
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(text.center(70))
    print("=" * 70 + "\n")


class ByteAssistant:
    """Interactive voice assistant with personality."""
    
    def __init__(self):
        self.task_count = 0
        self.is_sleeping = False
        
        # Greeting messages
        self.greetings = [
            "Hello! I'm Byte, your voice assistant. What can I do for you?",
            "Hi there! Byte here, ready to help. What do you need?",
            "Hey! Byte at your service. How can I assist you today?",
            "Namaste! I'm Byte. What task can I help you with?",
            "Hello! Byte is ready. What would you like me to do?"
        ]
        
        # Acknowledgment messages
        self.acknowledgments = [
            "Got it! Working on it...",
            "Sure thing! Let me do that...",
            "On it! Give me a moment...",
            "Understood! Processing...",
            "Okay! Let me handle that..."
        ]
        
        # Success messages
        self.success_messages = [
            "Done! Task completed successfully.",
            "All done! That worked perfectly.",
            "Success! Task finished.",
            "Complete! Everything went well.",
            "Finished! Task executed successfully."
        ]
        
        # Feedback questions
        self.feedback_questions = [
            "Anything else I can help you with?",
            "What's next? Any other task?",
            "Need anything else, or should I sleep?",
            "Can I do something else for you?",
            "What else can I help with today?"
        ]
        
        # Sleep messages
        self.sleep_messages = [
            "Going to sleep mode. Say 'byte' to wake me up!",
            "Sleeping now. Wake me when you need me!",
            "Taking a nap. Just say 'byte' when you're back!",
            "Sleep mode activated. Call me when you need help!",
            "Resting now. I'll be here when you need me!"
        ]
    
    def get_greeting(self):
        """Get a random greeting."""
        return random.choice(self.greetings)
    
    def get_acknowledgment(self):
        """Get a random acknowledgment."""
        return random.choice(self.acknowledgments)
    
    def get_success_message(self):
        """Get a random success message."""
        return random.choice(self.success_messages)
    
    def get_feedback_question(self):
        """Get a random feedback question."""
        return random.choice(self.feedback_questions)
    
    def get_sleep_message(self):
        """Get a random sleep message."""
        return random.choice(self.sleep_messages)


def main():
    print_header("🤖 Byte - Your Interactive Voice Assistant")
    
    print("Features:")
    print("  ✅ Wake word: 'byte'")
    print("  ✅ Interactive responses and feedback")
    print("  ✅ Asks for next task after completion")
    print("  ✅ Sleep mode (say 'sleep' to pause)")
    print("  ✅ Optimized for Indian English")
    print()
    
    # Check dependencies
    try:
        import speech_recognition as sr
        print("✅ Speech recognition available")
    except ImportError:
        print("❌ speech_recognition not installed")
        print("   Install with: pip install SpeechRecognition pyaudio")
        return
    
    # Load components
    try:
        from src.core.indian_english_voice_processor import IndianEnglishVoiceProcessor
        from src.core.nlp_processor import NLPProcessor
        from src.automation.task_engine import TaskEngine
        from src.core.screen_agent import ScreenAgent
        print("✅ Automation components loaded")
    except Exception as e:
        print(f"❌ Error loading components: {e}")
        return
    
    # Initialize
    print("\n🔧 Initializing Byte...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Initialize with wake word "byte"
        voice = IndianEnglishVoiceProcessor(
            use_whisper=False,
            use_gpt_enhancement=False,
            wake_word="byte",
            language="en-IN"
        )
        
        nlp = NLPProcessor()
        screen_agent = ScreenAgent()
        engine = TaskEngine(screen_agent)
        assistant = ByteAssistant()
        
        print("✅ Byte is ready!")
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return
    
    # Register handlers
    try:
        from src.automation.handlers import VSCodeHandler, GmailHandler, LinkedInHandler, BrowserHandler
        from src.core.nlp_processor import ApplicationType
        
        vscode_handler = VSCodeHandler(screen_agent)
        gmail_handler = GmailHandler(screen_agent)
        linkedin_handler = LinkedInHandler(screen_agent)
        browser_handler = BrowserHandler(screen_agent)
        
        engine.register_app_handler(ApplicationType.VSCODE, vscode_handler.handle_command)
        engine.register_app_handler(ApplicationType.GMAIL, gmail_handler.handle_command)
        engine.register_app_handler(ApplicationType.LINKEDIN, linkedin_handler.handle_command)
        engine.register_app_handler(ApplicationType.CHROME, browser_handler.handle_command)
        print("✅ Handlers registered")
    except Exception as e:
        print(f"⚠️  Warning: Some handlers failed: {e}")
    
    # Start interactive mode
    run_interactive_mode(voice, nlp, engine, assistant)


def run_interactive_mode(voice, nlp, engine, assistant):
    """Run interactive mode with wake word and feedback."""
    print_header("🤖 Byte Interactive Mode")
    
    print("How to use:")
    print("  1. Say 'byte' to wake me up")
    print("  2. I'll greet you and ask what you need")
    print("  3. Speak your command")
    print("  4. I'll execute and ask for feedback")
    print("  5. Say 'sleep' to put me in sleep mode")
    print("  6. Say 'byte' again to wake me up")
    print()
    print("Example commands:")
    print("  • 'Open Gmail only'")
    print("  • 'Search for Python tutorials na'")
    print("  • 'Do one thing, open VSCode'")
    print("  • 'Sleep' (to pause)")
    print()
    print("Press Ctrl+C to exit completely")
    print()
    
    # Initial greeting
    greeting = assistant.get_greeting()
    print(f"\n🤖 Byte: {greeting}")
    voice.speak(greeting, async_speech=True)
    
    print(f"\n🎤 Listening for wake word 'byte'...")
    print("   (Speak naturally, I'm optimized for Indian English)")
    print()
    
    is_awake = True
    waiting_for_command = False
    
    try:
        while True:
            # Listen for speech
            if is_awake:
                if waiting_for_command:
                    # Already awake, waiting for command
                    print("\n" + "-" * 70)
                    print("🎤 Listening for your command...")
                    command_text = voice.listen_once(
                        enhance_prompt=False,
                        timeout=20,
                        phrase_time_limit=30
                    )
                    waiting_for_command = False
                else:
                    # Listen for wake word
                    print(f"🎤 Say 'byte' to give me a command...")
                    command_text = voice.listen_once(
                        enhance_prompt=False,
                        timeout=30,
                        phrase_time_limit=30
                    )
            else:
                # In sleep mode, only listen for wake word
                print("😴 Sleeping... Say 'byte' to wake me up")
                command_text = voice.listen_once(
                    enhance_prompt=False,
                    timeout=30,
                    phrase_time_limit=30
                )
            
            if not command_text:
                continue
            
            command_lower = command_text.lower().strip()
            
            # Check for wake word
            if "byte" in command_lower or "bite" in command_lower or "bait" in command_lower:
                if not is_awake:
                    # Wake up from sleep
                    is_awake = True
                    greeting = assistant.get_greeting()
                    print(f"\n🤖 Byte: {greeting}")
                    voice.speak(greeting, async_speech=True)
                    waiting_for_command = True
                    continue
                else:
                    # Already awake, acknowledge wake word
                    greeting = assistant.get_greeting()
                    print(f"\n🤖 Byte: {greeting}")
                    voice.speak(greeting, async_speech=True)
                    waiting_for_command = True
                    continue
            
            # Check for sleep command
            if "sleep" in command_lower or "so ja" in command_lower or "rest" in command_lower:
                is_awake = False
                sleep_msg = assistant.get_sleep_message()
                print(f"\n🤖 Byte: {sleep_msg}")
                voice.speak(sleep_msg, async_speech=True)
                print()
                continue
            
            # Check for exit commands
            if any(word in command_lower for word in ["exit", "quit", "goodbye", "bye bye"]):
                print("\n🤖 Byte: Goodbye! Have a great day!")
                voice.speak("Goodbye! Have a great day!", async_speech=True)
                break
            
            # Execute command
            if is_awake:
                execute_with_feedback(command_text, nlp, engine, voice, assistant)
                
                # Ask for feedback
                feedback_q = assistant.get_feedback_question()
                print(f"\n🤖 Byte: {feedback_q}")
                voice.speak(feedback_q, async_speech=True)
                
                # Listen for response
                print("\n🎤 Listening for your response...")
                response = voice.listen_once(
                    enhance_prompt=False,
                    timeout=15,
                    phrase_time_limit=20
                )
                
                if response:
                    response_lower = response.lower().strip()
                    
                    # Check if user wants to sleep
                    if "sleep" in response_lower or "no" in response_lower or "nothing" in response_lower:
                        sleep_msg = assistant.get_sleep_message()
                        print(f"\n🤖 Byte: {sleep_msg}")
                        voice.speak(sleep_msg, async_speech=True)
                        is_awake = False
                    elif "yes" in response_lower or "yeah" in response_lower:
                        print("\n🤖 Byte: Sure! What do you need?")
                        voice.speak("Sure! What do you need?", async_speech=True)
                        waiting_for_command = True
                    else:
                        # Treat response as new command
                        execute_with_feedback(response, nlp, engine, voice, assistant)
                        
                        # Ask again
                        feedback_q = assistant.get_feedback_question()
                        print(f"\n🤖 Byte: {feedback_q}")
                        voice.speak(feedback_q, async_speech=True)
                        waiting_for_command = True
                else:
                    # No response, go to sleep
                    sleep_msg = assistant.get_sleep_message()
                    print(f"\n🤖 Byte: {sleep_msg}")
                    voice.speak(sleep_msg, async_speech=True)
                    is_awake = False
            
    except KeyboardInterrupt:
        print("\n\n🤖 Byte: Shutting down. Goodbye!")
        voice.speak("Shutting down. Goodbye!", async_speech=True)


def execute_with_feedback(command_text, nlp, engine, voice, assistant):
    """Execute command with interactive feedback."""
    print(f"\n📝 You said: {command_text}")
    
    # Acknowledge
    ack = assistant.get_acknowledgment()
    print(f"🤖 Byte: {ack}")
    voice.speak(ack, async_speech=True)
    
    try:
        # Parse command
        parsed = nlp.parse_command(command_text)
        
        print(f"🧠 Understanding: {parsed.action.value} on {parsed.application.value}")
        
        if parsed.confidence < 0.3:
            print("⚠️  Low confidence, but I'll try...")
            voice.speak("I'm not fully sure, but let me try", async_speech=True)
        
        # Execute
        result = engine.execute_command(parsed)
        
        # Show result with feedback
        if result.status.value == 'completed':
            success_msg = assistant.get_success_message()
            print(f"✅ {success_msg}")
            if result.execution_time > 0:
                print(f"⏱️  Time: {result.execution_time:.2f}s")
            voice.speak(success_msg, async_speech=True)
            assistant.task_count += 1
        else:
            print(f"❌ Failed: {result.message}")
            voice.speak(f"Sorry, that didn't work. {result.message}", async_speech=True)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        voice.speak("Sorry, I encountered an error", async_speech=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

