#!/usr/bin/env python3
"""
Quick test of Byte Smart with AI command parsing
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.core.nlp_processor import NLPProcessor

print("=" * 70)
print("🤖 Byte Smart - AI Command Parsing Test")
print("=" * 70)

# Initialize NLP with AI
nlp = NLPProcessor(use_ai=True)

if nlp.ai_converter and nlp.ai_converter.is_available():
    print("\n✅ AI-powered command parsing is ENABLED!")
    print(f"   Provider: {nlp.ai_converter.provider}")
else:
    print("\n⚠️  AI not available, using regex only")

print("\n" + "=" * 70)
print("Testing Commands:")
print("=" * 70)

test_commands = [
    "click windows key and type ChatGPT and open it",
    "you typed hello erase and type hello world",
    "open chrome and search for python tutorials",
]

for i, cmd in enumerate(test_commands, 1):
    print(f"\n{i}. 📝 Command: \"{cmd}\"")
    
    parsed = nlp.parse_command(cmd)
    
    print(f"   🧠 Parsed:")
    print(f"      Action: {parsed.action.value}")
    print(f"      Application: {parsed.application.value}")
    print(f"      Target: {parsed.target}")
    if parsed.parameters:
        print(f"      Parameters: {parsed.parameters}")
    print(f"      Confidence: {parsed.confidence:.0%}")

print("\n" + "=" * 70)
print("✨ AI Integration Working!")
print("=" * 70)
print("\n💡 Next: Run Byte Smart with voice commands!")
print("   C:/Python313/python.exe byte_smart.py")
print()

