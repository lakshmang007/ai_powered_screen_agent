"""
Test browser detection and selection.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.automation.handlers.browser_detector import BrowserDetector


def test_browser_detection():
    """Test browser detection."""
    print("=" * 70)
    print("Browser Detection Test")
    print("=" * 70)
    print()
    
    # Create detector
    detector = BrowserDetector()
    
    # Detect installed browsers
    print("Detecting installed browsers...")
    print()
    
    installed_browsers = detector.detect_installed_browsers()
    
    if not installed_browsers:
        print("❌ No browsers detected!")
        return
    
    print(f"✅ Found {len(installed_browsers)} browser(s):")
    print()
    
    for i, browser in enumerate(installed_browsers, 1):
        print(f"  {i}. {browser['name']}")
        print(f"     ID: {browser['id']}")
        print(f"     Command: {browser['command']}")
        print(f"     Path: {browser['path']}")
        print()
    
    print("=" * 70)
    print()
    
    # Test browser info
    print("Browser Information:")
    print()
    
    for browser_id in ['chrome', 'firefox', 'edge', 'opera', 'brave']:
        is_installed = detector._is_browser_installed(browser_id)
        status = "✅ Installed" if is_installed else "❌ Not installed"
        print(f"  {browser_id.capitalize()}: {status}")
        
        if is_installed:
            path = detector._get_browser_path(browser_id)
            if path:
                print(f"    Path: {path}")
    
    print()
    print("=" * 70)


def test_browser_selection_without_voice():
    """Test browser selection without voice processor."""
    print()
    print("=" * 70)
    print("Browser Selection Test (Without Voice)")
    print("=" * 70)
    print()
    
    # Create detector without voice processor
    detector = BrowserDetector()
    
    # Detect browsers
    installed_browsers = detector.detect_installed_browsers()
    
    if not installed_browsers:
        print("❌ No browsers detected!")
        return
    
    # Ask for browser choice (will use default since no voice processor)
    print("Selecting browser (will use default)...")
    browser_id = detector.ask_browser_choice(installed_browsers)
    
    if browser_id:
        browser = next((b for b in installed_browsers if b['id'] == browser_id), None)
        if browser:
            print(f"✅ Selected: {browser['name']}")
            print(f"   Command: {detector.get_browser_command(browser_id)}")
    else:
        print("❌ No browser selected")
    
    print()
    print("=" * 70)


def test_browser_commands():
    """Test browser command generation."""
    print()
    print("=" * 70)
    print("Browser Commands Test")
    print("=" * 70)
    print()
    
    detector = BrowserDetector()
    
    browsers = ['chrome', 'firefox', 'edge', 'opera', 'brave']
    
    for browser_id in browsers:
        command = detector.get_browser_command(browser_id)
        print(f"  {browser_id.capitalize()}: {command}")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    print()
    print("🔍 Browser Detection and Selection Test Suite")
    print()
    
    # Run tests
    test_browser_detection()
    test_browser_selection_without_voice()
    test_browser_commands()
    
    print()
    print("✅ All tests completed!")
    print()
    print("=" * 70)
    print()
    print("📝 Note:")
    print("   When you say 'open YouTube', Byte will:")
    print("   1. Detect all installed browsers")
    print("   2. Ask you which browser to use via voice")
    print("   3. Open YouTube in your selected browser")
    print()
    print("   Example:")
    print("   You: 'Byte, open YouTube'")
    print("   Byte: 'I can see Google Chrome, Microsoft Edge, and Opera.")
    print("         Which one would you like me to use?'")
    print("   You: 'Chrome'")
    print("   Byte: *Opens YouTube in Chrome*")
    print()
    print("=" * 70)

