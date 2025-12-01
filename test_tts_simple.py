#!/usr/bin/env python3
"""
Simple TTS test to diagnose the issue.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_direct_pyttsx3():
    """Test pyttsx3 directly without queue."""
    print("="*70)
    print("TEST 1: Direct pyttsx3 (no queue)")
    print("="*70)
    
    try:
        import pyttsx3
        
        engine = pyttsx3.init()
        engine.setProperty('rate', 160)
        engine.setProperty('volume', 0.9)
        
        print("\n1. Speaking: 'Test one'")
        engine.say("Test one")
        engine.runAndWait()
        print("   ✅ Completed")
        
        time.sleep(0.5)
        
        print("\n2. Speaking: 'Test two'")
        engine.say("Test two")
        engine.runAndWait()
        print("   ✅ Completed")
        
        time.sleep(0.5)
        
        print("\n3. Speaking: 'Test three'")
        engine.say("Test three")
        engine.runAndWait()
        print("   ✅ Completed")
        
        print("\n✅ Direct pyttsx3 test PASSED!")
        print("   If you heard all 3 messages, pyttsx3 works!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Direct pyttsx3 test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_queue_based_tts():
    """Test queue-based TTS like IndianEnglishVoiceProcessor."""
    print("\n" + "="*70)
    print("TEST 2: Queue-based TTS (like IndianEnglishVoiceProcessor)")
    print("="*70)
    
    try:
        import pyttsx3
        import queue
        import threading
        
        # Setup
        tts_queue = queue.Queue()
        tts_running = True
        tts_lock = threading.Lock()
        
        engine = pyttsx3.init()
        engine.setProperty('rate', 160)
        engine.setProperty('volume', 0.9)
        
        def tts_worker():
            """Worker thread for TTS."""
            while tts_running:
                try:
                    text = tts_queue.get(timeout=1)
                    print(f"   🔊 Worker speaking: '{text}'")
                    
                    with tts_lock:
                        engine.say(text)
                        engine.runAndWait()
                    
                    tts_queue.task_done()
                    print(f"   ✅ Worker completed: '{text}'")
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"   ❌ Worker error: {e}")
        
        # Start worker thread
        print("\nStarting TTS worker thread...")
        thread = threading.Thread(target=tts_worker, daemon=True)
        thread.start()
        print("✅ Worker thread started")
        
        # Test speaking
        print("\n1. Queuing: 'Test one'")
        tts_queue.put("Test one")
        time.sleep(3)  # Wait for it to speak
        
        print("\n2. Queuing: 'Test two'")
        tts_queue.put("Test two")
        time.sleep(3)
        
        print("\n3. Queuing: 'Test three'")
        tts_queue.put("Test three")
        time.sleep(3)
        
        # Check if thread is still alive
        if thread.is_alive():
            print("\n✅ Worker thread still alive")
        else:
            print("\n❌ Worker thread DIED!")
            return False
        
        # Stop worker
        tts_running = False
        thread.join(timeout=2)
        
        print("\n✅ Queue-based TTS test PASSED!")
        print("   If you heard all 3 messages, queue-based TTS works!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Queue-based TTS test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_indian_english_voice_processor():
    """Test IndianEnglishVoiceProcessor TTS."""
    print("\n" + "="*70)
    print("TEST 3: IndianEnglishVoiceProcessor TTS")
    print("="*70)
    
    try:
        from src.core.indian_english_voice_processor import IndianEnglishVoiceProcessor
        
        print("\nInitializing IndianEnglishVoiceProcessor...")
        voice = IndianEnglishVoiceProcessor(
            wake_word="byte",
            language="en-IN"
        )
        
        if not voice.tts_engine:
            print("❌ TTS engine not initialized!")
            return False
        
        print("✅ TTS engine initialized")
        
        if not voice.tts_running:
            print("❌ TTS worker not running!")
            return False
        
        print("✅ TTS worker running")
        
        if not voice.tts_thread or not voice.tts_thread.is_alive():
            print("❌ TTS thread not alive!")
            return False
        
        print("✅ TTS thread alive")
        
        # Test speaking
        print("\n1. Speaking: 'Test one'")
        voice.speak("Test one")
        time.sleep(3)
        
        # Check thread still alive
        if not voice.tts_thread.is_alive():
            print("❌ TTS thread DIED after first speak!")
            return False
        print("   ✅ Thread still alive")
        
        print("\n2. Speaking: 'Test two'")
        voice.speak("Test two")
        time.sleep(3)
        
        if not voice.tts_thread.is_alive():
            print("❌ TTS thread DIED after second speak!")
            return False
        print("   ✅ Thread still alive")
        
        print("\n3. Speaking: 'Test three'")
        voice.speak("Test three")
        time.sleep(3)
        
        if not voice.tts_thread.is_alive():
            print("❌ TTS thread DIED after third speak!")
            return False
        print("   ✅ Thread still alive")
        
        # Cleanup
        voice.cleanup()
        
        print("\n✅ IndianEnglishVoiceProcessor TTS test PASSED!")
        print("   If you heard all 3 messages, IndianEnglishVoiceProcessor works!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ IndianEnglishVoiceProcessor TTS test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all TTS tests."""
    print("="*70)
    print("TTS DIAGNOSTIC TEST SUITE".center(70))
    print("="*70)
    print("\nThis will test TTS at different levels to find the issue.")
    print("Listen carefully - you should hear 3 messages in each test.\n")
    
    results = []
    
    # Test 1: Direct pyttsx3
    results.append(("Direct pyttsx3", test_direct_pyttsx3()))
    
    # Test 2: Queue-based TTS
    results.append(("Queue-based TTS", test_queue_based_tts()))
    
    # Test 3: IndianEnglishVoiceProcessor
    results.append(("IndianEnglishVoiceProcessor", test_indian_english_voice_processor()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY".center(70))
    print("="*70)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<50} {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL TESTS PASSED!".center(70))
        print("\nTTS is working correctly!".center(70))
    else:
        print("❌ SOME TESTS FAILED!".center(70))
        print("\nCheck which test failed to diagnose the issue.".center(70))
    print("="*70)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

