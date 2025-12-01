"""
Test Windows Search with Vision
Tests the new Windows Search feature that uses OCR to detect apps
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.automation.handlers.system_search_handler import SystemSearchHandler

def test_windows_search_vision():
    """Test Windows Search with vision for Dolby."""
    print("=" * 60)
    print("Testing Windows Search with Vision")
    print("=" * 60)
    
    handler = SystemSearchHandler(voice_processor=None)
    
    # Test 1: Search for Dolby
    print("\n🔍 Test 1: Searching for 'dolby'...")
    result = handler._windows_search_with_vision('dolby')
    
    print(f"\nResult: {result}")
    
    if result.get('status') == 'found':
        print(f"✅ SUCCESS: Found {result.get('name')}")
    else:
        print(f"❌ FAILED: Status = {result.get('status')}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    print("\n⚠️  WARNING: This test will:")
    print("   1. Open Windows Search (Win+S)")
    print("   2. Type 'dolby'")
    print("   3. Take a screenshot")
    print("   4. Use OCR to detect apps")
    print("   5. Press Enter to open the first result")
    print("\n⚠️  Make sure you're ready before running this test!")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    input()
    
    test_windows_search_vision()

