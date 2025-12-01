#!/usr/bin/env python3
"""
Test microphone availability.
"""

import sys

def test_microphone():
    """Test if microphone is available."""
    print("="*70)
    print("MICROPHONE TEST".center(70))
    print("="*70)
    
    try:
        import speech_recognition as sr
        
        print("\n1. Testing microphone initialization...")
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()
        
        print("✅ Microphone object created")
        
        print("\n2. Testing microphone access...")
        with microphone as source:
            print("✅ Microphone opened successfully")
            print(f"   Sample rate: {source.SAMPLE_RATE}")
            print(f"   Chunk size: {source.CHUNK}")
            
            print("\n3. Testing ambient noise calibration...")
            print("   Calibrating for 1 second...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"✅ Calibration complete")
            print(f"   Energy threshold: {recognizer.energy_threshold}")
        
        print("\n4. Testing speech recognition...")
        print("   Please say something (5 seconds)...")
        
        with microphone as source:
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                print("✅ Audio captured")
                
                print("\n5. Testing Google Speech Recognition...")
                text = recognizer.recognize_google(audio, language="en-IN")
                print(f"✅ Recognized: '{text}'")
                
            except sr.WaitTimeoutError:
                print("⚠️  No speech detected (timeout)")
            except sr.UnknownValueError:
                print("⚠️  Could not understand audio")
            except sr.RequestError as e:
                print(f"❌ API error: {e}")
        
        print("\n" + "="*70)
        print("✅ MICROPHONE TEST PASSED!".center(70))
        print("="*70)
        print("\nYour microphone is working correctly!")
        print("Byte should be able to use it.")
        
        return True
        
    except ImportError:
        print("\n❌ speech_recognition not installed!")
        print("   Install with: pip install SpeechRecognition")
        return False
        
    except OSError as e:
        print(f"\n❌ Microphone error: {e}")
        print("\nPossible issues:")
        print("  1. No microphone connected")
        print("  2. Microphone in use by another application")
        print("  3. Microphone permissions not granted")
        print("  4. Audio drivers not installed")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_microphone()
    
    if not success:
        print("\n" + "="*70)
        print("TROUBLESHOOTING TIPS".center(70))
        print("="*70)
        print("\n1. Check if microphone is connected")
        print("2. Close other applications using microphone (Zoom, Teams, etc.)")
        print("3. Check Windows sound settings:")
        print("   - Right-click speaker icon → Sounds")
        print("   - Recording tab → Check if microphone is enabled")
        print("4. Grant microphone permissions:")
        print("   - Settings → Privacy → Microphone")
        print("   - Allow apps to access microphone")
        print("5. Update audio drivers")
        print("="*70)
    
    sys.exit(0 if success else 1)

