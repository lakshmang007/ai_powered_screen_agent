#!/usr/bin/env python3
"""
Test TTS to ensure it speaks multiple times without errors.
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core.indian_english_voice_processor import IndianEnglishVoiceProcessor

def main():
    print("Testing TTS...")
    
    voice = IndianEnglishVoiceProcessor(
        wake_word="test",
        language="en-IN"
    )
    
    print("\n1. First speech...")
    voice.speak("Hello, this is test number one.")
    time.sleep(1)
    
    print("\n2. Second speech...")
    voice.speak("This is test number two.")
    time.sleep(1)
    
    print("\n3. Third speech...")
    voice.speak("This is test number three.")
    time.sleep(1)
    
    print("\n4. Fourth speech...")
    voice.speak("This is test number four.")
    time.sleep(1)
    
    print("\n5. Fifth speech...")
    voice.speak("This is test number five.")
    
    print("\n✅ All tests completed!")
    print("If you heard all 5 speeches, TTS is working correctly.")
    
    time.sleep(2)
    voice.cleanup()

if __name__ == "__main__":
    main()

