#!/usr/bin/env python3
"""
Test Windows search commands like "click windows key and type X and open it"
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.nlp_processor import NLPProcessor

def test_windows_search_commands():
    """Test Windows search command parsing."""
    print("=" * 70)
    print("Testing Windows Search Commands")
    print("=" * 70)
    
    nlp = NLPProcessor()
    
    test_commands = [
        "click windows key and type chat GPT and open it",
        "press win key and type notepad and launch it",
        "windows key and type chrome and open it",
        "click windows key and type chart gpt and open it"
    ]
    
    for cmd in test_commands:
        print(f"\n📝 Command: {cmd}")
        
        # Split into steps
        steps = nlp.split_multi_step_command(cmd)
        
        print(f"   🔄 Detected {len(steps)} steps:")
        for i, step in enumerate(steps, 1):
            parsed = nlp.parse_command(step)
            print(f"      {i}. {step}")
            print(f"         Action: {parsed.action.value}")
            print(f"         Target: {parsed.target}")
    
    print("\n" + "=" * 70)
    print("\n✅ Expected behavior:")
    print("   Step 1: Click/Press Windows key")
    print("   Step 2: Type the search term")
    print("   Step 3: Press Enter (converted from 'open it')")
    print("=" * 70)

if __name__ == "__main__":
    test_windows_search_commands()

