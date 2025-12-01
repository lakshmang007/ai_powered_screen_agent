#!/usr/bin/env python3
"""
Basic Voice Demo - Works without OpenAI credits
Uses Google Speech Recognition (free) for voice input
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def main():
    print("\n🎙️  Basic Voice Automation Demo")
    print("=" * 60)
    print()
    print("This demo uses FREE Google Speech Recognition")
    print("No API credits needed!")
    print()
    
    # Check dependencies
    try:
        import speech_recognition as sr
        print("✅ Speech recognition available")
    except ImportError:
        print("❌ speech_recognition not installed")
        print("   Install with: pip install SpeechRecognition pyaudio")
        return
    
    try:
        from src.core.nlp_processor import NLPProcessor
        from src.automation.task_engine import TaskEngine
        from src.core.screen_agent import ScreenAgent
        print("✅ Automation components loaded")
    except Exception as e:
        print(f"❌ Error loading components: {e}")
        return
    
    # Initialize components
    print("\n🔧 Initializing automation system...")
    try:
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()
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
        print(f"⚠️  Warning: Some handlers failed to load: {e}")
    
    print("\n" + "=" * 60)
    print("Ready for Voice Commands!")
    print("=" * 60)
    print()
    print("Try saying:")
    print("  - 'open Gmail'")
    print("  - 'search for Python tutorials'")
    print("  - 'open VSCode'")
    print("  - 'scroll down'")
    print()
    print("Press Ctrl+C to exit")
    print()
    
    # Main loop
    try:
        while True:
            try:
                print("\n🎤 Listening... (speak now)")
                
                with microphone as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    print("🎤 Ready - speak your command...")
                    audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
                
                print("🔄 Processing speech...")
                
                # Transcribe with Google
                try:
                    text = recognizer.recognize_google(audio)
                    text = text.strip()
                    print(f"✅ Heard: '{text}'")
                except sr.UnknownValueError:
                    print("❌ Could not understand audio")
                    continue
                except sr.RequestError as e:
                    print(f"❌ Speech recognition error: {e}")
                    continue
                
                # Parse command
                print(f"\n📝 Processing: {text}")
                parsed = nlp.parse_command(text)
                
                print(f"🧠 Understood: {parsed.action.value} on {parsed.application.value}")
                if parsed.confidence < 0.3:
                    print("⚠️  Warning: Low confidence in command understanding")
                
                # Execute command
                result = engine.execute_command(parsed)
                
                # Display result
                if result.status.value == 'completed':
                    print(f"✅ Success: {result.message}")
                    if result.execution_time > 0:
                        print(f"⏱️  Execution time: {result.execution_time:.2f}s")
                else:
                    print(f"❌ Failed: {result.message}")
                
                print("\n" + "-" * 60)
                
            except sr.WaitTimeoutError:
                print("⏱️  No speech detected, try again...")
                continue
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")


if __name__ == "__main__":
    main()

