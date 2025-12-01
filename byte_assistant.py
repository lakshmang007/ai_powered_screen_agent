#!/usr/bin/env python3
"""
Byte - Your Smart Indian English Voice Assistant

Wake word: "byte"
- Greets you when you wake it up
- Executes your commands
- Asks for feedback after each task
- Goes to sleep when you say "sleep"
"""

import sys
import os
import random
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))


class BytePersonality:
    """Byte's personality and responses."""
    
    GREETINGS = [
        "Hello! What can I do for you?",
        "Hi! Byte here, ready to help!",
        "Hey! What do you need?",
        "Namaste! How can I assist?",
        "Yes! What's the task?"
    ]
    
    ACKNOWLEDGMENTS = [
        "Got it!",
        "Sure thing!",
        "On it!",
        "Okay!",
        "Working on it!"
    ]
    
    SUCCESS = [
        "Done!",
        "Complete!",
        "Finished!",
        "All done!",
        "Success!"
    ]
    
    FEEDBACK_QUESTIONS = [
        "Anything else?",
        "What's next?",
        "Need anything else, or should I sleep?",
        "Can I help with something else?",
        "More work, or should I rest?"
    ]
    
    SLEEP_MESSAGES = [
        "Going to sleep. Say 'byte' to wake me!",
        "Sleeping now. Wake me when you need me!",
        "Taking a nap. Call me anytime!",
        "Sleep mode. I'll be here!",
        "Resting. Say 'byte' when ready!"
    ]
    
    @staticmethod
    def random_choice(messages):
        return random.choice(messages)


def print_box(text, char="="):
    """Print text in a box."""
    print("\n" + char * 70)
    print(text.center(70))
    print(char * 70 + "\n")


def main():
    print_box("🤖 BYTE - Your Voice Assistant", "=")
    
    print("Wake Word: 'byte'")
    print("Sleep Command: 'sleep'")
    print("Exit: Press Ctrl+C")
    print()
    
    # Initialize
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from src.core.indian_english_voice_processor import IndianEnglishVoiceProcessor
        from src.core.nlp_processor import NLPProcessor
        from src.automation.task_engine import TaskEngine
        from src.core.screen_agent import ScreenAgent
        from src.automation.handlers import VSCodeHandler, GmailHandler, LinkedInHandler, BrowserHandler
        from src.core.nlp_processor import ApplicationType
        
        print("🔧 Initializing Byte...")
        
        voice = IndianEnglishVoiceProcessor(
            wake_word="byte",
            language="en-IN",
            use_whisper=False,
            use_gpt_enhancement=False
        )
        
        nlp = NLPProcessor()
        screen_agent = ScreenAgent()
        engine = TaskEngine(screen_agent)
        
        # Register handlers
        vscode_handler = VSCodeHandler(screen_agent)
        gmail_handler = GmailHandler(screen_agent)
        linkedin_handler = LinkedInHandler(screen_agent)
        browser_handler = BrowserHandler(screen_agent)
        
        engine.register_app_handler(ApplicationType.VSCODE, vscode_handler.handle_command)
        engine.register_app_handler(ApplicationType.GMAIL, gmail_handler.handle_command)
        engine.register_app_handler(ApplicationType.LINKEDIN, linkedin_handler.handle_command)
        engine.register_app_handler(ApplicationType.CHROME, browser_handler.handle_command)
        
        print("✅ Byte is ready!\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Start
    run_byte(voice, nlp, engine)


def run_byte(voice, nlp, engine):
    """Main Byte interaction loop."""
    
    print_box("🤖 Byte is Active!", "-")
    
    # Initial greeting
    greeting = BytePersonality.random_choice(BytePersonality.GREETINGS)
    print(f"🤖 Byte: {greeting}\n")
    voice.speak(greeting)
    
    is_awake = True
    task_count = 0
    
    try:
        while True:
            print("-" * 70)
            
            if is_awake:
                # Awake mode - listen for commands
                print("🎤 Listening... (say 'byte' for new task, or give command)")
                command = listen_for_input(voice)
                
                if not command:
                    continue
                
                cmd_lower = command.lower().strip()
                
                # Check for sleep
                if is_sleep_command(cmd_lower):
                    is_awake = False
                    sleep_msg = BytePersonality.random_choice(BytePersonality.SLEEP_MESSAGES)
                    print(f"\n😴 Byte: {sleep_msg}\n")
                    voice.speak(sleep_msg)
                    continue
                
                # Check for exit
                if is_exit_command(cmd_lower):
                    print("\n🤖 Byte: Goodbye!\n")
                    voice.speak("Goodbye!")
                    break
                
                # Check for wake word (new task)
                if is_wake_word(cmd_lower):
                    greeting = BytePersonality.random_choice(BytePersonality.GREETINGS)
                    print(f"\n🤖 Byte: {greeting}\n")
                    voice.speak(greeting)
                    
                    # Listen for the actual command
                    print("🎤 Listening for your command...")
                    command = listen_for_input(voice)
                    if not command:
                        continue
                    cmd_lower = command.lower().strip()
                
                # Execute command
                if not is_sleep_command(cmd_lower) and not is_exit_command(cmd_lower):
                    success = execute_command(command, nlp, engine, voice)
                    if success:
                        task_count += 1
                    
                    # Ask for feedback
                    time.sleep(0.5)
                    feedback_q = BytePersonality.random_choice(BytePersonality.FEEDBACK_QUESTIONS)
                    print(f"\n🤖 Byte: {feedback_q}\n")
                    voice.speak(feedback_q)
                    
                    # Listen for response
                    print("🎤 Listening for response...")
                    response = listen_for_input(voice, timeout=15)
                    
                    if response:
                        resp_lower = response.lower().strip()
                        
                        if is_sleep_command(resp_lower) or is_negative_response(resp_lower):
                            is_awake = False
                            sleep_msg = BytePersonality.random_choice(BytePersonality.SLEEP_MESSAGES)
                            print(f"\n😴 Byte: {sleep_msg}\n")
                            voice.speak(sleep_msg)
                        elif is_positive_response(resp_lower):
                            print("\n🤖 Byte: Sure! What do you need?\n")
                            voice.speak("Sure! What do you need?")
                        else:
                            # Treat as new command
                            execute_command(response, nlp, engine, voice)
                            task_count += 1
                    else:
                        # No response - go to sleep
                        is_awake = False
                        sleep_msg = BytePersonality.random_choice(BytePersonality.SLEEP_MESSAGES)
                        print(f"\n😴 Byte: {sleep_msg}\n")
                        voice.speak(sleep_msg)
            
            else:
                # Sleep mode - only wake on wake word
                print("😴 Sleeping... Say 'byte' to wake me up")
                command = listen_for_input(voice, timeout=60)
                
                if command and is_wake_word(command.lower()):
                    is_awake = True
                    greeting = BytePersonality.random_choice(BytePersonality.GREETINGS)
                    print(f"\n🤖 Byte: {greeting}\n")
                    voice.speak(greeting)
    
    except KeyboardInterrupt:
        print(f"\n\n🤖 Byte: Completed {task_count} tasks. Goodbye!\n")
        voice.speak("Goodbye!")


def listen_for_input(voice, timeout=20):
    """Listen for voice input."""
    try:
        command = voice.listen_once(
            enhance_prompt=False,
            timeout=timeout,
            phrase_time_limit=30
        )
        return command
    except Exception as e:
        print(f"⚠️  Listening error: {e}")
        return None


def execute_command(command_text, nlp, engine, voice):
    """Execute a command with feedback."""
    print(f"\n📝 Command: {command_text}")
    
    # Acknowledge
    ack = BytePersonality.random_choice(BytePersonality.ACKNOWLEDGMENTS)
    print(f"🤖 Byte: {ack}")
    voice.speak(ack)
    
    try:
        # Parse
        parsed = nlp.parse_command(command_text)
        print(f"🧠 Action: {parsed.action.value} on {parsed.application.value}")
        
        # Execute
        result = engine.execute_command(parsed)
        
        # Feedback
        if result.status.value == 'completed':
            success_msg = BytePersonality.random_choice(BytePersonality.SUCCESS)
            print(f"✅ {success_msg}")
            voice.speak(success_msg)
            return True
        else:
            print(f"❌ Failed: {result.message}")
            voice.speak("Sorry, that didn't work")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        voice.speak("Error occurred")
        return False


def is_wake_word(text):
    """Check if text contains wake word."""
    return any(word in text for word in ["byte", "bite", "bait"])


def is_sleep_command(text):
    """Check if text is a sleep command."""
    return any(word in text for word in ["sleep", "so ja", "rest", "nap"])


def is_exit_command(text):
    """Check if text is an exit command."""
    return any(word in text for word in ["exit", "quit", "goodbye", "bye bye", "shutdown"])


def is_positive_response(text):
    """Check if response is positive."""
    return any(word in text for word in ["yes", "yeah", "yep", "sure", "okay", "ok", "han", "haan"])


def is_negative_response(text):
    """Check if response is negative."""
    return any(word in text for word in ["no", "nope", "nothing", "nahi", "na", "nah"])


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

