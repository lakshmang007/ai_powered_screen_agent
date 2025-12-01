#!/usr/bin/env python3
"""
Setup script for enhanced voice processing with OpenAI integration.

This script helps you:
1. Install required dependencies
2. Set up API keys
3. Test the voice processing system
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60 + "\n")


def check_python_version():
    """Check if Python version is compatible."""
    print_header("Checking Python Version")
    
    if sys.version_info < (3, 7):
        print("❌ Error: Python 3.7 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True


def install_dependencies():
    """Install required dependencies."""
    print_header("Installing Dependencies")
    
    print("Installing base dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Base dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing base dependencies: {e}")
        return False
    
    print("\nInstalling OpenAI for enhanced voice processing...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openai"])
        print("✅ OpenAI installed")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Could not install OpenAI: {e}")
        print("   You can install it manually: pip install openai")
    
    print("\nOptional: Install ElevenLabs for better text-to-speech?")
    choice = input("Install ElevenLabs? (y/n): ").strip().lower()
    if choice == 'y':
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "elevenlabs"])
            print("✅ ElevenLabs installed")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Could not install ElevenLabs: {e}")
    
    return True


def setup_api_keys():
    """Help user set up API keys."""
    print_header("Setting Up API Keys")
    
    env_file = Path(".env")
    env_content = []
    
    if env_file.exists():
        print("Found existing .env file")
        with open(env_file, 'r') as f:
            env_content = f.readlines()
    else:
        print("Creating new .env file")
    
    # Check for OpenAI key
    has_openai_key = any("OPENAI_API_KEY" in line for line in env_content)
    
    if not has_openai_key:
        print("\n🔑 OpenAI API Key Setup")
        print("   Get your API key from: https://platform.openai.com/api-keys")
        print()
        
        api_key = input("Enter your OpenAI API key (or press Enter to skip): ").strip()
        
        if api_key:
            env_content.append(f"\n# OpenAI API Key\nOPENAI_API_KEY={api_key}\n")
            print("✅ OpenAI API key will be saved")
        else:
            print("⚠️  Skipping OpenAI API key setup")
            print("   You can add it later to the .env file")
    else:
        print("✅ OpenAI API key already configured")
    
    # Save .env file
    if env_content:
        with open(env_file, 'w') as f:
            f.writelines(env_content)
        print(f"\n✅ Configuration saved to {env_file}")
    
    return True


def test_voice_system():
    """Test the voice processing system."""
    print_header("Testing Voice System")
    
    print("Testing imports...")
    
    try:
        import speech_recognition as sr
        print("✅ speech_recognition imported")
    except ImportError:
        print("❌ speech_recognition not found")
        print("   Install with: pip install SpeechRecognition pyaudio")
        return False
    
    try:
        import pyttsx3
        print("✅ pyttsx3 imported")
    except ImportError:
        print("⚠️  pyttsx3 not found (text-to-speech will not work)")
    
    try:
        import openai
        print("✅ openai imported")
        
        # Check if API key is set
        if os.getenv("OPENAI_API_KEY"):
            print("✅ OpenAI API key found in environment")
        else:
            print("⚠️  OpenAI API key not found in environment")
            print("   Set OPENAI_API_KEY in .env file or environment variables")
    except ImportError:
        print("⚠️  openai not found (enhanced features will not work)")
        print("   Install with: pip install openai")
    
    print("\nTesting microphone access...")
    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("✅ Microphone access successful")
    except Exception as e:
        print(f"❌ Microphone access failed: {e}")
        print("   Make sure you have a microphone connected")
        print("   On Linux, you may need to install: sudo apt-get install portaudio19-dev python3-pyaudio")
        return False
    
    print("\n✅ All tests passed!")
    return True


def run_demo():
    """Run the voice automation demo."""
    print_header("Running Demo")
    
    print("Starting voice automation demo...")
    print("Press Ctrl+C to exit\n")
    
    try:
        subprocess.check_call([sys.executable, "examples/voice_automation_example.py"])
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running demo: {e}")
    except KeyboardInterrupt:
        print("\n\n✅ Demo stopped")


def main():
    """Main setup function."""
    print()
    print("🎙️  Enhanced Voice Processing Setup")
    print("=" * 60)
    print()
    print("This script will help you set up voice-powered automation with:")
    print("  • OpenAI Whisper for accurate voice recognition")
    print("  • GPT-4 for automatic prompt enhancement")
    print("  • Selenium integration for web automation")
    print()
    
    # Check Python version
    if not check_python_version():
        return
    
    # Install dependencies
    print("\n1. Install Dependencies")
    choice = input("   Install required packages? (y/n): ").strip().lower()
    if choice == 'y':
        if not install_dependencies():
            print("\n❌ Setup failed during dependency installation")
            return
    
    # Setup API keys
    print("\n2. Configure API Keys")
    choice = input("   Set up API keys? (y/n): ").strip().lower()
    if choice == 'y':
        if not setup_api_keys():
            print("\n❌ Setup failed during API key configuration")
            return
    
    # Test system
    print("\n3. Test Voice System")
    choice = input("   Run system tests? (y/n): ").strip().lower()
    if choice == 'y':
        if not test_voice_system():
            print("\n⚠️  Some tests failed, but you can continue")
    
    # Run demo
    print("\n4. Run Demo")
    choice = input("   Run voice automation demo? (y/n): ").strip().lower()
    if choice == 'y':
        run_demo()
    
    # Final instructions
    print_header("Setup Complete!")
    
    print("Next steps:")
    print()
    print("1. Make sure your .env file has your OpenAI API key:")
    print("   OPENAI_API_KEY=sk-your-key-here")
    print()
    print("2. Run the demo:")
    print("   python examples/voice_automation_example.py")
    print()
    print("3. Or use in your own code:")
    print("   from src.core.enhanced_voice_processor import EnhancedVoiceProcessor")
    print()
    print("4. Read the full guide:")
    print("   API_INTEGRATION_GUIDE.md")
    print()
    print("📚 Documentation:")
    print("   - API_INTEGRATION_GUIDE.md - Complete API integration guide")
    print("   - examples/voice_automation_example.py - Usage examples")
    print("   - src/core/enhanced_voice_processor.py - Enhanced voice processor")
    print()
    print("✅ You're all set! Happy automating! 🚀")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

