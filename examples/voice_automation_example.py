#!/usr/bin/env python3
"""
Example: Voice-Powered Automation with Automatic Prompt Enhancement

This example demonstrates how to use the enhanced voice processor with:
1. OpenAI Whisper for accurate voice recognition
2. GPT-4 for automatic prompt enhancement
3. Selenium for web automation
4. Wake word activation

Usage:
    python examples/voice_automation_example.py
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.core.enhanced_voice_processor import EnhancedVoiceProcessor
from src.core.nlp_processor import NLPProcessor
from src.automation.task_engine import TaskEngine
from src.core.screen_agent import ScreenAgent
from src.automation.handlers import VSCodeHandler, GmailHandler, LinkedInHandler, BrowserHandler
from src.core.nlp_processor import ApplicationType


class VoiceAutomationDemo:
    """
    Demonstration of voice-powered automation with automatic enhancement.
    """
    
    def __init__(self, use_openai: bool = True):
        """
        Initialize the voice automation demo.
        
        Args:
            use_openai: Whether to use OpenAI for Whisper and GPT-4
        """
        print("🚀 Initializing Voice Automation Demo...")
        
        # Initialize components
        self.screen_agent = ScreenAgent()
        self.nlp_processor = NLPProcessor()
        self.task_engine = TaskEngine(self.screen_agent)
        
        # Initialize enhanced voice processor
        if use_openai:
            print("🔧 Using OpenAI Whisper + GPT-4 for enhanced voice processing")
            self.voice_processor = EnhancedVoiceProcessor(
                use_whisper=True,
                use_gpt_enhancement=True,
                wake_word="computer"  # Say "computer" to activate
            )
        else:
            print("🔧 Using standard voice processing (Google Speech Recognition)")
            from src.core.voice_processor import VoiceProcessor
            self.voice_processor = VoiceProcessor()
        
        # Register application handlers
        self._register_handlers()
        
        print("✅ Initialization complete!")
        print()
    
    def _register_handlers(self):
        """Register application-specific handlers."""
        vscode_handler = VSCodeHandler(self.screen_agent)
        gmail_handler = GmailHandler(self.screen_agent)
        linkedin_handler = LinkedInHandler(self.screen_agent)
        browser_handler = BrowserHandler(self.screen_agent)
        
        self.task_engine.register_app_handler(ApplicationType.VSCODE, vscode_handler.handle_command)
        self.task_engine.register_app_handler(ApplicationType.GMAIL, gmail_handler.handle_command)
        self.task_engine.register_app_handler(ApplicationType.LINKEDIN, linkedin_handler.handle_command)
        self.task_engine.register_app_handler(ApplicationType.CHROME, browser_handler.handle_command)
    
    def run_single_command_demo(self):
        """
        Demo: Single voice command with automatic enhancement.
        """
        print("=" * 60)
        print("DEMO 1: Single Voice Command with Auto-Enhancement")
        print("=" * 60)
        print()
        print("Try saying something vague like:")
        print("  - 'open that email thing'")
        print("  - 'search for python tutorials'")
        print("  - 'post something on social media'")
        print()
        
        # Listen for command
        command_text = self.voice_processor.listen_once(enhance_prompt=True)
        
        if command_text:
            self._execute_command(command_text)
        else:
            print("❌ No command detected")
    
    def run_continuous_listening_demo(self):
        """
        Demo: Continuous listening with wake word activation.
        """
        print("=" * 60)
        print("DEMO 2: Continuous Listening with Wake Word")
        print("=" * 60)
        print()
        print("Say 'computer' followed by your command")
        print("Examples:")
        print("  - 'Computer, open Gmail'")
        print("  - 'Computer, search for AI tutorials'")
        print("  - 'Computer, create a new file in VSCode'")
        print()
        print("Press Ctrl+C to stop")
        print()
        
        try:
            # Start continuous listening
            self.voice_processor.start_continuous_listening(
                callback=self._handle_continuous_command,
                use_wake_word=True,
                enhance_prompts=True
            )
            
            # Keep running
            import time
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping continuous listening...")
            self.voice_processor.stop_continuous_listening()
            print("✅ Stopped")
    
    def run_selenium_integration_demo(self):
        """
        Demo: Voice commands with Selenium automation.
        """
        print("=" * 60)
        print("DEMO 3: Voice + Selenium Web Automation")
        print("=" * 60)
        print()
        print("Try commands like:")
        print("  - 'open Gmail and compose email'")
        print("  - 'search Google for Python tutorials'")
        print("  - 'open LinkedIn and create post'")
        print()
        
        command_text = self.voice_processor.listen_once(enhance_prompt=True)
        
        if command_text:
            self._execute_command(command_text)
    
    def _execute_command(self, command_text: str):
        """
        Execute a voice command.
        
        Args:
            command_text: The command text (already enhanced)
        """
        print(f"\n📝 Executing: {command_text}")
        
        try:
            # Parse command
            parsed_command = self.nlp_processor.parse_command(command_text)
            
            print(f"🧠 Understood: {parsed_command.action.value} on {parsed_command.application.value}")
            
            if parsed_command.confidence < 0.3:
                print("⚠️  Warning: Low confidence in command understanding")
                self.voice_processor.speak("I'm not sure I understood that correctly", async_speech=True)
            
            # Execute command
            result = self.task_engine.execute_command(parsed_command)
            
            # Display result
            if result.status.value == 'completed':
                print(f"✅ Success: {result.message}")
                if result.execution_time > 0:
                    print(f"⏱️  Execution time: {result.execution_time:.2f}s")
                
                # Speak result
                self.voice_processor.speak("Command completed successfully", async_speech=True)
            else:
                print(f"❌ Failed: {result.message}")
                self.voice_processor.speak("Command failed", async_speech=True)
                
        except Exception as e:
            print(f"❌ Error: {e}")
            self.voice_processor.speak("An error occurred", async_speech=True)
    
    def _handle_continuous_command(self, command_text: str):
        """
        Handle command from continuous listening.
        
        Args:
            command_text: The command text (already enhanced)
        """
        print(f"\n{'='*60}")
        self._execute_command(command_text)
        print(f"{'='*60}\n")
        print("🎤 Listening for next command... (say 'computer' first)")


def print_menu():
    """Print the demo menu."""
    print()
    print("=" * 60)
    print("Voice Automation Demo - Choose a mode:")
    print("=" * 60)
    print()
    print("1. Single Command Mode")
    print("   - Speak one command at a time")
    print("   - Automatic prompt enhancement")
    print()
    print("2. Continuous Listening Mode")
    print("   - Always listening with wake word ('computer')")
    print("   - Hands-free operation")
    print()
    print("3. Selenium Integration Demo")
    print("   - Voice commands for web automation")
    print("   - Works with Gmail, LinkedIn, Google, etc.")
    print()
    print("4. Exit")
    print()


def main():
    """Main entry point."""
    print()
    print("🎙️  Voice-Powered Automation Demo")
    print("=" * 60)
    print()
    
    # Check for OpenAI API key
    use_openai = False
    if os.getenv("OPENAI_API_KEY"):
        print("✅ OpenAI API key found - using Whisper + GPT-4")
        use_openai = True
    else:
        print("⚠️  OpenAI API key not found")
        print("   Set OPENAI_API_KEY environment variable to use enhanced features")
        print("   Falling back to Google Speech Recognition")
    
    print()
    
    # Initialize demo
    try:
        demo = VoiceAutomationDemo(use_openai=use_openai)
    except Exception as e:
        print(f"❌ Error initializing demo: {e}")
        print("\nMake sure you have installed all dependencies:")
        print("  pip install -r requirements.txt")
        print("  pip install openai  # For enhanced features")
        return
    
    # Main loop
    while True:
        print_menu()
        
        try:
            choice = input("Enter your choice (1-4): ").strip()
            
            if choice == '1':
                demo.run_single_command_demo()
            elif choice == '2':
                demo.run_continuous_listening_demo()
            elif choice == '3':
                demo.run_selenium_integration_demo()
            elif choice == '4':
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-4.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()

