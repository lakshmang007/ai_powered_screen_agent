#!/usr/bin/env python3
"""
Byte Smart - Intelligent Voice Assistant with Follow-up Questions

Features:
- Wake word: "byte"
- Asks intelligent follow-up questions
- Checks if apps are installed
- Asks which browser to use
- Confirms ambiguous actions
- Sleep mode
- Optimized for Indian English
"""

import sys
import os
import random
import time
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))


class ContextMemory:
    """Remembers what Byte has done recently."""

    def __init__(self):
        self.history = []
        self.last_typed_text = None
        self.last_opened_app = None
        self.last_action = None
        self.max_history = 10

    def add_action(self, action_type, details):
        """Add an action to memory."""
        entry = {
            'action': action_type,
            'details': details,
            'timestamp': time.time()
        }
        self.history.append(entry)

        # Keep only recent history
        if len(self.history) > self.max_history:
            self.history.pop(0)

        # Update specific trackers
        if action_type == 'type':
            self.last_typed_text = details.get('text')
        elif action_type == 'open':
            self.last_opened_app = details.get('app')

        self.last_action = action_type

    def get_last_typed_text(self):
        """Get the last text that was typed."""
        return self.last_typed_text

    def get_last_action(self):
        """Get the last action performed."""
        return self.last_action

    def clear(self):
        """Clear all memory."""
        self.history = []
        self.last_typed_text = None
        self.last_opened_app = None
        self.last_action = None


class BytePersonality:
    """Byte's personality and responses."""

    GREETINGS = [
        "Hello! What can I do for you?",
        "Hi! Byte here, ready to help!",
        "Hey! What do you need?",
        "Namaste! How can I assist?",
        "Yes! What's the task?"
    ]

    ACKNOWLEDGMENTS = [
        "Got it!",
        "Sure thing!",
        "On it!",
        "Okay!",
        "Working on it!"
    ]

    SUCCESS = [
        "Done!",
        "Complete!",
        "Finished!",
        "All done!",
        "Success!"
    ]
    
    FEEDBACK_QUESTIONS = [
        "Anything else?",
        "What's next?",
        "Need anything else, or should I sleep?",
        "Can I help with something else?",
        "More work, or should I rest?"
    ]
    
    SLEEP_MESSAGES = [
        "Going to sleep. Say 'byte' to wake me!",
        "Sleeping now. Wake me when you need me!",
        "Taking a nap. Call me anytime!",
        "Sleep mode. I'll be here!",
        "Resting. Say 'byte' when ready!"
    ]
    
    @staticmethod
    def random_choice(messages):
        return random.choice(messages)


def print_box(text, char="="):
    """Print text in a box."""
    print("\n" + char * 70)
    print(text.center(70))
    print(char * 70 + "\n")


def main():
    print_box("🤖 BYTE SMART - Intelligent Voice Assistant", "=")
    
    print("Features:")
    print("  ✅ Wake word: 'byte'")
    print("  ✅ Intelligent follow-up questions")
    print("  ✅ Checks if apps are installed")
    print("  ✅ Asks which browser to use")
    print("  ✅ Sleep mode")
    print("  ✅ Optimized for Indian English")
    print()
    
    # Initialize
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from src.core.indian_english_voice_processor import IndianEnglishVoiceProcessor
        from src.core.nlp_processor import NLPProcessor
        from src.automation.task_engine import TaskEngine
        from src.core.screen_agent import ScreenAgent
        from src.automation.handlers import VSCodeHandler, GmailHandler, LinkedInHandler, BrowserHandler
        from src.core.nlp_processor import ApplicationType
        from src.core.intelligent_assistant import IntelligentAssistant
        from src.automation.handlers.smart_app_opener import SmartAppOpener
        from src.automation.handlers.system_search_handler import SystemSearchHandler
        
        print("🔧 Initializing Byte Smart...")
        
        voice = IndianEnglishVoiceProcessor(
            wake_word="byte",
            language="en-IN",
            use_whisper=False,
            use_gpt_enhancement=False
        )
        
        nlp = NLPProcessor()
        screen_agent = ScreenAgent()
        engine = TaskEngine(screen_agent)

        # Initialize context memory
        context = ContextMemory()

        # Initialize intelligent assistant
        intelligent = IntelligentAssistant(voice, nlp)

        # Initialize system search handler
        system_search = SystemSearchHandler(voice)

        # Initialize smart app opener
        smart_opener = SmartAppOpener(voice, system_search)

        # Register handlers
        vscode_handler = VSCodeHandler(screen_agent)
        gmail_handler = GmailHandler(screen_agent)
        linkedin_handler = LinkedInHandler(screen_agent)
        browser_handler = BrowserHandler(screen_agent)
        
        engine.register_app_handler(ApplicationType.VSCODE, vscode_handler.handle_command)
        engine.register_app_handler(ApplicationType.GMAIL, gmail_handler.handle_command)
        engine.register_app_handler(ApplicationType.LINKEDIN, linkedin_handler.handle_command)
        engine.register_app_handler(ApplicationType.CHROME, browser_handler.handle_command)
        
        print("✅ Byte Smart is ready!\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Start
    run_byte_smart(voice, nlp, engine, intelligent, context, smart_opener)


def run_byte_smart(voice, nlp, engine, intelligent, context, smart_opener):
    """Main Byte Smart interaction loop."""
    
    print_box("🤖 Byte Smart is Active!", "-")
    
    # Initial greeting
    greeting = BytePersonality.random_choice(BytePersonality.GREETINGS)
    print(f"🤖 Byte: {greeting}\n")
    voice.speak(greeting)
    
    is_awake = True
    task_count = 0
    
    try:
        while True:
            print("-" * 70)
            
            if is_awake:
                # Awake mode
                print("🎤 Listening... (say 'byte' for new task, or give command)")
                command = listen_for_input(voice)
                
                if not command:
                    continue
                
                cmd_lower = command.lower().strip()
                
                # Check for sleep
                if is_sleep_command(cmd_lower):
                    is_awake = False
                    sleep_msg = BytePersonality.random_choice(BytePersonality.SLEEP_MESSAGES)
                    print(f"\n😴 Byte: {sleep_msg}\n")
                    voice.speak(sleep_msg)
                    continue
                
                # Check for exit
                if is_exit_command(cmd_lower):
                    print("\n🤖 Byte: Goodbye!\n")
                    voice.speak("Goodbye!")
                    break
                
                # Check for wake word
                if is_wake_word(cmd_lower):
                    greeting = BytePersonality.random_choice(BytePersonality.GREETINGS)
                    print(f"\n🤖 Byte: {greeting}\n")
                    voice.speak(greeting)
                    
                    # Listen for command
                    print("🎤 Listening for your command...")
                    command = listen_for_input(voice)
                    if not command:
                        continue
                    cmd_lower = command.lower().strip()
                
                # Execute with intelligence
                if not is_sleep_command(cmd_lower) and not is_exit_command(cmd_lower):
                    success = execute_intelligent_command(command, nlp, engine, voice, intelligent, context, smart_opener)
                    if success:
                        task_count += 1
                    
                    # Ask for feedback
                    time.sleep(0.5)
                    feedback_q = BytePersonality.random_choice(BytePersonality.FEEDBACK_QUESTIONS)
                    print(f"\n🤖 Byte: {feedback_q}\n")
                    voice.speak(feedback_q)
                    
                    # Listen for response
                    print("🎤 Listening for response...")
                    response = listen_for_input(voice, timeout=15)
                    
                    if response:
                        resp_lower = response.lower().strip()
                        
                        if is_sleep_command(resp_lower) or is_negative_response(resp_lower):
                            is_awake = False
                            sleep_msg = BytePersonality.random_choice(BytePersonality.SLEEP_MESSAGES)
                            print(f"\n😴 Byte: {sleep_msg}\n")
                            voice.speak(sleep_msg)
                        elif is_positive_response(resp_lower):
                            print("\n🤖 Byte: Sure! What do you need?\n")
                            voice.speak("Sure! What do you need?")
                        else:
                            # Treat as new command
                            execute_intelligent_command(response, nlp, engine, voice, intelligent, context, smart_opener)
                            task_count += 1
                    else:
                        # No response - go to sleep
                        is_awake = False
                        sleep_msg = BytePersonality.random_choice(BytePersonality.SLEEP_MESSAGES)
                        print(f"\n😴 Byte: {sleep_msg}\n")
                        voice.speak(sleep_msg)
            
            else:
                # Sleep mode
                print("😴 Sleeping... Say 'byte' to wake me up")
                command = listen_for_input(voice, timeout=60)
                
                if command and is_wake_word(command.lower()):
                    is_awake = True
                    greeting = BytePersonality.random_choice(BytePersonality.GREETINGS)
                    print(f"\n🤖 Byte: {greeting}\n")
                    voice.speak(greeting)
    
    except KeyboardInterrupt:
        print(f"\n\n🤖 Byte: Completed {task_count} tasks. Goodbye!\n")
        voice.speak("Goodbye!")
        voice.cleanup()


def listen_for_input(voice, timeout=20):
    """Listen for voice input."""
    try:
        command = voice.listen_once(timeout=timeout, phrase_time_limit=30)
        return command
    except Exception as e:
        print(f"⚠️  Listening error: {e}")
        return None


def execute_intelligent_command(command_text, nlp, engine, voice, intelligent, context, smart_opener=None):
    """Execute command with intelligent follow-up questions and context awareness."""
    print(f"\n📝 Command: {command_text}")

    # Acknowledge
    ack = BytePersonality.random_choice(BytePersonality.ACKNOWLEDGMENTS)
    print(f"🤖 Byte: {ack}")
    voice.speak(ack)

    try:
        # Check for context-aware commands (erase, clear, etc.)
        cmd_lower = command_text.lower()

        # Handle "erase that and type X" pattern
        if 'erase' in cmd_lower or 'clear' in cmd_lower or 'delete' in cmd_lower:
            if 'and type' in cmd_lower or 'and write' in cmd_lower:
                # This is "erase X and type Y" command
                print("🧠 Context-aware command detected: Erase and replace")

                # First, select all and delete
                print("📍 Step 1: Selecting all text")
                engine.screen_agent.key_combination('ctrl', 'a')
                time.sleep(0.3)

                print("📍 Step 2: Deleting selected text")
                engine.screen_agent.press_key('delete')
                time.sleep(0.3)

                # Extract what to type
                import re
                type_match = re.search(r'(?:and\s+)?(?:type|write)\s+(.+)', cmd_lower)
                if type_match:
                    new_text = type_match.group(1).strip()
                    print(f"📍 Step 3: Typing new text: {new_text}")
                    engine.screen_agent.type_text(new_text)

                    # Update context
                    context.add_action('type', {'text': new_text})

                    success_msg = BytePersonality.random_choice(BytePersonality.SUCCESS)
                    print(f"✅ {success_msg}")
                    voice.speak(success_msg)
                    return True

        # Handle "windows key and type X and open it" pattern
        if 'windows key' in cmd_lower or 'win key' in cmd_lower:
            if 'and type' in cmd_lower and ('open it' in cmd_lower or 'launch it' in cmd_lower):
                print("🧠 Context-aware command detected: Windows search and open")

                # Press Windows key
                print("📍 Step 1: Pressing Windows key")
                engine.screen_agent.press_key('win')
                time.sleep(0.5)

                # Extract what to type
                import re
                type_match = re.search(r'(?:and\s+)?type\s+(.+?)\s+(?:and\s+)?(?:open|launch)', cmd_lower)
                if type_match:
                    search_text = type_match.group(1).strip()
                    print(f"📍 Step 2: Typing search: {search_text}")
                    engine.screen_agent.type_text(search_text)
                    time.sleep(0.5)

                    # Press Enter to open
                    print("📍 Step 3: Pressing Enter to open")
                    engine.screen_agent.press_key('enter')

                    # Update context
                    context.add_action('open', {'app': search_text})

                    success_msg = BytePersonality.random_choice(BytePersonality.SUCCESS)
                    print(f"✅ {success_msg}")
                    voice.speak(success_msg)
                    return True

        # Check if this is a multi-step command
        steps = nlp.split_multi_step_command(command_text)

        if len(steps) > 1:
            print(f"🔄 Multi-step command detected: {len(steps)} steps")
            all_success = True

            for i, step in enumerate(steps, 1):
                print(f"\n📍 Step {i}/{len(steps)}: {step}")

                # Parse and execute each step
                parsed = nlp.parse_command(step)
                print(f"🧠 Understanding: {parsed.action.value} on {parsed.application.value}")

                # Execute the step
                result = engine.execute_command(parsed)

                if result.status.value == 'completed':
                    print(f"✅ Step {i} completed")

                    # Track in context
                    if parsed.action.value == 'type':
                        context.add_action('type', {'text': parsed.target})
                    elif parsed.action.value == 'open':
                        context.add_action('open', {'app': parsed.application.value})

                    time.sleep(1)  # Small delay between steps
                else:
                    print(f"❌ Step {i} failed: {result.message}")
                    all_success = False
                    break

            if all_success:
                success_msg = BytePersonality.random_choice(BytePersonality.SUCCESS)
                print(f"\n✅ All steps {success_msg}")
                voice.speak(success_msg)
                return True
            else:
                voice.speak("Sorry, one of the steps didn't work")
                return False

        # Single command - handle normally
        parsed = nlp.parse_command(command_text)
        print(f"🧠 Understanding: {parsed.action.value} on {parsed.application.value}")

        # Check if we need to ask follow-up questions
        action_str = parsed.action.value.lower()
        app_str = parsed.application.value.lower()

        # Handle OPEN commands with smart opener
        if action_str == "open":
            # Extract app name from command
            app_name = extract_app_name(command_text)
            if app_name and smart_opener:
                print(f"🔍 Smart opening: {app_name}")
                result = smart_opener.open_app_smart(app_name)

                if result['status'] == 'completed':
                    context.add_action('open', {'app': app_name})
                    success_msg = BytePersonality.random_choice(BytePersonality.SUCCESS)
                    print(f"✅ {success_msg}")
                    return True
                elif result['status'] == 'already_open':
                    # Already handled by smart opener
                    return True
                elif result['status'] == 'cancelled':
                    return False
                else:
                    # Fall back to old method
                    action_details = intelligent.handle_ambiguous_open_command(app_name)
                    return execute_intelligent_action(action_details, voice, engine)
            elif app_name:
                # No smart opener, use old method
                action_details = intelligent.handle_ambiguous_open_command(app_name)
                return execute_intelligent_action(action_details, voice, engine)

        # Handle SEARCH commands with intelligence
        elif action_str == "search":
            query = parsed.parameters.get("query", command_text)
            action_details = intelligent.handle_search_command(query)
            return execute_search_action(action_details, voice)

        # Execute normally
        result = engine.execute_command(parsed)

        if result.status.value == 'completed':
            # Track in context
            if parsed.action.value == 'type':
                context.add_action('type', {'text': parsed.target})
            elif parsed.action.value == 'open':
                context.add_action('open', {'app': parsed.application.value})

            success_msg = BytePersonality.random_choice(BytePersonality.SUCCESS)
            print(f"✅ {success_msg}")
            voice.speak(success_msg)
            return True
        else:
            print(f"❌ Failed: {result.message}")
            voice.speak("Sorry, that didn't work")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        voice.speak("Error occurred")
        return False


def extract_app_name(command_text):
    """Extract application name from command."""
    # Remove common words
    words_to_remove = ["open", "launch", "start", "run", "please", "kindly", "can", "you", "the", "a", "an"]
    words = command_text.lower().split()
    app_words = [w for w in words if w not in words_to_remove]
    return " ".join(app_words) if app_words else None


def execute_intelligent_action(action_details, voice, engine):
    """Execute action from intelligent assistant."""
    action = action_details.get("action")
    
    if action == "cancel":
        print(f"❌ Cancelled: {action_details.get('message')}")
        voice.speak("Okay, cancelled")
        return False
    
    elif action == "open_local":
        app_path = action_details.get("app_path")
        try:
            subprocess.Popen([app_path])
            print(f"✅ Opened {action_details.get('app_name')}")
            voice.speak("Done!")
            return True
        except Exception as e:
            print(f"❌ Failed to open: {e}")
            voice.speak("Failed to open")
            return False
    
    elif action == "open_browser":
        url = action_details.get("url")
        browser = action_details.get("browser", "chrome")
        try:
            if browser == "chrome":
                subprocess.Popen(["start", "chrome", url], shell=True)
            elif browser == "firefox":
                subprocess.Popen(["start", "firefox", url], shell=True)
            elif browser == "edge":
                subprocess.Popen(["start", "msedge", url], shell=True)
            print(f"✅ Opened in {browser}")
            voice.speak("Done!")
            return True
        except Exception as e:
            print(f"❌ Failed: {e}")
            voice.speak("Failed")
            return False
    
    return False


def execute_search_action(action_details, voice):
    """Execute search action."""
    query = action_details.get("query")
    engine_name = action_details.get("engine", "google")
    browser = action_details.get("browser", "chrome")
    
    # Build search URL
    search_urls = {
        "google": f"https://www.google.com/search?q={query.replace(' ', '+')}",
        "bing": f"https://www.bing.com/search?q={query.replace(' ', '+')}",
        "duckduckgo": f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
    }
    
    url = search_urls.get(engine_name, search_urls["google"])
    
    try:
        if browser == "chrome":
            subprocess.Popen(["start", "chrome", url], shell=True)
        elif browser == "firefox":
            subprocess.Popen(["start", "firefox", url], shell=True)
        elif browser == "edge":
            subprocess.Popen(["start", "msedge", url], shell=True)
        
        print(f"✅ Searching {engine_name} for '{query}' in {browser}")
        voice.speak("Done!")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        voice.speak("Failed")
        return False


# Helper functions
def is_wake_word(text):
    return any(word in text for word in ["byte", "bite", "bait"])

def is_sleep_command(text):
    return any(word in text for word in ["sleep", "so ja", "rest", "nap"])

def is_exit_command(text):
    return any(word in text for word in ["exit", "quit", "goodbye", "bye bye", "shutdown"])

def is_positive_response(text):
    return any(word in text for word in ["yes", "yeah", "yep", "sure", "okay", "ok", "han", "haan"])

def is_negative_response(text):
    return any(word in text for word in ["no", "nope", "nothing", "nahi", "na", "nah"])


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

