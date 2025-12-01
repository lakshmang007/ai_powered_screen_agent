"""
Complete Test for Enhanced Search
Tests all search methods including Windows Search with vision
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.automation.handlers.system_search_handler import SystemSearchHandler

def test_complete_search():
    """Test complete search flow."""
    print("=" * 60)
    print("Testing Complete Search Flow")
    print("=" * 60)
    
    handler = SystemSearchHandler(voice_processor=None)
    
    # Test 1: Search for Chrome (should find in file system)
    print("\n🔍 Test 1: Searching for 'chrome'...")
    result = handler.search_application('chrome')
    print(f"Status: {result.get('status')}")
    print(f"Method: {result.get('method')}")
    print(f"Name: {result.get('name')}")
    if result.get('status') == 'found':
        print("✅ Chrome found in file system")
    else:
        print("❌ Chrome not found")
    
    # Test 2: Search for Microsoft (should find multiple)
    print("\n🔍 Test 2: Searching for 'microsoft'...")
    result = handler.search_application('microsoft')
    print(f"Status: {result.get('status')}")
    if result.get('status') == 'found':
        print(f"✅ Found: {result.get('name')}")
    elif result.get('status') == 'multiple':
        print(f"✅ Found multiple matches")
    else:
        print("❌ Microsoft not found")
    
    # Test 3: Search for Dolby (will try Windows Search)
    print("\n🔍 Test 3: Searching for 'dolby'...")
    print("   This will use Windows Search with vision...")
    print("   ⚠️  Windows Search will open automatically!")
    result = handler.search_application('dolby')
    print(f"Status: {result.get('status')}")
    print(f"Method: {result.get('method')}")
    print(f"Name: {result.get('name')}")
    if result.get('status') == 'found':
        print("✅ Dolby found!")
    else:
        print(f"❌ Dolby not found - Status: {result.get('status')}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_complete_search()

