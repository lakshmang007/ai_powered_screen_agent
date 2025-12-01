"""
Test script to verify Byte Smart conversation in GUI.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

def test_byte_smart_integration():
    """Test that Byte Smart conversation is integrated."""
    print("🧪 Testing Byte Smart Conversation Integration...")
    
    try:
        from src.gui.main_window import MainWindow
        print("✅ MainWindow imported successfully")
    except Exception as e:
        print(f"❌ Failed to import MainWindow: {e}")
        return False
    
    try:
        # Create window (but don't run mainloop)
        app = MainWindow()
        
        # Check Byte Smart methods exist
        assert hasattr(app, '_start_byte_smart_mode'), "Missing _start_byte_smart_mode method"
        assert hasattr(app, '_stop_byte_smart_mode'), "Missing _stop_byte_smart_mode method"
        assert hasattr(app, '_byte_smart_loop'), "Missing _byte_smart_loop method"
        assert hasattr(app, '_listen_for_byte_input'), "Missing _listen_for_byte_input method"
        assert hasattr(app, '_execute_byte_command'), "Missing _execute_byte_command method"
        assert hasattr(app, '_is_wake_word'), "Missing _is_wake_word method"
        assert hasattr(app, '_is_sleep_command'), "Missing _is_sleep_command method"
        assert hasattr(app, '_is_exit_command'), "Missing _is_exit_command method"
        assert hasattr(app, '_is_negative_response'), "Missing _is_negative_response method"
        
        print("✅ All Byte Smart methods present")
        
        # Check wake word detection
        assert app._is_wake_word("byte"), "Wake word 'byte' not detected"
        assert app._is_wake_word("hey byte"), "Wake word in sentence not detected"
        assert not app._is_wake_word("hello"), "False positive for wake word"
        print("✅ Wake word detection working")
        
        # Check sleep command detection
        assert app._is_sleep_command("sleep"), "Sleep command not detected"
        assert app._is_sleep_command("no thanks"), "Negative response not detected"
        assert not app._is_sleep_command("open chrome"), "False positive for sleep"
        print("✅ Sleep command detection working")
        
        # Check exit command detection
        assert app._is_exit_command("exit"), "Exit command not detected"
        assert app._is_exit_command("quit"), "Quit command not detected"
        assert not app._is_exit_command("open chrome"), "False positive for exit"
        print("✅ Exit command detection working")
        
        # Check negative response detection
        assert app._is_negative_response("no"), "Negative response 'no' not detected"
        assert app._is_negative_response("nope"), "Negative response 'nope' not detected"
        assert not app._is_negative_response("yes"), "False positive for negative"
        print("✅ Negative response detection working")
        
        # Check features
        print(f"\n📊 Feature Status:")
        print(f"   - Byte Smart mode: {app.has_byte_smart}")
        print(f"   - Smart App Opener: {app.has_smart_opener}")
        print(f"   - Context Memory: {app.has_context_memory}")
        print(f"   - Macro Support: {app.has_macro_support}")
        
        # Destroy window
        app.root.destroy()
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 Byte Smart GUI Conversation Test")
    print("=" * 60)
    
    if not test_byte_smart_integration():
        print("\n❌ Tests failed")
        return
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print("\n💡 To run the GUI with Byte Smart conversation:")
    print("   python main.py")
    print("\n💡 How to use:")
    print("   1. Click '🎤 Byte Smart' button")
    print("   2. Say: 'byte'")
    print("   3. Byte: 'Hello! What can I do for you?'")
    print("   4. Say: 'open chatgpt'")
    print("   5. Byte: 'Got it!' (executes command)")
    print("   6. Byte: 'Anything else?'")
    print("   7. Say: 'no thanks' or 'sleep'")
    print("   8. Byte: 'Going to sleep. Say byte to wake me!'")
    print("\n🎊 Byte Smart now talks to you just like in byte_smart.py!")

if __name__ == "__main__":
    main()

