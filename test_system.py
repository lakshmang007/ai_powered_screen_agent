#!/usr/bin/env python3
"""
System Test Script for Byte Smart
Tests all components and reports what's working
"""

import sys

def print_header(text):
    print("\n" + "=" * 70)
    print(text.center(70))
    print("=" * 70)

def test_import(module_name, description=""):
    """Test if a module can be imported."""
    try:
        __import__(module_name)
        print(f"✅ {module_name:30} - {description}")
        return True
    except ImportError as e:
        print(f"❌ {module_name:30} - {description}")
        print(f"   Error: {e}")
        return False

def test_microphone():
    """Test if microphone is accessible."""
    try:
        import speech_recognition as sr
        mic = sr.Microphone()
        print(f"✅ Microphone Access           - Can access microphone")
        return True
    except Exception as e:
        print(f"❌ Microphone Access           - Cannot access microphone")
        print(f"   Error: {e}")
        return False

def test_tts():
    """Test if text-to-speech works."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        print(f"✅ Text-to-Speech              - TTS engine initialized")
        return True
    except Exception as e:
        print(f"❌ Text-to-Speech              - TTS initialization failed")
        print(f"   Error: {e}")
        return False

def main():
    print_header("🤖 Byte Smart System Test")
    
    print("\n📦 Testing Core Dependencies:")
    core_results = []
    core_results.append(test_import("speech_recognition", "Voice recognition"))
    core_results.append(test_import("pyttsx3", "Text-to-speech"))
    core_results.append(test_import("dotenv", "Environment variables"))
    
    print("\n🎤 Testing Voice Components:")
    voice_results = []
    voice_results.append(test_microphone())
    voice_results.append(test_tts())
    
    print("\n🔧 Testing Optional Dependencies:")
    optional_results = []
    optional_results.append(test_import("cv2", "OpenCV (screen analysis)"))
    optional_results.append(test_import("numpy", "NumPy (numerical operations)"))
    optional_results.append(test_import("selenium", "Selenium (web automation)"))
    optional_results.append(test_import("pyautogui", "PyAutoGUI (mouse/keyboard)"))
    optional_results.append(test_import("PIL", "Pillow (image processing)"))
    optional_results.append(test_import("mss", "MSS (screen capture)"))
    optional_results.append(test_import("pytesseract", "Tesseract (OCR)"))
    optional_results.append(test_import("psutil", "PSUtil (process management)"))
    optional_results.append(test_import("pygetwindow", "PyGetWindow (window management)"))
    optional_results.append(test_import("spacy", "spaCy (NLP)"))
    
    print("\n📊 Testing Byte Smart Components:")
    component_results = []
    component_results.append(test_import("src.core.screen_agent", "Screen Agent"))
    component_results.append(test_import("src.core.nlp_processor", "NLP Processor"))
    component_results.append(test_import("src.core.intelligent_assistant", "Intelligent Assistant"))
    component_results.append(test_import("src.core.indian_english_voice_processor", "Voice Processor"))
    component_results.append(test_import("src.automation.task_engine", "Task Engine"))
    
    # Summary
    print_header("📋 Test Summary")
    
    core_pass = sum(core_results)
    voice_pass = sum(voice_results)
    optional_pass = sum(optional_results)
    component_pass = sum(component_results)
    
    print(f"\nCore Dependencies:      {core_pass}/{len(core_results)} passed")
    print(f"Voice Components:       {voice_pass}/{len(voice_results)} passed")
    print(f"Optional Dependencies:  {optional_pass}/{len(optional_results)} passed")
    print(f"Byte Smart Components:  {component_pass}/{len(component_results)} passed")
    
    print("\n" + "=" * 70)
    
    if core_pass == len(core_results) and voice_pass == len(voice_results):
        print("✅ SYSTEM READY! All core components are working!")
        print("\nYou can run: python byte_smart.py")
    elif core_pass == len(core_results):
        print("⚠️  PARTIAL: Core dependencies OK, but voice components need fixing")
        print("\n🔧 To fix microphone access:")
        print("   The issue is PyAudio is not installed.")
        print("   ")
        print("   Solution 1: Install standard Windows Python (not MSYS2)")
        print("   Then: pip install pyaudio")
        print("   ")
        print("   Solution 2: Use MSYS2 package manager")
        print("   Run: pacman -S mingw-w64-ucrt-x86_64-portaudio")
        print("   Then: pip install pyaudio")
    else:
        print("❌ CRITICAL: Core dependencies missing!")
        print("\n🔧 Install missing core dependencies:")
        print("   pip install SpeechRecognition pyttsx3 python-dotenv")
    
    print("\n" + "=" * 70)
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
    except Exception as e:
        print(f"\n\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()

