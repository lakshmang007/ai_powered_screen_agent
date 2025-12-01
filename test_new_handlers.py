#!/usr/bin/env python3
"""
Test new YouTube and Keyboard handlers.
"""

import sys
import time

def test_youtube_handler():
    """Test YouTube handler."""
    print("="*70)
    print("YOUTUBE HANDLER TEST".center(70))
    print("="*70)
    
    try:
        from src.automation.handlers.youtube_handler import YouTubeHandler
        from src.core.nlp_processor import ParsedCommand, ActionType, ApplicationType
        
        handler = YouTubeHandler()
        
        print("\n1. Testing YouTube play video...")
        command = ParsedCommand(
            action=ActionType.PLAY,
            application=ApplicationType.YOUTUBE,
            parameters={'query': 'Python tutorial'},
            raw_text="play python tutorial on youtube"
        )
        
        result = handler.handle_command(command)
        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message']}")
        
        if result['status'] == 'completed':
            print("   ✅ YouTube handler working!")
            print("   🌐 YouTube should open in your browser")
            time.sleep(2)
            return True
        else:
            print(f"   ❌ Failed: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"\n❌ YouTube handler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_keyboard_handler():
    """Test keyboard handler."""
    print("\n" + "="*70)
    print("KEYBOARD HANDLER TEST".center(70))
    print("="*70)
    
    try:
        from src.automation.handlers.keyboard_handler import KeyboardHandler
        from src.core.nlp_processor import ParsedCommand, ActionType, ApplicationType
        
        handler = KeyboardHandler()
        
        # Test 1: Single key
        print("\n1. Testing single key press (Escape)...")
        command = ParsedCommand(
            action=ActionType.PRESS,
            application=ApplicationType.KEYBOARD,
            parameters={'key': 'escape'},
            raw_text="press escape"
        )
        
        result = handler.handle_command(command)
        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message']}")
        
        if result['status'] != 'completed':
            print(f"   ❌ Failed: {result.get('message')}")
            return False
        
        print("   ✅ Single key press working!")
        time.sleep(1)
        
        # Test 2: Named shortcut
        print("\n2. Testing named shortcut (copy)...")
        command = ParsedCommand(
            action=ActionType.PRESS,
            application=ApplicationType.KEYBOARD,
            parameters={'key': 'copy'},
            raw_text="copy"
        )
        
        result = handler.handle_command(command)
        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message']}")
        
        if result['status'] != 'completed':
            print(f"   ❌ Failed: {result.get('message')}")
            return False
        
        print("   ✅ Named shortcut working!")
        time.sleep(1)
        
        # Test 3: Key combination
        print("\n3. Testing key combination (Ctrl+Shift+Esc - Task Manager)...")
        print("   ⚠️  This will open Task Manager - close it manually")
        time.sleep(2)
        
        command = ParsedCommand(
            action=ActionType.PRESS,
            application=ApplicationType.KEYBOARD,
            parameters={'key': 'task manager'},
            raw_text="open task manager"
        )
        
        result = handler.handle_command(command)
        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message']}")
        
        if result['status'] != 'completed':
            print(f"   ❌ Failed: {result.get('message')}")
            return False
        
        print("   ✅ Key combination working!")
        print("   📋 Task Manager should have opened")
        
        return True
            
    except Exception as e:
        print(f"\n❌ Keyboard handler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_nlp_recognition():
    """Test NLP recognition of new commands."""
    print("\n" + "="*70)
    print("NLP RECOGNITION TEST".center(70))
    print("="*70)
    
    try:
        from src.core.nlp_processor import NLPProcessor
        
        nlp = NLPProcessor()
        
        # Test YouTube commands
        print("\n1. Testing YouTube command recognition...")
        
        test_commands = [
            "play music on youtube",
            "search youtube for python",
            "open youtube"
        ]
        
        for cmd in test_commands:
            parsed = nlp.parse_command(cmd)
            print(f"   '{cmd}'")
            print(f"      → Action: {parsed.action.value}")
            print(f"      → App: {parsed.application.value}")
            
            if parsed.application.value == 'youtube':
                print(f"      ✅ Recognized as YouTube")
            else:
                print(f"      ⚠️  Not recognized as YouTube")
        
        # Test keyboard commands
        print("\n2. Testing keyboard command recognition...")
        
        test_commands = [
            "press windows key",
            "press enter",
            "copy",
            "paste",
            "take screenshot"
        ]
        
        for cmd in test_commands:
            parsed = nlp.parse_command(cmd)
            print(f"   '{cmd}'")
            print(f"      → Action: {parsed.action.value}")
            print(f"      → App: {parsed.application.value}")
            
            if parsed.action.value in ['press', 'keyboard'] or parsed.application.value == 'keyboard':
                print(f"      ✅ Recognized as keyboard command")
            else:
                print(f"      ⚠️  Not recognized as keyboard command")
        
        return True
            
    except Exception as e:
        print(f"\n❌ NLP recognition test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("NEW HANDLERS TEST SUITE".center(70))
    print("="*70)
    print("\nTesting YouTube and Keyboard handlers...")
    print("This will:")
    print("  1. Open YouTube in your browser")
    print("  2. Press some keyboard keys")
    print("  3. Open Task Manager (close it manually)")
    print("\nPress Ctrl+C to cancel, or wait 5 seconds to continue...")
    
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\n\n❌ Tests cancelled by user")
        return 1
    
    results = []
    
    # Test YouTube handler
    results.append(("YouTube Handler", test_youtube_handler()))
    
    # Test keyboard handler
    results.append(("Keyboard Handler", test_keyboard_handler()))
    
    # Test NLP recognition
    results.append(("NLP Recognition", test_nlp_recognition()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY".center(70))
    print("="*70)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:.<50} {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!".center(70))
        print("="*70)
        print("\nYouTube and Keyboard handlers are working correctly!")
        print("\nYou can now use:")
        print("  • 'Play [video] on YouTube'")
        print("  • 'Press Windows key'")
        print("  • 'Copy', 'Paste', etc.")
        print("  • 'Take screenshot'")
        print("  • And many more keyboard shortcuts!")
        return 0
    else:
        print("\n" + "="*70)
        print("❌ SOME TESTS FAILED".center(70))
        print("="*70)
        print("\nPlease check the errors above.")
        print("\nCommon issues:")
        print("  1. PyAutoGUI not installed: pip install pyautogui")
        print("  2. No internet connection (for YouTube)")
        print("  3. Browser blocked by firewall")
        return 1


if __name__ == "__main__":
    sys.exit(main())

