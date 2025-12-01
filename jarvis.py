#!/usr/bin/env python3
"""
JARVIS - Just A Rather Very Intelligent System
Inspired by Iron Man

Features:
- Wake word: "JARVIS"
- Personality: Tony Stark's JARVIS (calls user "Lucky")
- Install apps using winget
- Go to websites directly
- Intelligent follow-up questions
- Checks if apps are installed
- Sleep mode
"""

import sys
import os
import random
import time
import subprocess
import re
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import threading
from src.gui.jarvis_overlay import JarvisOverlay

class ContextMemory:
    """Remembers what JARVIS has done recently."""

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


class JarvisPersonality:
    """JARVIS personality and responses."""
    
    GREETINGS = [
        "Good to see you, Lucky. How may I be of assistance?",
        "At your service, Lucky. What can I do for you?",
        "Hello, Lucky. I'm here to help.",
        "Yes, Lucky. What do you need?",
        "Ready and waiting, Lucky."
    ]
    
    ACKNOWLEDGMENTS = [
        "Right away, Lucky.",
        "Certainly, Lucky.",
        "Of course, Lucky.",
        "On it, Lucky.",
        "Consider it done, Lucky."
    ]
    
    SUCCESS = [
        "Task completed, Lucky.",
        "Done, Lucky.",
        "All finished, Lucky.",
        "Mission accomplished, Lucky.",
        "Successfully executed, Lucky."
    ]
    
    FEEDBACK_QUESTIONS = [
        "Anything else, Lucky?",
        "What's next on the agenda?",
        "Shall we continue?",
        "Any other protocols to run?",
        "Standing by for further instructions."
    ]
    
    SLEEP_MESSAGES = [
        "Going into sleep mode, Lucky. Say 'JARVIS' to wake me.",
        "Powering down non-essential systems.",
        "Standing by in low power mode.",
        "I'll be here if you need me, Lucky.",
        "Resting now."
    ]
    
    @staticmethod
    def random_choice(messages):
        return random.choice(messages)


def print_box(text, char="="):
    """Print text in a box."""
    print("\n" + char * 70)
    print(text.center(70))
    print(char * 70 + "\n")


def install_app(app_name, voice):
    """Install an application using winget."""
    print(f"⬇️ Installing {app_name}...")
    voice.speak(f"Attempting to install {app_name}, Lucky. This might take a moment.")
    
    try:
        # Run winget search to check if it exists
        search_cmd = f"winget search \"{app_name}\""
        result = subprocess.run(search_cmd, shell=True, capture_output=True, text=True)
        
        if "No package found" in result.stdout:
            print(f"❌ Could not find {app_name}")
            voice.speak(f"I couldn't find {app_name} in the repository, Lucky.")
            return False
            
        # If found, install
        voice.speak(f"Found {app_name}. Starting installation. Please check for any prompts.")
        # Open a new terminal for installation so the user can see/interact
        install_cmd = f"start cmd /k winget install \"{app_name}\""
        subprocess.Popen(install_cmd, shell=True)
        
        return True
    except Exception as e:
        print(f"❌ Error installing: {e}")
        voice.speak("There was an error initiating the installation protocol.")
        return False


def go_to_website(url, voice):
    """Go to a specific website."""
    # Clean up URL
    url = url.lower().strip()
    if url.startswith("go to "):
        url = url[6:]
    if url.startswith("visit "):
        url = url[6:]
        
    # Add https if missing
    if not url.startswith('http'):
        if not url.startswith('www.') and '.' not in url:
            url = f"{url}.com"
        url = 'https://' + url
    
    print(f"🌐 Visiting {url}...")
    voice.speak(f"Navigating to {url}, Lucky.")
    
    try:
        # Try Chrome first
        subprocess.Popen(f"start chrome {url}", shell=True)
        return True
    except:
        try:
            # Try Edge
            subprocess.Popen(f"start msedge {url}", shell=True)
            return True
        except:
            voice.speak("I couldn't open the browser, Lucky.")
            return False


def main():
    print_box("🤖 JARVIS - Just A Rather Very Intelligent System", "=")
    
    print("Features:")
    print("  ✅ Wake word: 'JARVIS'")
    print("  ✅ Personality: Iron Man Style")
    print("  ✅ Install Apps (winget)")
    print("  ✅ Go to Websites")
    print("  ✅ Intelligent Task Execution")
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
        
        print("🔧 Initializing JARVIS systems...")
        
        voice = IndianEnglishVoiceProcessor(
            wake_word="jarvis",
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

        # Shared state for interruption
        interrupt_event = threading.Event()

        # Initialize system search handler with interrupt event
        system_search = SystemSearchHandler(voice, interrupt_event=interrupt_event)

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
        
        print("✅ JARVIS is online!\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Start
    run_jarvis(voice, nlp, engine, intelligent, context, smart_opener, interrupt_event)


def run_jarvis(voice, nlp, engine, intelligent, context, smart_opener, interrupt_event):
    """Main JARVIS interaction loop with GUI."""
    
    # Shared state
    state = {
        "running": True,
        "interrupted": False
    }

    def on_interrupt():
        state["interrupted"] = True
        interrupt_event.set() # Signal interruption to handlers
        voice.stop_speaking()
        print("Interruption requested!")
    
    overlay = JarvisOverlay(on_interrupt=on_interrupt)
    
    def logic_thread():
        try:
            _jarvis_logic(voice, nlp, engine, intelligent, context, smart_opener, overlay, state)
        except Exception as e:
            print(f"Error in logic thread: {e}")
            import traceback
            traceback.print_exc()
        finally:
            overlay.close()

    t = threading.Thread(target=logic_thread, daemon=True)
    t.start()
    
    overlay.run()
    state["running"] = False


def _jarvis_logic(voice, nlp, engine, intelligent, context, smart_opener, overlay, state):
    """Main JARVIS interaction loop logic."""
    
    print_box("🤖 JARVIS is Active!", "-")
    overlay.update_status("Active", "#00FF00")
    overlay.update_text("I am JARVIS. How can I help you?")
    
    # Initial greeting
    greeting = JarvisPersonality.random_choice(JarvisPersonality.GREETINGS)
    print(f"🤖 JARVIS: {greeting}\n")
    voice.speak(greeting)
    
    is_awake = True
    task_count = 0
    
    try:
        while state["running"]:
            print("-" * 70)
            
            # Check for interruption
            if state["interrupted"]:
                state["interrupted"] = False
                interrupt_event.clear() # Reset interrupt signal
                voice.stop_speaking()
                overlay.update_status("Interrupted", "#FF4444")
                overlay.update_text("Ready for new command...")
                time.sleep(0.5)
                # Continue loop to listen again
            
            if is_awake:
                # Awake mode
                print("🎤 Listening... (say 'JARVIS' for new task, or give command)")
                overlay.update_status("Listening...", "#00FFFF")
                
                command = listen_for_input(voice)
                
                if not command:
                    continue
                
                overlay.update_text(f"You said: {command}")
                cmd_lower = command.lower().strip()
                
                # Check for sleep
                if is_sleep_command(cmd_lower):
                    is_awake = False
                    sleep_msg = JarvisPersonality.random_choice(JarvisPersonality.SLEEP_MESSAGES)
                    print(f"\n😴 JARVIS: {sleep_msg}\n")
                    overlay.update_status("Sleeping", "#888888")
                    overlay.update_text(sleep_msg)
                    voice.speak(sleep_msg)
                    continue
                
                # Check for exit
                if is_exit_command(cmd_lower):
                    print("\n🤖 JARVIS: Goodbye, Lucky!\n")
                    overlay.update_status("Goodbye", "#FF0000")
                    voice.speak("Goodbye, Lucky!")
                    break
                
                # Check for wake word
                if is_wake_word(cmd_lower):
                    greeting = JarvisPersonality.random_choice(JarvisPersonality.GREETINGS)
                    print(f"\n🤖 JARVIS: {greeting}\n")
                    overlay.update_text(greeting)
                    voice.speak(greeting)
                    
                    # Listen for command
                    print("🎤 Listening for your command...")
                    overlay.update_status("Listening for command...", "#00FFFF")
                    command = listen_for_input(voice)
                    if not command:
                        continue
                    overlay.update_text(f"Command: {command}")
                    cmd_lower = command.lower().strip()
                
                # Execute with intelligence
                if not is_sleep_command(cmd_lower) and not is_exit_command(cmd_lower):
                    overlay.update_status("Processing...", "#FFFF00")
                    success = execute_jarvis_command(command, nlp, engine, voice, intelligent, context, smart_opener)
                    if success:
                        task_count += 1
                    
                    # Ask for feedback
                    time.sleep(0.5)
                    feedback_q = JarvisPersonality.random_choice(JarvisPersonality.FEEDBACK_QUESTIONS)
                    print(f"\n🤖 JARVIS: {feedback_q}\n")
                    overlay.update_text(feedback_q)
                    voice.speak(feedback_q)
                    
                    # Listen for response
                    print("🎤 Listening for response...")
                    overlay.update_status("Listening for response...", "#00FFFF")
                    response = listen_for_input(voice, timeout=15)
                    
                    if response:
                        overlay.update_text(f"Response: {response}")
                        resp_lower = response.lower().strip()
                        
                        if is_sleep_command(resp_lower) or is_negative_response(resp_lower):
                            is_awake = False
                            sleep_msg = JarvisPersonality.random_choice(JarvisPersonality.SLEEP_MESSAGES)
                            print(f"\n😴 JARVIS: {sleep_msg}\n")
                            overlay.update_status("Sleeping", "#888888")
                            overlay.update_text(sleep_msg)
                            voice.speak(sleep_msg)
                        elif is_positive_response(resp_lower):
                            print("\n🤖 JARVIS: Very well. What is the next task?\n")
                            overlay.update_text("Ready for next task")
                            voice.speak("Very well. What is the next task?")
                        else:
                            # Treat as new command
                            execute_jarvis_command(response, nlp, engine, voice, intelligent, context, smart_opener)
                            task_count += 1
                    else:
                        # No response - go to sleep
                        is_awake = False
                        sleep_msg = JarvisPersonality.random_choice(JarvisPersonality.SLEEP_MESSAGES)
                        print(f"\n😴 JARVIS: {sleep_msg}\n")
                        overlay.update_status("Sleeping", "#888888")
                        voice.speak(sleep_msg)
            
            else:
                # Sleep mode
                print("😴 Sleeping... Say 'JARVIS' to wake me up")
                overlay.update_status("Sleeping (Say 'JARVIS')", "#555555")
                command = listen_for_input(voice, timeout=60)
                
                if command and is_wake_word(command.lower()):
                    is_awake = True
                    greeting = JarvisPersonality.random_choice(JarvisPersonality.GREETINGS)
                    print(f"\n🤖 JARVIS: {greeting}\n")
                    overlay.update_status("Waking up...", "#00FF00")
                    voice.speak(greeting)
    
    except KeyboardInterrupt:
        print(f"\n\n🤖 JARVIS: Completed {task_count} tasks. Goodbye, Lucky!\n")
        voice.speak("Goodbye, Lucky!")
        voice.cleanup()


def listen_for_input(voice, timeout=20):
    """Listen for voice input."""
    try:
        command = voice.listen_once(timeout=timeout, phrase_time_limit=30)
        return command
    except Exception as e:
        print(f"⚠️  Listening error: {e}")
        return None


def execute_jarvis_command(command_text, nlp, engine, voice, intelligent, context, smart_opener=None):
    """Execute command with JARVIS intelligence."""
    import re
    import logging
    print(f"\n[CMD] Command: {command_text}")

    # Acknowledge
    ack = JarvisPersonality.random_choice(JarvisPersonality.ACKNOWLEDGMENTS)
    print(f"[JARVIS] JARVIS: {ack}")
    voice.speak(ack)

    try:
        cmd_lower = command_text.lower()

        # 1. Check for SHUTDOWN command (flexible patterns)
        shutdown_patterns = [
            r'\b(shutdown|shut\s+down)\s+(the\s+)?(system|computer|pc|machine)\b',
            r'\bpower\s+off\b',
            r'\bshutdown\b(?!\s+\w)',  # "shutdown" not followed by another word (to avoid "shutdown chrome")
            r'\bshut\s+down\b(?!\s+(the|a|an|my)\s+\w)',  # "shut down" not followed by "the/a/an/my [app]"
        ]
        
        if any(re.search(pattern, cmd_lower) for pattern in shutdown_patterns):
            print("[SHUTDOWN] System shutdown requested")
            voice.speak("Initiating system shutdown sequence, Lucky.")
            
            # Check if we should close all apps first
            if 'close all' in cmd_lower or 'close apps' in cmd_lower:
                print("[SHUTDOWN] Closing all applications first...")
                voice.speak("Closing all applications first.")
                try:
                    # Close all windows using Alt+F4 in a loop
                    import pyautogui
                    for _ in range(10):  # Close up to 10 windows
                        pyautogui.hotkey('alt', 'f4')
                        time.sleep(0.3)
                except Exception as e:
                    print(f"[WARNING] Error closing apps: {e}")
            
            # Initiate shutdown
            print("[SHUTDOWN] Shutting down system...")
            voice.speak("Goodbye, Lucky. Shutting down now.")
            time.sleep(2)  # Give time for speech
            
            try:
                subprocess.run(["shutdown", "/s", "/t", "5"], check=True)
                return True
            except Exception as e:
                print(f"[ERROR] Shutdown failed: {e}")
                voice.speak("I encountered an error initiating shutdown, Lucky.")
                return False

        # 2. Check for INSTALL command
        if "install" in cmd_lower:
            # Extract app name
            app_name = cmd_lower.split("install")[-1].strip()
            if app_name:
                return install_app(app_name, voice)
        
        # 3. Check for GO TO WEBSITE command
        if "go to" in cmd_lower and ("website" in cmd_lower or ".com" in cmd_lower or "www" in cmd_lower or "http" in cmd_lower):
            # Extract URL
            url = cmd_lower.split("go to")[-1].strip()
            # Remove "website" if present
            url = url.replace("website", "").strip()
            if url:
                return go_to_website(url, voice)
        
        if "visit" in cmd_lower:
             url = cmd_lower.split("visit")[-1].strip()
             if url:
                 return go_to_website(url, voice)

        # 4. Check for MINIMIZE ALL WINDOWS command
        if re.search(r'\b(minimize|minimise)\s+(all\s+)?(windows|window|apps|applications)\b', cmd_lower):
            print("[MINIMIZE] Minimizing all windows")
            voice.speak("Minimizing all windows, Lucky.")
            
            try:
                import pyautogui
                # Use Win+M to minimize all windows
                pyautogui.hotkey('win', 'm')
                
                success_msg = JarvisPersonality.random_choice(JarvisPersonality.SUCCESS)
                print(f"[SUCCESS] {success_msg}")
                voice.speak(success_msg)
                return True
            except Exception as e:
                print(f"[ERROR] Minimize failed: {e}")
                voice.speak("I encountered an error minimizing windows, Lucky.")
                return False

        # 5. Check for LIST MACROS / VIEW MACRO LIST command
        if re.search(r'\b(list|view|show)\s+(macros?|macro\s+list|recordings?)\b', cmd_lower):
            print("[MACROS] Listing available macros")
            voice.speak("Let me check the available macros, Lucky.")
            
            try:
                from pathlib import Path
                macro_dir = Path("macros")
                
                if not macro_dir.exists() or not list(macro_dir.glob("*.json")):
                    print("[MACROS] No macros found")
                    voice.speak("I couldn't find any recorded macros, Lucky.")
                    return False
                
                macro_files = list(macro_dir.glob("*.json"))
                macro_names = [f.stem for f in macro_files]
                
                print(f"[MACROS] Found {len(macro_names)} macros:")
                for name in macro_names:
                    print(f"  - {name}")
                
                # Speak the list
                if len(macro_names) == 1:
                    voice.speak(f"I found one macro: {macro_names[0]}")
                else:
                    macro_list = ", ".join(macro_names[:-1]) + f", and {macro_names[-1]}"
                    voice.speak(f"I found {len(macro_names)} macros: {macro_list}")
                
                return True
            except Exception as e:
                print(f"[ERROR] Failed to list macros: {e}")
                voice.speak("I encountered an error listing macros, Lucky.")
                return False

        # 6. Check for PLAY MACRO command
        if re.search(r'\b(play|run|execute)\s+(macro|recording)\s+(.+)', cmd_lower):
            match = re.search(r'\b(play|run|execute)\s+(macro|recording)\s+(.+)', cmd_lower)
            if match:
                macro_name = match.group(3).strip()
                print(f"[MACRO] Playing macro: {macro_name}")
                voice.speak(f"Playing macro {macro_name}, Lucky.")
                
                try:
                    from pathlib import Path
                    import json
                    
                    macro_dir = Path("macros")
                    macro_file = macro_dir / f"{macro_name}.json"
                    
                    if not macro_file.exists():
                        print(f"[ERROR] Macro '{macro_name}' not found")
                        voice.speak(f"I couldn't find a macro named {macro_name}, Lucky.")
                        return False
                    
                    # Import and play
                    from src.core.macro_recorder import MacroRecorder
                    MacroRecorder.play_file(str(macro_file))
                    
                    success_msg = JarvisPersonality.random_choice(JarvisPersonality.SUCCESS)
                    print(f"[SUCCESS] {success_msg}")
                    voice.speak(success_msg)
                    return True
                    
                except Exception as e:
                    print(f"[ERROR] Macro playback failed: {e}")
                    voice.speak("I encountered an error playing the macro, Lucky.")
                    return False

        # 7. Handle "erase that and type X" pattern
        if 'erase' in cmd_lower or 'clear' in cmd_lower or 'delete' in cmd_lower:
            if 'and type' in cmd_lower or 'and write' in cmd_lower:
                # This is "erase X and type Y" command
                print("[NLP] Context-aware command detected: Erase and replace")

                # First, select all and delete
                print("[STEP] Step 1: Selecting all text")
                engine.screen_agent.key_combination('ctrl', 'a')
                time.sleep(0.3)

                print("[STEP] Step 2: Deleting selected text")
                engine.screen_agent.press_key('delete')
                time.sleep(0.3)

                # Extract what to type
                import re
                type_match = re.search(r'(?:and\s+)?(?:type|write)\s+(.+)', cmd_lower)
                if type_match:
                    new_text = type_match.group(1).strip()
                    print(f"[STEP] Step 3: Typing new text: {new_text}")
                    engine.screen_agent.type_text(new_text)

                    # Update context
                    context.add_action('type', {'text': new_text})

                    success_msg = JarvisPersonality.random_choice(JarvisPersonality.SUCCESS)
                    print(f"[SUCCESS] {success_msg}")
                    voice.speak(success_msg)
                    return True

        # 8. Handle "windows key and type X and open it" pattern
        if 'windows key' in cmd_lower or 'win key' in cmd_lower:
            if 'and type' in cmd_lower and ('open it' in cmd_lower or 'launch it' in cmd_lower):
                print("[NLP] Context-aware command detected: Windows search and open")

                # Press Windows key
                print("[STEP] Step 1: Pressing Windows key")
                engine.screen_agent.press_key('win')
                time.sleep(0.5)

                # Extract what to type
                import re
                type_match = re.search(r'(?:and\s+)?type\s+(.+?)\s+(?:and\s+)?(?:open|launch)', cmd_lower)
                if type_match:
                    search_text = type_match.group(1).strip()
                    print(f"[STEP] Step 2: Typing search: {search_text}")
                    engine.screen_agent.type_text(search_text)
                    time.sleep(0.5)

                    # Press Enter to open
                    print("[STEP] Step 3: Pressing Enter to open")
                    engine.screen_agent.press_key('enter')

                    # Update context
                    context.add_action('open', {'app': search_text})

                    success_msg = JarvisPersonality.random_choice(JarvisPersonality.SUCCESS)
                    print(f"[SUCCESS] {success_msg}")
                    voice.speak(success_msg)
                    return True

        # 9. Check if this is a multi-step command
        steps = nlp.split_multi_step_command(command_text)

        if len(steps) > 1:
            print(f"[MULTI] Multi-step command detected: {len(steps)} steps")
            all_success = True

            for i, step in enumerate(steps, 1):
                print(f"\n[STEP] Step {i}/{len(steps)}: {step}")

                # Parse and execute each step
                parsed = nlp.parse_command(step)
                print(f"[NLP] Understanding: {parsed.action.value} on {parsed.application.value}")

                # Execute the step
                result = engine.execute_command(parsed)

                if result.status.value == 'completed':
                    print(f"[SUCCESS] Step {i} completed")

                    # Track in context
                    if parsed.action.value == 'type':
                        context.add_action('type', {'text': parsed.target})
                    elif parsed.action.value == 'open':
                        context.add_action('open', {'app': parsed.application.value})

                    time.sleep(1)  # Small delay between steps
                else:
                    print(f"[FAILED] Step {i} failed: {result.message}")
                    all_success = False
                    break

            if all_success:
                success_msg = JarvisPersonality.random_choice(JarvisPersonality.SUCCESS)
                print(f"\n[SUCCESS] All steps {success_msg}")
                voice.speak(success_msg)
                return True
            else:
                voice.speak("Sorry Lucky, one of the steps didn't execute correctly.")
                return False

        # 10. Single command - handle normally
        parsed = nlp.parse_command(command_text)
        print(f"[NLP] Understanding: {parsed.action.value} on {parsed.application.value}")

        # Check if we need to ask follow-up questions
        action_str = parsed.action.value.lower()
        app_str = parsed.application.value.lower()

        # Handle OPEN commands with smart opener
        if action_str == "open":
            # Extract app name from command
            app_name = extract_app_name(command_text)
            
            # Check for force windows search flag from NLP
            force_windows = parsed.parameters.get('force_windows_search', False)
            
            # If forced, clean up app name further to remove "using windows" if extract_app_name missed it
            if force_windows and app_name:
                app_name = re.sub(r'\b(using|in|with|via)\s+windows\b', '', app_name).strip()
            
            if app_name and smart_opener:
                print(f"[SMART] Smart opening: {app_name} (Force Windows: {force_windows})")
                logging.info(f"Smart opening: {app_name} (Force Windows: {force_windows})")
                result = smart_opener.open_app_smart(app_name, force_windows_search=force_windows)
                logging.info(f"Smart opener result: {result}")

                if result['status'] == 'completed':
                    context.add_action('open', {'app': app_name})
                    success_msg = JarvisPersonality.random_choice(JarvisPersonality.SUCCESS)
                    print(f"[SUCCESS] {success_msg}")
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

            success_msg = JarvisPersonality.random_choice(JarvisPersonality.SUCCESS)
            print(f"[SUCCESS] {success_msg}")
            voice.speak(success_msg)
            return True
        elif result.status.value == 'ambiguous':
            # Handle ambiguity
            print(f"[AMBIGUOUS] Ambiguous: {result.message}")
            voice.speak(result.message)
            
            # Listen for clarification
            print("[MIC] Listening for clarification...")
            clarification = listen_for_input(voice, timeout=10)
            
            if clarification:
                # Construct new command with clarification
                new_command = f"{command_text} {clarification}"
                print(f"[RETRY] Retrying with: {new_command}")
                return execute_jarvis_command(new_command, nlp, engine, voice, intelligent, context, smart_opener)
            else:
                voice.speak("I didn't hear a clarification, Lucky.")
                return False
        else:
            print(f"[FAILED] Failed: {result.message}")
            voice.speak("I encountered an error executing that command, Lucky.")
            return False

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        voice.speak("System error detected.")
        return False


def extract_app_name(command_text):
    """Extract application name from command."""
    # Remove common words and phrases
    text = command_text.lower()
    
    # Remove phrases
    phrases_to_remove = [
        "using windows", "in windows", "with windows", "via windows",
        "please", "kindly", "can you", "could you", "would you"
    ]
    
    for phrase in phrases_to_remove:
        text = text.replace(phrase, "")
        
    # Remove start verbs
    verbs = ["open", "launch", "start", "run", "bring up", "show me"]
    for verb in verbs:
        if text.startswith(verb):
            text = text[len(verb):].strip()
    
    # Remove articles and filler words
    words_to_remove = ["the", "a", "an", "app", "application", "software", "softwares"]
    words = text.split()
    app_words = [w for w in words if w not in words_to_remove]
    
    clean_name = " ".join(app_words) if app_words else None
    
    # Phonetic corrections
    if clean_name:
        corrections = {
            "dolby axis": "dolby access",
            "dolby axes": "dolby access",
            "dolby excess": "dolby access",
            "vs code": "vscode",
            "visual studio": "vscode",
            "chrome browser": "chrome",
            "edge browser": "edge"
        }
        for wrong, right in corrections.items():
            if wrong in clean_name:
                clean_name = clean_name.replace(wrong, right)
                
    return clean_name


def execute_intelligent_action(action_details, voice, engine):
    """Execute action from intelligent assistant."""
    action = action_details.get("action")
    
    if action == "cancel":
        print(f"❌ Cancelled: {action_details.get('message')}")
        voice.speak("Operation cancelled, Lucky.")
        return False
    
    elif action == "open_local":
        app_path = action_details.get("app_path")
        try:
            subprocess.Popen([app_path])
            print(f"✅ Opened {action_details.get('app_name')}")
            voice.speak("Application launched, Lucky.")
            return True
        except Exception as e:
            print(f"❌ Failed to open: {e}")
            voice.speak("I failed to launch the application, Lucky.")
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
            voice.speak("Browser launched, Lucky.")
            return True
        except Exception as e:
            print(f"❌ Failed: {e}")
            voice.speak("Browser launch failed.")
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
        voice.speak("Search initiated, Lucky.")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        voice.speak("Search failed.")
        return False


# Helper functions
def is_wake_word(text):
    return any(word in text for word in ["jarvis", "jarves", "jar vis"])

def is_sleep_command(text):
    return any(word in text for word in ["sleep", "standby", "rest", "power down"])

def is_exit_command(text):
    return any(word in text for word in ["exit", "quit", "goodbye", "bye"])

def is_positive_response(text):
    return any(word in text for word in ["yes", "yeah", "yep", "sure", "okay", "ok", "affirmative", "proceed"])

def is_negative_response(text):
    return any(word in text for word in ["no", "nope", "nothing", "negative", "cancel"])


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
