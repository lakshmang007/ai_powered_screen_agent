#!/usr/bin/env python3
"""
Indian English Voice Automation Demo

Features:
- Optimized for Indian English accents
- Longer listening duration (doesn't exit quickly)
- Multiple recognition engines with fallback
- Natural Indian English command patterns
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(text.center(70))
    print("=" * 70 + "\n")


def main():
    print_header("🎙️ Indian English Voice Automation")
    
    print("Features:")
    print("  ✅ Optimized for Indian English accents")
    print("  ✅ Longer listening time (won't exit quickly)")
    print("  ✅ Multiple recognition engines with fallback")
    print("  ✅ Understands natural Indian English patterns")
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
    print("\n🔧 Initializing system...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Initialize Indian English voice processor
        voice = IndianEnglishVoiceProcessor(
            use_whisper=False,  # Set to True if you have OpenAI credits
            use_gpt_enhancement=False,  # Set to True if you have OpenAI credits
            wake_word="computer",
            language="en-IN"  # Indian English
        )
        
        nlp = NLPProcessor()
        screen_agent = ScreenAgent()
        engine = TaskEngine(screen_agent)
        
        print("✅ System ready!")
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
    
    # Show menu
    print_header("Choose Mode")
    
    print("1. Single Command Mode")
    print("   - Speak one command at a time")
    print("   - Extended listening time (won't exit quickly)")
    print()
    
    print("2. Continuous Listening Mode")
    print("   - Always listening with wake word")
    print("   - Say 'computer' then your command")
    print()
    
    print("3. Continuous Without Wake Word")
    print("   - Always listening (no wake word needed)")
    print("   - Just speak your commands")
    print()
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        run_single_command_mode(voice, nlp, engine)
    elif choice == "2":
        run_continuous_with_wake_word(voice, nlp, engine)
    elif choice == "3":
        run_continuous_no_wake_word(voice, nlp, engine)
    else:
        print("Invalid choice!")


def run_single_command_mode(voice, nlp, engine):
    """Single command mode with extended listening."""
    print_header("Single Command Mode - Indian English")
    
    print("Examples of commands you can say:")
    print("  • 'Open Gmail only'")
    print("  • 'Search for Python tutorials na'")
    print("  • 'Do one thing, open VSCode'")
    print("  • 'Kindly open LinkedIn'")
    print("  • 'Open that Chrome browser'")
    print("  • 'Search Google for machine learning'")
    print()
    print("Press Ctrl+C to exit")
    print()
    
    try:
        while True:
            print("\n" + "-" * 70)
            
            # Listen with VERY extended timeout - won't cut off mid-sentence
            command_text = voice.listen_once(
                enhance_prompt=False,  # Set to True if you have OpenAI credits
                timeout=20,  # Wait 20 seconds for speech to start
                phrase_time_limit=30  # Allow 30 seconds of speaking
            )
            
            if command_text:
                execute_command(command_text, nlp, engine, voice)
            else:
                print("❌ No command detected. Try again!")
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")


def run_continuous_with_wake_word(voice, nlp, engine):
    """Continuous listening with wake word."""
    print_header("Continuous Mode with Wake Word")
    
    print("How to use:")
    print("  1. Say 'computer' to activate")
    print("  2. Speak your command")
    print("  3. System executes and waits for next 'computer'")
    print()
    print("Examples:")
    print("  • 'Computer, open Gmail'")
    print("  • 'Computer, search for Python tutorials'")
    print("  • 'Computer, open VSCode'")
    print()
    print("Press Ctrl+C to stop")
    print()
    
    def handle_command(text):
        execute_command(text, nlp, engine, voice)
        print(f"\n🎤 Say 'computer' for next command...")
    
    try:
        voice.start_continuous_listening(
            callback=handle_command,
            use_wake_word=True,
            enhance_prompts=False  # Set to True if you have OpenAI credits
        )
        
        # Keep running
        while True:
            import time
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping...")
        voice.stop_continuous_listening()
        print("👋 Goodbye!")


def run_continuous_no_wake_word(voice, nlp, engine):
    """Continuous listening without wake word."""
    print_header("Continuous Mode - No Wake Word")
    
    print("⚠️  Warning: Always listening mode!")
    print("   System will respond to any speech it hears")
    print()
    print("Just speak your commands naturally:")
    print("  • 'Open Gmail'")
    print("  • 'Search for Python'")
    print("  • 'Open VSCode'")
    print()
    print("Press Ctrl+C to stop")
    print()
    
    def handle_command(text):
        execute_command(text, nlp, engine, voice)
    
    try:
        voice.start_continuous_listening(
            callback=handle_command,
            use_wake_word=False,
            enhance_prompts=False
        )
        
        # Keep running
        while True:
            import time
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping...")
        voice.stop_continuous_listening()
        print("👋 Goodbye!")


def execute_command(command_text, nlp, engine, voice):
    """Execute a voice command."""
    print(f"\n📝 Processing: {command_text}")
    
    try:
        # Parse command
        parsed = nlp.parse_command(command_text)
        
        print(f"🧠 Understood: {parsed.action.value} on {parsed.application.value}")
        
        if parsed.confidence < 0.3:
            print("⚠️  Warning: Low confidence - trying anyway...")
        
        # Execute
        result = engine.execute_command(parsed)
        
        # Show result
        if result.status.value == 'completed':
            print(f"✅ Success: {result.message}")
            if result.execution_time > 0:
                print(f"⏱️  Time: {result.execution_time:.2f}s")
            voice.speak("Done", async_speech=True)
        else:
            print(f"❌ Failed: {result.message}")
            voice.speak("Failed", async_speech=True)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        voice.speak("Error occurred", async_speech=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

