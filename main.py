#!/usr/bin/env python3
"""
AI-Powered Screen Agent - Main Application Entry Point

This application provides an intelligent automation tool that takes text or voice commands
and performs automated tasks by interacting with your screen and applications.

Features:
- 🎤 Voice commands with wake word "byte"
- 🧠 AI-powered command understanding (Google Gemini)
- 🪟 Smart app opening with taskbar checking
- 💬 Intelligent follow-up questions
- 🎨 Enhanced UI/UX with colors and emojis
- 🌐 Web app support (25+ apps)
- 📝 Context memory for smart commands

Usage:
    python main.py [options]

Examples:
    python main.py                    # Start with GUI
    python main.py --cli              # Start in CLI mode
    python main.py --voice            # Start in voice mode (Byte Smart)
    python main.py --config config.ini  # Use custom config file
"""

import sys
import os
import argparse
import logging
import time
import random
from pathlib import Path

# Add src directory to Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

# Load API keys (GEMINI_API_KEY / GROQ_API_KEY / ...) from .env before anything reads them.
# Without this, CLI and GUI modes silently ran without AI.
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJECT_ROOT, '.env'))
except ImportError:
    pass

# Windows consoles default to cp1252, which can't print the emoji in our output
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass

from src.utils.helpers import setup_logging, load_config
from src.gui.main_window import MainWindow
from src.core.screen_agent import ScreenAgent
from src.core.nlp_processor import NLPProcessor
from src.automation.task_engine import TaskEngine

# Try to import optional voice components
try:
    from src.core.indian_english_voice_processor import IndianEnglishVoiceProcessor
    HAS_VOICE = True
except ImportError:
    HAS_VOICE = False

# Try to import smart app opener
try:
    from src.automation.handlers.smart_app_opener import SmartAppOpener
    from src.automation.handlers.system_search_handler import SystemSearchHandler
    HAS_SMART_OPENER = True
except ImportError:
    HAS_SMART_OPENER = False

# Try to import intelligent assistant
try:
    from src.core.intelligent_assistant import IntelligentAssistant
    HAS_INTELLIGENT = True
except ImportError:
    HAS_INTELLIGENT = False


# ============================================================================
# UI/UX Helper Functions
# ============================================================================

def print_banner():
    """Print enhanced banner with colors and emojis."""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║        🤖 AI-POWERED SCREEN AGENT - BYTE SMART 🤖                   ║
║                                                                      ║
║        Intelligent Voice & Screen Automation Assistant              ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_box(text, border_char="="):
    """Print text in a box."""
    width = 70
    print(border_char * width)
    print(text.center(width))
    print(border_char * width)


def print_feature_list():
    """Print feature list."""
    features = """
✨ Features:
  🎤 Voice commands with wake word "byte"
  🧠 AI-powered command understanding (Google Gemini)
  🪟 Smart app opening with taskbar checking
  💬 Intelligent follow-up questions
  🌐 Web app support (25+ apps)
  📝 Context memory for smart commands
  🎨 Enhanced UI/UX with colors and emojis
    """
    print(features)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AI-Powered Screen Agent - Intelligent Voice & Screen Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           Start with GUI interface
  %(prog)s --cli                     Start in command-line mode
  %(prog)s --voice                   Start in voice mode (Byte Smart)
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
        '--voice',
        action='store_true',
        help='Run in voice mode (Byte Smart) with wake word activation'
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

def register_default_handlers(task_engine, screen_agent, whatsapp_confirm=None):
    """Register the application-specific handlers on a task engine.

    whatsapp_confirm: optional fn(contact, message) -> bool asked before sending.
    """
    from src.automation.handlers import VSCodeHandler, GmailHandler, LinkedInHandler, BrowserHandler
    from src.automation.handlers.whatsapp_handler import WhatsAppHandler
    from src.core.nlp_processor import ApplicationType

    task_engine.register_app_handler(ApplicationType.VSCODE, VSCodeHandler(screen_agent).handle_command)
    task_engine.register_app_handler(ApplicationType.GMAIL, GmailHandler(screen_agent).handle_command)
    task_engine.register_app_handler(ApplicationType.LINKEDIN, LinkedInHandler(screen_agent).handle_command)
    task_engine.register_app_handler(ApplicationType.CHROME, BrowserHandler(screen_agent).handle_command)
    task_engine.register_app_handler(
        ApplicationType.WHATSAPP, WhatsAppHandler(screen_agent, confirm_callback=whatsapp_confirm).handle_command)


def run_gui_mode(config):
    """Run the application in GUI mode."""
    try:
        app = MainWindow()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        logging.exception(f"Error running GUI application: {e}")
        sys.exit(1)

def run_cli_mode(config):
    """Run the application in CLI mode with enhanced UI."""
    print_banner()
    print("\n🎯 CLI Mode - Type commands or 'help' for assistance")
    print("=" * 70)

    # Initialize components
    try:
        screen_agent = ScreenAgent()
        nlp_processor = NLPProcessor(use_ai=True)  # Use AI if available
        task_engine = TaskEngine(screen_agent)

        # Initialize smart opener if available
        smart_opener = None
        if HAS_SMART_OPENER:
            system_search = SystemSearchHandler(voice_processor=None)
            smart_opener = SmartAppOpener(voice_processor=None, system_search_handler=system_search)
            print("✅ Smart App Opener enabled")

        print("✅ All components initialized")

    except Exception as e:
        print(f"⚠️  Warning: Some components failed to initialize: {e}")
        print("Continuing with limited functionality...")
        screen_agent = ScreenAgent()
        nlp_processor = NLPProcessor(use_ai=False)
        task_engine = TaskEngine(screen_agent)
        smart_opener = None
    
    # Setup handlers
    register_default_handlers(task_engine, screen_agent)
    
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
                elif user_input.lower() == 'features':
                    print_feature_list()
                    continue

                # Parse and execute command with smart opener
                print(f"\n📝 Processing: {user_input}")
                parsed_command = nlp_processor.parse_command(user_input)

                print(f"🧠 Understood: {parsed_command.action.value} on {parsed_command.application.value}")
                if parsed_command.action.value == 'multi_step':
                    for i, step in enumerate(parsed_command.parameters.get('steps', []), 1):
                        print(f"   {i}. {step}")
                if parsed_command.confidence < 0.3:
                    print("⚠️  Warning: Low confidence in command understanding")
                elif parsed_command.confidence > 0.8:
                    print(f"✨ High confidence: {parsed_command.confidence:.0%}")

                # Handle OPEN commands with smart opener
                if parsed_command.action.value.lower() == "open" and smart_opener and parsed_command.application.value != "whatsapp":
                    app_name = parsed_command.target or parsed_command.application.value
                    if app_name and app_name.lower() != "unknown":
                        print(f"🔍 Smart opening: {app_name}")
                        result_dict = smart_opener.open_app_smart(app_name)

                        if result_dict['status'] in ('completed', 'already_open'):
                            print(f"✅ Success: {result_dict['message']}")
                            continue
                        elif result_dict['status'] == 'cancelled':
                            print("❌ Cancelled by user")
                            continue

                # Execute command normally
                result = task_engine.execute_command(parsed_command)

                # Display result with enhanced formatting
                if result.status.value == 'completed':
                    print(f"✅ Success: {result.message}")
                elif result.status.value == 'ambiguous':
                    print(f"❓ Ambiguous: {result.message}")
                    clarification = input("Clarification > ").strip()
                    if clarification:
                        new_input = f"{user_input} {clarification}"
                        print(f"🔄 Retrying: {new_input}")
                        # Recursively handle (or just continue loop logic by reprocessing)
                        # For simplicity in this loop structure, we'll just process it immediately
                        parsed_command = nlp_processor.parse_command(new_input)
                        result = task_engine.execute_command(parsed_command)
                        if result.status.value == 'completed':
                            print(f"✅ Success: {result.message}")
                        else:
                            print(f"❌ Failed: {result.message}")
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
        print("\n\n👋 Goodbye! Thanks for using Byte Smart!")
    finally:
        # Cleanup
        print("🧹 Cleaning up...")
        pass

def print_help():
    """Print enhanced help information."""
    help_text = """
╔══════════════════════════════════════════════════════════════════════╗
║                        📚 AVAILABLE COMMANDS                         ║
╚══════════════════════════════════════════════════════════════════════╝

🔧 System Commands:
  help                    Show this help message
  quit, exit, q          Exit the application
  history                Show command execution history
  features               Show feature list

📝 Example Commands:
  open chatgpt           Smart open (checks taskbar → installed → browser)
  open chrome            Brings to front if already running
  open gmail             Opens in browser if not installed
  create a new folder named "test" in vscode
  search for "python tutorial" in google
  type hello world
  press enter

🎤 Voice Mode:
  Run with --voice flag to use Byte Smart voice assistant
  Wake word: "byte"
  Natural language understanding with AI

💡 Tips:
  ✨ Use natural language - AI will understand
  🪟 "open" commands are smart - checks taskbar first
  🌐 Web apps open in browser automatically
  🧠 AI provides 95% accuracy (vs 70% regex)
  📝 Context-aware commands supported

🌐 Supported Web Apps (25+):
  chatgpt, claude, gemini, gmail, youtube, twitter, facebook,
  instagram, linkedin, github, stackoverflow, reddit, netflix,
  spotify, discord, slack, notion, figma, canva, and more!
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
        timestamp = time.strftime('%H:%M:%S', time.localtime(entry['timestamp']))
        
        status_icon = "✅" if result.status.value == 'completed' else "❌"
        print(f"{i}. [{timestamp}] {status_icon} {command.raw_text}")
        print(f"   → {result.message}")

def run_voice_mode(config):
    """Run the application in voice mode (JARVIS)."""
    if not HAS_VOICE:
        print("❌ Voice mode not available - PyAudio not installed")
        print("Install with: pip install pyaudio")
        return

    print_banner()
    print("\n🎤 Voice Mode - Say 'JARVIS' to activate")
    print("=" * 70)

    try:
        # Initialize voice processor
        from src.core.indian_english_voice_processor import IndianEnglishVoiceProcessor
        voice = IndianEnglishVoiceProcessor(
            wake_word="jarvis",
            language="en-IN",
            use_whisper=False,
            use_gpt_enhancement=False
        )
        print("✅ Voice processor initialized")

        # Initialize NLP with AI
        nlp = NLPProcessor(use_ai=True)
        print("✅ NLP processor initialized (AI-powered)")

        # Initialize screen agent and task engine
        screen_agent = ScreenAgent()
        engine = TaskEngine(screen_agent)
        from jarvis import make_voice_confirm
        register_default_handlers(engine, screen_agent, whatsapp_confirm=make_voice_confirm(voice))
        print("✅ Task engine initialized")

        # Shared interrupt signal (overlay STOP button -> long-running handlers)
        import threading
        interrupt_event = threading.Event()

        # Initialize smart opener
        smart_opener = None
        if HAS_SMART_OPENER:
            system_search = SystemSearchHandler(voice, interrupt_event=interrupt_event)
            smart_opener = SmartAppOpener(voice_processor=voice, system_search_handler=system_search)
            print("✅ Smart App Opener initialized")

        # Initialize intelligent assistant (takes the NLP processor, not the screen agent)
        intelligent = None
        if HAS_INTELLIGENT:
            intelligent = IntelligentAssistant(voice, nlp)
            print("✅ Intelligent Assistant initialized")

        print("\n" + "=" * 70)
        print("🤖 JARVIS is ready!")
        print("=" * 70)
        print("\n💡 Say 'JARVIS' to start, then give your command")
        print("💡 Examples:")
        print("   - 'JARVIS' → 'install spotify'")
        print("   - 'JARVIS' → 'go to youtube.com'")
        print("   - 'JARVIS' → 'open vscode'")
        print("\n🛑 Press Ctrl+C to exit\n")

        # Import JARVIS main loop
        from jarvis import run_jarvis, ContextMemory

        # Create context memory
        context = ContextMemory()

        # Run the main loop
        run_jarvis(voice, nlp, engine, intelligent, context, smart_opener, interrupt_event)

    except KeyboardInterrupt:
        print("\n\n👋 Goodbye! Thanks for using JARVIS!")
    except Exception as e:
        print(f"❌ Error in voice mode: {e}")
        logging.exception(f"Voice mode error: {e}")
    finally:
        print("🧹 Cleaning up...")
        try:
            if 'voice' in locals():
                voice.cleanup()
        except Exception:
            pass

def main():
    """Main application entry point."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Load configuration
    try:
        config_path = args.config if os.path.isabs(args.config) else os.path.join(PROJECT_ROOT, args.config)
        config = load_config(config_path)
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
        if args.voice:
            run_voice_mode(config)
        elif args.cli:
            run_cli_mode(config)
        else:
            run_gui_mode(config)
    except Exception as e:
        logging.error(f"Application error: {e}")
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()