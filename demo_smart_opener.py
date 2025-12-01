#!/usr/bin/env python3
"""
Demo: Smart App Opener in Action
Shows how the smart opener works with different scenarios
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.automation.handlers.smart_app_opener import SmartAppOpener
from src.automation.handlers.system_search_handler import SystemSearchHandler

def print_scenario(title):
    """Print scenario header."""
    print("\n" + "=" * 70)
    print(f"📋 SCENARIO: {title}")
    print("=" * 70)

def print_step(step_num, description):
    """Print step."""
    print(f"\n  {step_num}. {description}")

# Initialize
system_search = SystemSearchHandler(voice_processor=None)
smart_opener = SmartAppOpener(voice_processor=None, system_search_handler=system_search)

print("=" * 70)
print("🎬 SMART APP OPENER - DEMO")
print("=" * 70)
print("\nThis demo shows how Byte Smart intelligently handles 'open' commands")

# Scenario 1: App already running
print_scenario("App Already Running (e.g., Chrome)")
print_step("🎤", "You say: 'byte, open chrome'")
print_step("🔍", "Byte checks taskbar...")

result = smart_opener.check_if_running("chrome")
if result['is_running']:
    print_step("✅", f"Found running: {result['title']}")
    print_step("🪟", "Byte brings window to front (restores if minimized)")
    print_step("🤖", "Byte says: 'Chrome is already open, bringing it to front'")
else:
    print_step("❌", "Chrome not running")
    print_step("💾", "Byte would check installed apps next...")

# Scenario 2: App not running but installed
print_scenario("App Installed But Not Running (e.g., Notepad)")
print_step("🎤", "You say: 'byte, open notepad'")
print_step("🔍", "Byte checks taskbar...")
print_step("❌", "Not running")
print_step("💾", "Byte searches installed apps...")
print_step("✅", "Found: C:\\Windows\\System32\\notepad.exe")
print_step("🚀", "Byte launches notepad")
print_step("🤖", "Byte says: 'Opening Notepad'")

# Scenario 3: App not installed (web version)
print_scenario("App Not Installed - Web Version (e.g., ChatGPT)")
print_step("🎤", "You say: 'byte, open chatgpt'")
print_step("🔍", "Byte checks taskbar...")

result = smart_opener.check_if_running("chatgpt")
if result['is_running']:
    print_step("✅", f"Found running: {result['title']}")
else:
    print_step("❌", "Not running")
    print_step("💾", "Byte searches installed apps...")
    print_step("❌", "Not installed")
    print_step("🌐", "Byte checks web URLs...")
    
    # Check if we have a web URL
    app_lower = "chatgpt"
    url = None
    for key, u in smart_opener.web_urls.items():
        if key in app_lower:
            url = u
            break
    
    if url:
        print_step("✅", f"Found web URL: {url}")
        print_step("🤖", "Byte asks: 'I couldn't find ChatGPT installed. Should I open it in your browser?'")
        print_step("🎤", "You say: 'yes'")
        print_step("🤖", "Byte asks: 'Which browser? Chrome, Firefox, or Edge?'")
        print_step("🎤", "You say: 'chrome'")
        print_step("🌐", f"Byte opens {url} in Chrome")
        print_step("🤖", "Byte says: 'Opening ChatGPT in Chrome'")

# Show all supported web apps
print_scenario("Supported Web Apps (25+)")
print("\n  Byte knows web URLs for these apps:")
print()

web_apps = list(smart_opener.web_urls.keys())
for i in range(0, len(web_apps), 4):
    row = web_apps[i:i+4]
    print("  " + " | ".join(f"{app:15}" for app in row))

# Summary
print("\n" + "=" * 70)
print("🎊 SUMMARY")
print("=" * 70)
print("""
When you say "open [app]", Byte Smart:

1. 🔍 Checks if app is running in taskbar
   → If yes: Brings window to front (even if minimized)
   
2. 💾 Checks if app is installed on your system
   → If yes: Launches the application
   
3. 🌐 Checks if app has a web version
   → If yes: Asks if you want to open in browser
   → Asks which browser to use
   → Opens in chosen browser

This makes Byte much smarter and more user-friendly!
""")

print("=" * 70)
print("🚀 TRY IT NOW!")
print("=" * 70)
print("""
Run Byte Smart:
  C:/Python313/python.exe byte_smart.py

Then try:
  "byte"
  "open chatgpt"
  "open chrome"
  "open notepad"
  "open gmail"
""")

