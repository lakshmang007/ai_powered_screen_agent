#!/usr/bin/env python3
"""
Test AI-powered command conversion

This script demonstrates how AI improves command understanding.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

def test_ai_vs_regex():
    """Compare AI-powered vs regex-based command parsing."""
    print("=" * 70)
    print("🤖 AI-Powered Command Conversion Test")
    print("=" * 70)
    
    # Check if AI is available
    from src.core.ai_command_converter import AICommandConverter
    
    # Try Gemini first
    ai = AICommandConverter(provider="gemini")
    
    if not ai.is_available():
        print("\n❌ AI not available. Please set up an API key:")
        print("\n📝 Quick Setup:")
        print("1. Get free API key from: https://makersuite.google.com/app/apikey")
        print("2. Create .env file with: GEMINI_API_KEY=your_key_here")
        print("3. Or run: pip install google-generativeai")
        print("\nSee AI_SETUP_GUIDE.md for detailed instructions")
        return
    
    print(f"\n✅ AI Provider: {ai.provider}")
    print(f"✅ AI is ready!\n")
    
    # Test commands
    test_commands = [
        "click windows key and type ChatGPT and open it",
        "you typed hello erase and type hello world",
        "open chrome, search for AI tutorials, and click the first result",
        "press the windows button, find calculator, then launch it",
        "select all the text, copy it, open notepad, and paste",
    ]
    
    print("Testing complex commands:\n")
    
    for i, cmd in enumerate(test_commands, 1):
        print(f"{i}. Command: \"{cmd}\"")
        
        try:
            result = ai.convert_command(cmd)
            
            if result:
                print(f"   ✅ AI Understanding:")
                print(f"      Action: {result.action}")
                print(f"      Application: {result.application}")
                print(f"      Target: {result.target}")
                if result.parameters:
                    print(f"      Parameters: {result.parameters}")
                print(f"      Confidence: {result.confidence:.0%}")
            else:
                print(f"   ❌ AI couldn't parse this command")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    print("=" * 70)
    print("\n💡 Benefits of AI:")
    print("   ✅ Understands natural variations")
    print("   ✅ Handles complex multi-step commands")
    print("   ✅ Better context awareness")
    print("   ✅ More accurate parsing")
    print("\n" + "=" * 70)


def test_with_nlp_processor():
    """Test AI integration with NLP processor."""
    print("\n" + "=" * 70)
    print("🧠 Testing NLP Processor with AI")
    print("=" * 70)
    
    from src.core.nlp_processor import NLPProcessor
    
    # Initialize with AI enabled
    nlp = NLPProcessor(use_ai=True)
    
    if nlp.ai_converter and nlp.ai_converter.is_available():
        print("\n✅ NLP Processor initialized with AI support!")
    else:
        print("\n⚠️  NLP Processor running without AI (using regex only)")
        print("   Set up AI for better accuracy - see AI_SETUP_GUIDE.md")
        return
    
    test_commands = [
        "click windows key and type ChatGPT and open it",
        "erase that and type hello world",
    ]
    
    print("\nParsing commands with AI:\n")
    
    for cmd in test_commands:
        print(f"📝 Command: \"{cmd}\"")
        parsed = nlp.parse_command(cmd)
        
        print(f"   Action: {parsed.action.value}")
        print(f"   Application: {parsed.application.value}")
        print(f"   Target: {parsed.target}")
        print(f"   Confidence: {parsed.confidence:.0%}")
        print()
    
    print("=" * 70)


if __name__ == "__main__":
    print("\n🚀 Starting AI Command Conversion Tests\n")
    
    # Test 1: AI vs Regex
    test_ai_vs_regex()
    
    # Test 2: Integration with NLP
    test_with_nlp_processor()
    
    print("\n✨ Tests complete!")
    print("\n💡 To enable AI in Byte Smart:")
    print("   1. Set up API key (see AI_SETUP_GUIDE.md)")
    print("   2. Run: C:/Python313/python.exe byte_smart.py")
    print("   3. Byte will automatically use AI for better understanding!")
    print()

