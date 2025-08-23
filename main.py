#!/usr/bin/env python3
"""
AI-Powered Screen Agent - Main Application Entry Point

This application provides an intelligent automation tool that takes text or voice commands
and performs automated tasks by interacting with your screen and applications.

Usage:
    python main.py [options]

Examples:
    python main.py                    # Start with GUI
    python main.py --cli              # Start in CLI mode
    python main.py --config config.ini  # Use custom config file
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.helpers import setup_logging, load_config
from src.gui.main_window import MainWindow
from src.core.screen_agent import ScreenAgent
from src.core.voice_processor import VoiceProcessor
from src.core.nlp_processor import NLPProcessor
from src.automation.task_engine import TaskEngine

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AI-Powered Screen Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           Start with GUI interface
  %(prog)s --cli                     Start in command-line mode
  %(prog)s --config custom.ini       Use custom configuration file
  %(prog)s --log-level DEBUG         Set logging level to DEBUG
        """
    )
    
    parser.add_argument(
        '--cli',
        action='store_true',
        help='Run in command-line interface mode instead of GUI'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.ini',
        help='Path to configuration file (default: config/config.ini)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        help='Path to log file (default: from config or logs/screen_agent.log)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='AI-Powered Screen Agent v1.0.0'
    )
    
    return parser.parse_args()

def run_gui_mode(config):
    """Run the application in GUI mode."""
    try:
        app = MainWindow()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        logging.error(f"Error running GUI application: {e}")
        sys.exit(1)

def run_cli_mode(config):
    """Run the application in CLI mode."""
    print("AI-Powered Screen Agent - CLI Mode")
    print("Type 'help' for available commands, 'quit' to exit")
    print("-" * 50)

    # Initialize components
    try:
        screen_agent = ScreenAgent()
        voice_processor = VoiceProcessor()
        nlp_processor = NLPProcessor()
        task_engine = TaskEngine(screen_agent)
    except Exception as e:
        print(f"Warning: Some components failed to initialize: {e}")
        print("Continuing with limited functionality...")
        screen_agent = ScreenAgent()
        voice_processor = None
        nlp_processor = NLPProcessor()
        task_engine = TaskEngine(screen_agent)
    
    # Setup handlers
    from src.automation.handlers import VSCodeHandler, GmailHandler, LinkedInHandler, BrowserHandler
    from src.core.nlp_processor import ApplicationType
    
    vscode_handler = VSCodeHandler(screen_agent)
    gmail_handler = GmailHandler(screen_agent)
    linkedin_handler = LinkedInHandler(screen_agent)
    browser_handler = BrowserHandler(screen_agent)
    
    task_engine.register_app_handler(ApplicationType.VSCODE, vscode_handler.handle_command)
    task_engine.register_app_handler(ApplicationType.GMAIL, gmail_handler.handle_command)
    task_engine.register_app_handler(ApplicationType.LINKEDIN, linkedin_handler.handle_command)
    task_engine.register_app_handler(ApplicationType.CHROME, browser_handler.handle_command)
    
    try:
        while True:
            try:
                # Get user input
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == 'help':
                    print_help()
                    continue
                elif user_input.lower() == 'history':
                    show_history(task_engine)
                    continue
                elif user_input.lower().startswith('voice'):
                    if voice_processor:
                        handle_voice_command(voice_processor, nlp_processor, task_engine)
                    else:
                        print("❌ Voice processing not available (PyAudio not installed)")
                    continue
                
                # Parse and execute command
                print(f"Processing: {user_input}")
                parsed_command = nlp_processor.parse_command(user_input)
                
                print(f"Understood: {parsed_command.action.value} on {parsed_command.application.value}")
                if parsed_command.confidence < 0.3:
                    print("⚠️  Warning: Low confidence in command understanding")
                
                # Execute command
                result = task_engine.execute_command(parsed_command)
                
                # Display result
                if result.status.value == 'completed':
                    print(f"✅ Success: {result.message}")
                else:
                    print(f"❌ Failed: {result.message}")
                
                if result.execution_time > 0:
                    print(f"⏱️  Execution time: {result.execution_time:.2f}s")
                
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit")
            except Exception as e:
                print(f"❌ Error: {e}")
                logging.error(f"CLI error: {e}")
    
    except KeyboardInterrupt:
        print("\nGoodbye!")
    finally:
        # Cleanup
        try:
            voice_processor.stop_continuous_listening()
        except:
            pass

def print_help():
    """Print help information."""
    help_text = """
Available Commands:
  help                    Show this help message
  quit, exit, q          Exit the application
  history                Show command execution history
  voice                  Start voice input mode
  
Example Commands:
  create a new folder named "test" in vscode
  open gmail and send email to john@example.com
  post this image to my linkedin account
  search for "python tutorial" in google
  open notepad
  
Voice Commands:
  Say "voice" to start voice input mode
  Speak your command naturally
  
Tips:
  - Be specific about what you want to do
  - Mention the application you want to use
  - Use natural language - the AI will understand
    """
    print(help_text)

def show_history(task_engine):
    """Show command execution history."""
    history = task_engine.get_task_history()
    if not history:
        print("No command history available")
        return
    
    print("\nCommand History (last 10):")
    print("-" * 50)
    
    for i, entry in enumerate(history[-10:], 1):
        command = entry['command']
        result = entry['result']
        import time
        timestamp = time.strftime('%H:%M:%S', time.localtime(entry['timestamp']))
        
        status_icon = "✅" if result.status.value == 'completed' else "❌"
        print(f"{i}. [{timestamp}] {status_icon} {command.raw_text}")
        print(f"   → {result.message}")

def handle_voice_command(voice_processor, nlp_processor, task_engine):
    """Handle voice command input."""
    try:
        command_text = voice_processor.listen_once()
        if command_text:
            print(f"\n📝 Processing command: {command_text}")

            # Parse and execute
            parsed_command = nlp_processor.parse_command(command_text)
            print(f"🧠 Understood: {parsed_command.action.value} on {parsed_command.application.value}")

            if parsed_command.confidence < 0.3:
                print("⚠️  Warning: Low confidence in command understanding")

            result = task_engine.execute_command(parsed_command)

            # Display result
            if result.status.value == 'completed':
                print(f"✅ Success: {result.message}")
                if result.execution_time > 0:
                    print(f"⏱️  Execution time: {result.execution_time:.2f}s")
                # Optionally speak the result
                if voice_processor.tts_engine:
                    voice_processor.speak("Command completed successfully", async_speech=True)
            else:
                print(f"❌ Failed: {result.message}")
                if voice_processor.tts_engine:
                    voice_processor.speak("Command failed", async_speech=True)
        else:
            print("❌ No voice input detected")

    except Exception as e:
        print(f"❌ Voice command error: {e}")

def main():
    """Main application entry point."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        config = {}
    
    # Setup logging
    log_level = args.log_level
    log_file = args.log_file or config.get('logging', {}).get('file', 'logs/screen_agent.log')
    
    try:
        setup_logging(log_level, log_file)
        logging.info("AI-Powered Screen Agent starting...")
        logging.info(f"Configuration loaded from: {args.config}")
        logging.info(f"Log level: {log_level}")
    except Exception as e:
        print(f"Error setting up logging: {e}")
        # Continue without file logging
        setup_logging(log_level)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required")
        sys.exit(1)
    
    # Run application
    try:
        if args.cli:
            run_cli_mode(config)
        else:
            run_gui_mode(config)
    except Exception as e:
        logging.error(f"Application error: {e}")
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
