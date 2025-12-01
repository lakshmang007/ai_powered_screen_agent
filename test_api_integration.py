#!/usr/bin/env python3
"""
Quick test script to verify OpenAI API integration.
This will test your API key and voice processing setup.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_env_loading():
    """Test if .env file loads correctly."""
    print("=" * 60)
    print("Testing Environment Configuration")
    print("=" * 60)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ python-dotenv loaded successfully")
    except ImportError:
        print("❌ python-dotenv not installed")
        print("   Install with: pip install python-dotenv")
        return False
    
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"✅ OpenAI API key found: {api_key[:20]}...{api_key[-4:]}")
        return True
    else:
        print("❌ OpenAI API key not found in environment")
        return False


def test_openai_import():
    """Test if OpenAI library is installed."""
    print("\n" + "=" * 60)
    print("Testing OpenAI Library")
    print("=" * 60)
    
    try:
        import openai
        print(f"✅ OpenAI library imported successfully (version: {openai.__version__})")
        return True
    except ImportError:
        print("❌ OpenAI library not installed")
        print("   Install with: pip install openai")
        return False


def test_openai_api():
    """Test if OpenAI API key works."""
    print("\n" + "=" * 60)
    print("Testing OpenAI API Connection")
    print("=" * 60)

    try:
        from dotenv import load_dotenv
        from openai import OpenAI

        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")

        print("🔄 Testing API connection with a simple request...")

        # Test with a simple completion (new API v2.x)
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'API test successful' if you can read this."}
            ],
            max_tokens=20
        )

        result = response.choices[0].message.content
        print(f"✅ API connection successful!")
        print(f"   Response: {result}")
        return True

    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False


def test_speech_recognition():
    """Test if speech recognition is available."""
    print("\n" + "=" * 60)
    print("Testing Speech Recognition")
    print("=" * 60)
    
    try:
        import speech_recognition as sr
        print("✅ speech_recognition library imported")
        
        # Test microphone access
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                print("✅ Microphone access successful")
                return True
        except Exception as e:
            print(f"⚠️  Microphone access failed: {e}")
            print("   Voice input may not work")
            return False
            
    except ImportError:
        print("❌ speech_recognition not installed")
        print("   Install with: pip install SpeechRecognition pyaudio")
        return False


def test_enhanced_voice_processor():
    """Test if enhanced voice processor can be imported."""
    print("\n" + "=" * 60)
    print("Testing Enhanced Voice Processor")
    print("=" * 60)
    
    try:
        from src.core.enhanced_voice_processor import EnhancedVoiceProcessor
        print("✅ EnhancedVoiceProcessor imported successfully")
        
        # Try to initialize
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            voice = EnhancedVoiceProcessor(
                use_whisper=True,
                use_gpt_enhancement=True,
                wake_word="computer"
            )
            print("✅ EnhancedVoiceProcessor initialized successfully")
            print(f"   - Whisper enabled: {voice.use_whisper}")
            print(f"   - GPT enhancement enabled: {voice.use_gpt_enhancement}")
            print(f"   - Wake word: '{voice.wake_word}'")
            return True
        except Exception as e:
            print(f"⚠️  Initialization warning: {e}")
            print("   Some features may not work")
            return False
            
    except ImportError as e:
        print(f"❌ EnhancedVoiceProcessor import failed: {e}")
        return False


def test_prompt_enhancement():
    """Test GPT-4 prompt enhancement."""
    print("\n" + "=" * 60)
    print("Testing Prompt Enhancement")
    print("=" * 60)
    
    try:
        from dotenv import load_dotenv
        from src.core.enhanced_voice_processor import EnhancedVoiceProcessor
        
        load_dotenv()
        voice = EnhancedVoiceProcessor(use_gpt_enhancement=True)
        
        test_commands = [
            "open that email thing",
            "search for python",
            "post on social media"
        ]
        
        print("🔄 Testing prompt enhancement with sample commands...\n")
        
        for cmd in test_commands:
            try:
                enhanced = voice._enhance_prompt(cmd)
                print(f"   Original: '{cmd}'")
                print(f"   Enhanced: '{enhanced}'")
                print()
            except Exception as e:
                print(f"   ❌ Enhancement failed for '{cmd}': {e}")
                return False
        
        print("✅ Prompt enhancement working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Prompt enhancement test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n🎙️  OpenAI API Integration Test")
    print("=" * 60)
    print()
    
    results = []
    
    # Run tests
    results.append(("Environment Loading", test_env_loading()))
    results.append(("OpenAI Import", test_openai_import()))
    results.append(("OpenAI API Connection", test_openai_api()))
    results.append(("Speech Recognition", test_speech_recognition()))
    results.append(("Enhanced Voice Processor", test_enhanced_voice_processor()))
    results.append(("Prompt Enhancement", test_prompt_enhancement()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 All tests passed! Your integration is ready to use!")
        print("\nNext steps:")
        print("1. Run the demo: python examples/voice_automation_example.py")
        print("2. Try voice commands with automatic enhancement")
        print("3. Read QUICK_START_VOICE.md for usage examples")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install missing packages: pip install openai python-dotenv SpeechRecognition")
        print("- Check your API key in .env file")
        print("- Verify internet connection")
    
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test cancelled")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

