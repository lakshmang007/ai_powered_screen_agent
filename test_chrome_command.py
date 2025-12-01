#!/usr/bin/env python3
"""
Test the Chrome multi-step command without voice
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.nlp_processor import NLPProcessor
from src.automation.task_engine import TaskEngine
from src.core.screen_agent import ScreenAgent

def test_chrome_command():
    """Test the Chrome multi-step command."""
    print("=" * 70)
    print("Testing: Open Chrome and type Dolby and press enter")
    print("=" * 70)

    # Initialize components
    nlp = NLPProcessor()
    screen_agent = ScreenAgent()
    engine = TaskEngine(screen_agent)
    
    # The command
    command_text = "Open Chrome and type Dolby and press enter"
    print(f"\n📝 Command: {command_text}")
    
    # Split into steps
    steps = nlp.split_multi_step_command(command_text)
    print(f"\n🔄 Multi-step command detected: {len(steps)} steps\n")
    
    all_success = True
    
    for i, step in enumerate(steps, 1):
        print(f"📍 Step {i}/{len(steps)}: {step}")
        
        # Parse the step
        parsed = nlp.parse_command(step)
        print(f"   🧠 Understanding: {parsed.action.value} on {parsed.application.value}")
        if parsed.target:
            print(f"   🎯 Target: {parsed.target}")
        
        # Execute the step
        try:
            result = engine.execute_command(parsed)
            
            if result.status.value == 'completed':
                print(f"   ✅ Step {i} completed: {result.message}")
                time.sleep(2)  # Wait between steps
            else:
                print(f"   ❌ Step {i} failed: {result.message}")
                all_success = False
                break
        except Exception as e:
            print(f"   ❌ Step {i} error: {e}")
            all_success = False
            break
        
        print()
    
    print("=" * 70)
    if all_success:
        print("✅ All steps completed successfully!")
    else:
        print("❌ Command failed at one of the steps")
    print("=" * 70)

if __name__ == "__main__":
    test_chrome_command()

