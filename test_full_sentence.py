#!/usr/bin/env python3
"""
Test script to verify full sentence recognition.
This will help you test if "open gmail only" is captured completely.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def main():
    print("\n" + "=" * 70)
    print("Full Sentence Recognition Test".center(70))
    print("=" * 70)
    print()
    print("This test will help verify that the system captures your FULL sentence")
    print("without cutting off mid-speech.")
    print()
    
    # Load voice processor
    try:
        from src.core.indian_english_voice_processor import IndianEnglishVoiceProcessor
        print("✅ Indian English Voice Processor loaded")
    except Exception as e:
        print(f"❌ Error loading voice processor: {e}")
        return
    
    # Initialize
    print("\n🔧 Initializing with VERY PATIENT settings...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        voice = IndianEnglishVoiceProcessor(
            language="en-IN",
            use_whisper=False,
            use_gpt_enhancement=False
        )
        
        print("✅ Voice processor initialized")
        print()
        print("Settings:")
        print(f"  • Pause threshold: {voice.recognizer.pause_threshold}s (waits this long for pauses)")
        print(f"  • Non-speaking duration: {voice.recognizer.non_speaking_duration}s (silence before stopping)")
        print(f"  • Energy threshold: {voice.recognizer.energy_threshold}")
        print()
        
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return
    
    # Test sentences
    test_sentences = [
        "open gmail only",
        "search for python tutorials na",
        "do one thing open vscode",
        "kindly open linkedin",
        "please search google for machine learning"
    ]
    
    print("=" * 70)
    print("Test Sentences to Try".center(70))
    print("=" * 70)
    print()
    for i, sentence in enumerate(test_sentences, 1):
        print(f"{i}. '{sentence}'")
    print()
    print("=" * 70)
    print()
    
    print("Instructions:")
    print("  1. When you see 'Ready', speak your FULL sentence")
    print("  2. The system will wait 2 seconds of silence before stopping")
    print("  3. Speak naturally at your normal pace")
    print("  4. Don't rush - the system is VERY patient now")
    print()
    print("Press Ctrl+C to exit")
    print()
    
    test_count = 0
    
    try:
        while True:
            test_count += 1
            print("\n" + "=" * 70)
            print(f"Test #{test_count}")
            print("=" * 70)
            
            # Listen
            command = voice.listen_once(
                timeout=20,              # Wait 20 seconds for you to start
                phrase_time_limit=30     # Allow 30 seconds of speaking
            )
            
            if command:
                print("\n" + "✅" * 35)
                print(f"CAPTURED: '{command}'")
                print("✅" * 35)
                
                # Check if it's a full sentence
                word_count = len(command.split())
                print(f"\nWord count: {word_count} words")
                
                if word_count >= 3:
                    print("✅ Good! Captured multiple words")
                elif word_count == 2:
                    print("⚠️  Only 2 words - try speaking a bit slower")
                else:
                    print("❌ Only 1 word captured - the system cut off too early")
                    print("   Try again and speak more slowly")
                
                # Analyze what was captured
                print("\nAnalysis:")
                if "open" in command and "gmail" in command:
                    print("  ✅ Captured both 'open' and 'gmail'")
                    if "only" in command:
                        print("  ✅ Captured 'only' too - PERFECT!")
                    else:
                        print("  ⚠️  Missing 'only' - try pausing less between words")
                
            else:
                print("\n❌ No speech detected")
                print("   Make sure your microphone is working")
            
            print("\n" + "-" * 70)
            
            # Ask if user wants to continue
            try:
                response = input("\nTry again? (Enter to continue, 'q' to quit): ").strip().lower()
                if response == 'q':
                    break
            except:
                continue
    
    except KeyboardInterrupt:
        print("\n\n👋 Test complete!")
        print(f"\nTotal tests: {test_count}")
    
    print("\n" + "=" * 70)
    print("Tips for Better Recognition".center(70))
    print("=" * 70)
    print()
    print("If the system is still cutting off:")
    print()
    print("1. Speak slightly SLOWER")
    print("   - Pause briefly between words")
    print("   - Example: 'open ... gmail ... only'")
    print()
    print("2. Speak slightly LOUDER")
    print("   - Make sure microphone picks up your voice")
    print()
    print("3. Reduce pauses WITHIN your sentence")
    print("   - The system stops after 2 seconds of silence")
    print("   - Keep speaking without long pauses")
    print()
    print("4. Use a better microphone")
    print("   - Headset microphone works best")
    print("   - USB microphone is even better")
    print()
    print("5. Calibrate in your environment")
    print("   - Run: voice.calibrate_microphone()")
    print()
    print("=" * 70)
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

