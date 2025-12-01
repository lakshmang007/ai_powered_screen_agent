#!/usr/bin/env python3
"""
Test context-aware commands like "erase and type"
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.nlp_processor import NLPProcessor

def test_context_commands():
    """Test context-aware command parsing."""
    print("=" * 70)
    print("Testing Context-Aware Commands")
    print("=" * 70)
    
    nlp = NLPProcessor()
    
    test_commands = [
        "erase that and type hello world",
        "clear and type new text",
        "delete that and write something else",
        "erase and type dolby",
        "you typed hello erase and type hello world"
    ]
    
    for cmd in test_commands:
        print(f"\n📝 Command: {cmd}")
        
        # Check if it's an erase command
        cmd_lower = cmd.lower()
        if 'erase' in cmd_lower or 'clear' in cmd_lower or 'delete' in cmd_lower:
            if 'and type' in cmd_lower or 'and write' in cmd_lower:
                print("   ✅ Detected: Erase and replace pattern")
                
                # Extract what to type
                import re
                type_match = re.search(r'(?:and\s+)?(?:type|write)\s+(.+)', cmd_lower)
                if type_match:
                    new_text = type_match.group(1).strip()
                    print(f"   📝 New text to type: '{new_text}'")
                    print(f"   🔄 Actions:")
                    print(f"      1. Select all (Ctrl+A)")
                    print(f"      2. Delete")
                    print(f"      3. Type: '{new_text}'")
            else:
                print("   ⚠️  Erase command without replacement")
        else:
            # Parse normally
            parsed = nlp.parse_command(cmd)
            print(f"   Action: {parsed.action.value}")
            print(f"   Target: {parsed.target}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    test_context_commands()

