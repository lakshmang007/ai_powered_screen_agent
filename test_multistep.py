#!/usr/bin/env python3
"""
Test multi-step command parsing
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from core.nlp_processor import NLPProcessor

def test_multistep_parsing():
    """Test multi-step command parsing."""
    nlp = NLPProcessor()
    
    print("=" * 70)
    print("Testing Multi-Step Command Parsing")
    print("=" * 70)
    
    # Test command
    command = "Open Chrome and type Dolby and click enter"
    print(f"\n📝 Command: {command}")
    
    # Split into steps
    steps = nlp.split_multi_step_command(command)
    print(f"\n🔄 Detected {len(steps)} steps:")
    
    for i, step in enumerate(steps, 1):
        print(f"\n  Step {i}: {step}")
        parsed = nlp.parse_command(step)
        print(f"    → Action: {parsed.action.value}")
        print(f"    → App: {parsed.application.value}")
        print(f"    → Target: {parsed.target}")
        print(f"    → Parameters: {parsed.parameters}")
    
    print("\n" + "=" * 70)
    
    # Test more commands
    test_commands = [
        "open notepad and type hello world",
        "search for python then click first result",
        "open gmail and send email",
        "type my name and press enter",
        "click submit and then wait"
    ]
    
    print("\nTesting more multi-step commands:")
    print("=" * 70)
    
    for cmd in test_commands:
        print(f"\n📝 Command: {cmd}")
        steps = nlp.split_multi_step_command(cmd)
        print(f"   Steps: {len(steps)}")
        for i, step in enumerate(steps, 1):
            parsed = nlp.parse_command(step)
            print(f"   {i}. {step} → {parsed.action.value}")

if __name__ == "__main__":
    test_multistep_parsing()

