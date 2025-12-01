"""
Test searching for Dolby and other apps with substring matching.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.automation.handlers.system_search_handler import SystemSearchHandler


def test_dolby_search():
    """Test searching for Dolby."""
    print("=" * 70)
    print("Test: Searching for 'dolby'")
    print("=" * 70)
    print()
    
    handler = SystemSearchHandler(voice_processor=None)
    result = handler.search_application("dolby")
    
    print(f"Status: {result['status']}")
    print()
    
    if result['status'] == 'found':
        print(f"✅ FOUND!")
        print(f"   Name: {result.get('name', 'N/A')}")
        print(f"   Path: {result.get('path', 'N/A')}")
        print(f"   Method: {result.get('method', 'N/A')}")
    elif result['status'] == 'multiple':
        print(f"✅ FOUND MULTIPLE!")
        print(f"   Matches: {len(result.get('matches', []))}")
        for i, match in enumerate(result.get('matches', []), 1):
            print(f"   {i}. {match['name']}")
            print(f"      Path: {match['path']}")
    else:
        print(f"❌ NOT FOUND")
        print(f"   Message: {result.get('message', 'N/A')}")
    
    print()
    print("=" * 70)
    return result


def test_chat_search():
    """Test searching for 'chat' (should find ChatGPT if installed)."""
    print()
    print("=" * 70)
    print("Test: Searching for 'chat'")
    print("=" * 70)
    print()
    
    handler = SystemSearchHandler(voice_processor=None)
    result = handler.search_application("chat")
    
    print(f"Status: {result['status']}")
    print()
    
    if result['status'] == 'found':
        print(f"✅ FOUND!")
        print(f"   Name: {result.get('name', 'N/A')}")
        print(f"   Path: {result.get('path', 'N/A')}")
        print(f"   Method: {result.get('method', 'N/A')}")
    elif result['status'] == 'multiple':
        print(f"✅ FOUND MULTIPLE!")
        print(f"   Matches: {len(result.get('matches', []))}")
        for i, match in enumerate(result.get('matches', []), 1):
            print(f"   {i}. {match['name']}")
            print(f"      Path: {match['path']}")
    else:
        print(f"❌ NOT FOUND")
        print(f"   Message: {result.get('message', 'N/A')}")
    
    print()
    print("=" * 70)
    return result


def test_substring_matching():
    """Test various substring searches."""
    print()
    print("=" * 70)
    print("Test: Substring Matching")
    print("=" * 70)
    print()
    
    test_cases = [
        ("dolby", "Should find Dolby Access, Dolby Atmos, etc."),
        ("chat", "Should find ChatGPT, Teams Chat, etc."),
        ("microsoft", "Should find Microsoft Edge, Word, etc."),
        ("chrome", "Should find Google Chrome"),
    ]
    
    handler = SystemSearchHandler(voice_processor=None)
    
    for app_name, description in test_cases:
        print(f"Searching for: '{app_name}'")
        print(f"Description: {description}")
        
        result = handler.search_application(app_name)
        
        if result['status'] == 'found':
            print(f"✅ Found: {result.get('name', 'N/A')}")
        elif result['status'] == 'multiple':
            matches = result.get('matches', [])
            print(f"✅ Found {len(matches)} matches:")
            for match in matches[:3]:  # Show first 3
                print(f"   - {match['name']}")
            if len(matches) > 3:
                print(f"   ... and {len(matches) - 3} more")
        else:
            print(f"❌ Not found")
        
        print()
    
    print("=" * 70)


def test_windows_apps():
    """Test Windows Apps search specifically."""
    print()
    print("=" * 70)
    print("Test: Windows Apps (UWP) Search")
    print("=" * 70)
    print()
    
    handler = SystemSearchHandler(voice_processor=None)
    
    # Search Windows Apps folder directly
    windows_apps_path = os.path.expanduser(r'~\AppData\Local\Microsoft\WindowsApps')
    
    if os.path.exists(windows_apps_path):
        print(f"Windows Apps folder: {windows_apps_path}")
        print()
        
        dolby_apps = []
        for file in os.listdir(windows_apps_path):
            if 'dolby' in file.lower() and file.lower().endswith('.exe'):
                dolby_apps.append(file)
        
        if dolby_apps:
            print(f"✅ Found {len(dolby_apps)} Dolby app(s) in WindowsApps:")
            for app in dolby_apps:
                print(f"   - {app}")
        else:
            print("❌ No Dolby apps found in WindowsApps")
    else:
        print("❌ Windows Apps folder not found")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    print()
    print("🔍 Enhanced Substring Search Test Suite")
    print()
    
    try:
        # Test Windows Apps folder first
        test_windows_apps()
        
        # Test Dolby search
        dolby_result = test_dolby_search()
        
        # Test Chat search
        chat_result = test_chat_search()
        
        # Test various substring searches
        test_substring_matching()
        
        print()
        print("✅ All tests completed!")
        print()
        
        # Summary
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print()
        
        if dolby_result['status'] in ['found', 'multiple']:
            print("✅ Dolby search: WORKING")
        else:
            print("❌ Dolby search: NOT FOUND (may not be installed)")
        
        if chat_result['status'] in ['found', 'multiple']:
            print("✅ Chat search: WORKING")
        else:
            print("⚠️  Chat search: NOT FOUND (ChatGPT may not be installed)")
        
        print()
        print("=" * 70)
        
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print()

