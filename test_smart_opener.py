#!/usr/bin/env python3
"""
Test Smart App Opener
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.automation.handlers.smart_app_opener import SmartAppOpener
from src.automation.handlers.system_search_handler import SystemSearchHandler

print("=" * 60)
print("🧪 Testing Smart App Opener")
print("=" * 60)

# Initialize (without voice for testing)
system_search = SystemSearchHandler(voice_processor=None)
smart_opener = SmartAppOpener(voice_processor=None, system_search_handler=system_search)

print("\n✅ Smart App Opener initialized")

# Test 1: Check if an app is running
print("\n" + "=" * 60)
print("Test 1: Check if Chrome is running")
print("=" * 60)

result = smart_opener.check_if_running("chrome")
print(f"Is running: {result['is_running']}")
if result['is_running']:
    print(f"Window title: {result['title']}")

# Test 2: Check if an app is running
print("\n" + "=" * 60)
print("Test 2: Check if ChatGPT is running")
print("=" * 60)

result = smart_opener.check_if_running("chatgpt")
print(f"Is running: {result['is_running']}")
if result['is_running']:
    print(f"Window title: {result['title']}")

# Test 3: Check web URLs
print("\n" + "=" * 60)
print("Test 3: Check web URLs")
print("=" * 60)

test_apps = ['chatgpt', 'claude', 'gemini', 'gmail', 'youtube']
for app in test_apps:
    app_lower = app.lower()
    url = None
    for key, u in smart_opener.web_urls.items():
        if key in app_lower or app_lower in key:
            url = u
            break
    print(f"{app}: {url if url else 'No URL'}")

# Test 4: Smart open (without voice)
print("\n" + "=" * 60)
print("Test 4: Smart open ChatGPT (dry run)")
print("=" * 60)

print("This would:")
print("1. Check if ChatGPT is running in taskbar")
print("2. If running, bring to front")
print("3. If not running, check if installed")
print("4. If not installed, ask to open in browser")
print("5. If yes, ask which browser")
print("6. Open in browser")

print("\n✅ All tests completed!")
print("\nTo test with voice, run:")
print("  C:/Python313/python.exe byte_smart.py")
print("  Then say: 'byte'")
print("  Then say: 'open chatgpt'")

