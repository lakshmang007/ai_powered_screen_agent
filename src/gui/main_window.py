"""
Main GUI window for the AI-Powered Screen Agent.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import threading
import logging
from typing import Optional
import time
import os

from ..core.screen_agent import ScreenAgent
from ..core.voice_processor import VoiceProcessor
from ..core.nlp_processor import NLPProcessor, ParsedCommand, ApplicationType
from ..automation.task_engine import TaskEngine, TaskResult, TaskStatus
from ..automation.handlers import VSCodeHandler, GmailHandler, LinkedInHandler, BrowserHandler
from .jarvis_overlay import JarvisOverlay

class MainWindow:
    """Main application window."""
    
    def __init__(self):
        """Initialize the main window."""
        self.root = tk.Tk()
        self.root.title("AI-Powered Screen Agent - Byte Smart")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)

        # Initialize core components
        self.screen_agent = ScreenAgent()

        # Try to use Indian English Voice Processor (Byte Smart)
        try:
            from ..core.indian_english_voice_processor import IndianEnglishVoiceProcessor
            self.voice_processor = IndianEnglishVoiceProcessor(wake_word="jarvis")
            self.has_byte_smart = True
        except Exception as e:
            logging.getLogger(__name__).warning(f"Falling back to basic voice processor: {e}")
            self.voice_processor = VoiceProcessor()
            self.has_byte_smart = False

        # Initialize NLP with AI support
        self.nlp_processor = NLPProcessor(use_ai=True)
        self.task_engine = TaskEngine(self.screen_agent)

        # Initialize Smart App Opener
        try:
            from ..automation.handlers.smart_app_opener import SmartAppOpener
            from ..automation.handlers.system_search_handler import SystemSearchHandler
            system_search = SystemSearchHandler(voice_processor=self.voice_processor)
            self.smart_opener = SmartAppOpener(voice_processor=self.voice_processor,
                                              system_search_handler=system_search)
            self.has_smart_opener = True
        except Exception:
            self.smart_opener = None
            self.has_smart_opener = False

        # Initialize Context Memory (for Byte Smart)
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from byte_smart import ContextMemory
            self.context_memory = ContextMemory()
            self.has_context_memory = True
        except ImportError:
            self.context_memory = None
            self.has_context_memory = False

        # Initialize Macro Recorder
        try:
            from ..core.macro_recorder import MacroRecorder, HAS_PYNPUT
            self.macro_recorder = None  # Will be created when recording starts
            self.has_macro_support = HAS_PYNPUT  # Check if pynput is actually available
            self.is_recording_macro = False
            self.macro_save_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "macros")
            os.makedirs(self.macro_save_dir, exist_ok=True)
        except ImportError:
            self.has_macro_support = False
            self.is_recording_macro = False

        # Initialize handlers
        self._setup_handlers()

        # GUI state
        self.is_listening = False
        self.current_task = None
        self.byte_smart_mode = False  # Wake word mode

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Overlay for JARVIS mode
        self.overlay = None

        # Create GUI elements
        self._create_widgets()
        self._setup_layout()
        self._setup_bindings()

        # Start the application
        self._setup_logging_display()
        
        # Setup global shortcuts
        self.root.after(1000, self._setup_global_shortcuts)
    
    def _setup_handlers(self):
        """Setup application-specific handlers."""
        
        # Register handlers with the task engine
        vscode_handler = VSCodeHandler(self.screen_agent)
        gmail_handler = GmailHandler(self.screen_agent)
        linkedin_handler = LinkedInHandler(self.screen_agent)
        browser_handler = BrowserHandler(self.screen_agent)
        
        self.task_engine.register_app_handler(ApplicationType.VSCODE, vscode_handler.handle_command)
        self.task_engine.register_app_handler(ApplicationType.GMAIL, gmail_handler.handle_command)
        self.task_engine.register_app_handler(ApplicationType.LINKEDIN, linkedin_handler.handle_command)
        self.task_engine.register_app_handler(ApplicationType.CHROME, browser_handler.handle_command)
        self.task_engine.register_app_handler(ApplicationType.MACRO, self._handle_macro_command)

    def _handle_macro_command(self, command: ParsedCommand) -> TaskResult:
        """Handle macro-related commands."""
        from ..core.nlp_processor import ActionType
        
        target = command.target
        
        # Check if it's a general "open list" command
        is_general_open = False
        
        # Explicitly check for "list macros" or "show macros" which might come as OPEN action
        if command.action in [ActionType.OPEN, ActionType.CLICK]:
            if not target:
                # "Open macros" (target might be empty if application is MACRO)
                is_general_open = True
            elif target.lower() in ['macros', 'macro list', 'list', 'the list', 'all macros', 'macro']:
                is_general_open = True
            elif "list" in target.lower() and "macro" in target.lower():
                # e.g. "list macros" -> target might be "list macros"
                is_general_open = True

        if is_general_open:
            # "Open macros" -> Open list
            # Bring main window to front first
            self.root.after(0, self._bring_to_front)
            self.root.after(100, self._show_macro_list)
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message="Opened macro list"
            )
            
        elif command.action == ActionType.PLAY or (command.action == ActionType.OPEN and target):
            # "Play macro X" or "Open macro X" (interpreted as play)
            if not target:
                return TaskResult(
                    status=TaskStatus.FAILED,
                    message="Please specify which macro to play (e.g., 'play macro 1')"
                )
            
            # Clean target (remove "play with", "macro", etc.)
            clean_target = target.lower()
            clean_target = clean_target.replace("play with", "")
            clean_target = clean_target.replace("play", "")
            clean_target = clean_target.replace("macro", "") # Remove "macro" word to find name
            clean_target = clean_target.strip()
            
            # If target became empty (e.g. user said "play macro"), fail
            if not clean_target:
                 return TaskResult(
                    status=TaskStatus.FAILED,
                    message="Please specify a macro name"
                )

            # Find macro
            macro_path = self._get_macro_by_identifier(clean_target)
            if macro_path:
                # Play it
                self.root.after(0, lambda: self._play_macro_by_path(macro_path))
                return TaskResult(
                    status=TaskStatus.COMPLETED,
                    message=f"Playing macro: {macro_path.stem}"
                )
            else:
                return TaskResult(
                    status=TaskStatus.FAILED,
                    message=f"Could not find macro matching '{target}'"
                )
                
        return TaskResult(
            status=TaskStatus.FAILED,
            message=f"Unsupported macro action: {command.action.value}"
        )

    def _bring_to_front(self):
        """Bring the main window to the front."""
        if self.root.state() == 'iconic':
            self.root.deiconify()
        self.root.lift()
        self.root.focus_force()


    def _get_macro_by_identifier(self, identifier: str) -> Optional[str]:
        """Find macro path by name or index (1-based)."""
        from pathlib import Path
        macro_dir = Path(self.macro_save_dir)
        if not macro_dir.exists():
            return None
            
        # Get all macros sorted by creation time (oldest first)
        # This ensures "macro 1" is consistent
        macros = sorted(list(macro_dir.glob("*.json")), key=os.path.getctime)
        
        if not macros:
            return None
            
        identifier_lower = identifier.lower()
        
        # Handle "last", "latest", "recent"
        if any(w in identifier_lower for w in ['last', 'latest', 'newest', 'recent', 'recorded']):
             return macros[-1]
            
        # Check if identifier is a number
        # Convert words to numbers if needed
        number_map = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
        }
        
        index = None
        if identifier.isdigit():
            index = int(identifier)
        elif identifier_lower in number_map:
            index = number_map[identifier_lower]
            
        if index is not None:
            # 1-based index
            if 1 <= index <= len(macros):
                return macros[index - 1]
        
        # Check by name (fuzzy match)
        for m in macros:
            if identifier_lower in m.stem.lower():
                return m
                
        return None
    
    def _create_widgets(self):
        """Create GUI widgets."""
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        
        # Title
        self.title_label = ttk.Label(
            self.main_frame, 
            text="AI-Powered Screen Agent", 
            font=("Arial", 16, "bold")
        )
        
        # Status frame
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_label = ttk.Label(self.status_frame, text="Status: Ready")
        self.status_indicator = tk.Canvas(self.status_frame, width=20, height=20)
        self.status_indicator.create_oval(2, 2, 18, 18, fill="green", outline="darkgreen")
        
        # Command input frame
        self.input_frame = ttk.LabelFrame(self.main_frame, text="Command Input", padding="5")
        
        # Text input
        self.text_input = ttk.Entry(self.input_frame, font=("Arial", 11))
        self.text_input.bind('<Return>', self._on_text_command)
        
        # Buttons frame
        self.buttons_frame = ttk.Frame(self.input_frame)
        self.execute_button = ttk.Button(
            self.buttons_frame,
            text="Execute",
            command=self._on_execute_command
        )

        # Voice button with Byte Smart support
        voice_text = "🎤 Byte Smart" if self.has_byte_smart else "🎤 Voice"
        self.voice_button = ttk.Button(
            self.buttons_frame,
            text=voice_text,
            command=self._toggle_voice_listening
        )

        self.clear_button = ttk.Button(
            self.buttons_frame,
            text="Clear",
            command=self._clear_input
        )

        # Macro buttons frame
        self.macro_frame = ttk.LabelFrame(self.main_frame, text="Macro Recording", padding="5")

        self.record_macro_button = ttk.Button(
            self.macro_frame,
            text="⏺️ Record Macro",
            command=self._start_macro_recording
        )

        self.stop_macro_button = ttk.Button(
            self.macro_frame,
            text="⏹️ Stop Recording",
            command=self._stop_macro_recording,
            state=tk.DISABLED
        )

        self.play_macro_button = ttk.Button(
            self.macro_frame,
            text="▶️ Play Macro",
            command=self._play_macro
        )

        self.macro_list_button = ttk.Button(
            self.macro_frame,
            text="📋 Macro List",
            command=self._show_macro_list
        )

        # Macro status label
        self.macro_status_label = ttk.Label(
            self.macro_frame,
            text="Ready to record",
            foreground="green"
        )
        
        # Output frame
        self.output_frame = ttk.LabelFrame(self.main_frame, text="Output & Logs", padding="5")
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(
            self.output_frame, 
            height=15, 
            font=("Consolas", 10),
            state=tk.DISABLED
        )
        
        # Control frame
        self.control_frame = ttk.Frame(self.main_frame)
        
        # Settings button
        self.settings_button = ttk.Button(
            self.control_frame, 
            text="Settings", 
            command=self._show_settings
        )
        
        # History button
        self.history_button = ttk.Button(
            self.control_frame, 
            text="History", 
            command=self._show_history
        )
        
        # Stop button
        self.stop_button = ttk.Button(
            self.control_frame, 
            text="Stop", 
            command=self._stop_current_task,
            state=tk.DISABLED
        )
    
    def _setup_layout(self):
        """Setup widget layout."""
        # Main frame
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(2, weight=1)  # Output frame gets extra space
        
        # Title
        self.title_label.grid(row=0, column=0, pady=(0, 10))
        
        # Status frame
        self.status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        self.status_indicator.grid(row=0, column=1, padx=(10, 0))
        
        # Input frame
        self.input_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.input_frame.columnconfigure(0, weight=1)
        
        # Text input
        self.text_input.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Buttons frame
        self.buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.execute_button.grid(row=0, column=0, padx=(0, 5))
        self.voice_button.grid(row=0, column=1, padx=(0, 5))
        self.clear_button.grid(row=0, column=2)

        # Macro frame
        self.macro_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        self.record_macro_button.grid(row=0, column=0, padx=(0, 5))
        self.stop_macro_button.grid(row=0, column=1, padx=(0, 5))
        self.play_macro_button.grid(row=0, column=2, padx=(0, 5))
        self.macro_list_button.grid(row=0, column=3, padx=(0, 5))
        self.macro_status_label.grid(row=1, column=0, columnspan=4, pady=(5, 0))

        # Output frame
        self.output_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 10))
        self.output_frame.columnconfigure(0, weight=1)
        self.output_frame.rowconfigure(0, weight=1)

        # Output text
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Control frame
        self.control_frame.grid(row=5, column=0, sticky=(tk.W, tk.E))
        self.settings_button.grid(row=0, column=0, padx=(0, 5))
        self.history_button.grid(row=0, column=1, padx=(0, 5))
        self.stop_button.grid(row=0, column=2)
    
    def _setup_bindings(self):
        """Setup event bindings."""
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_logging_display(self):
        """Setup logging to display in the GUI."""
        # Create a custom handler to display logs in the GUI
        class GUILogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
            
            def emit(self, record):
                msg = self.format(record)
                def append():
                    self.text_widget.config(state=tk.NORMAL)
                    self.text_widget.insert(tk.END, msg + '\n')
                    self.text_widget.see(tk.END)
                    self.text_widget.config(state=tk.DISABLED)
                
                # Schedule the GUI update in the main thread
                self.text_widget.after(0, append)
        
        # Add the handler to the root logger
        gui_handler = GUILogHandler(self.output_text)
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(gui_handler)
        logging.getLogger().setLevel(logging.INFO)
    
    def _on_text_command(self, event=None):
        """Handle text command input."""
        self._on_execute_command()
    
    def _on_execute_command(self):
        """Execute the command from text input."""
        command_text = self.text_input.get().strip()
        if not command_text:
            return
        
        self._log_message(f"Executing command: {command_text}")
        
        # Execute in separate thread to avoid blocking GUI
        threading.Thread(
            target=self._execute_command_thread,
            args=(command_text,),
            daemon=True
        ).start()
    
    def _execute_command_thread(self, command_text: str):
        """Execute command in separate thread with Smart Byte features."""
        try:
            # Update status
            self._update_status("Processing...", "orange")
            self._set_buttons_state(False)

            # Parse the command with AI
            parsed_command = self.nlp_processor.parse_command(command_text)
            self._log_message(f"🧠 Parsed: {parsed_command.action.value} on {parsed_command.application.value}")

            if parsed_command.confidence < 0.3:
                self._log_message("⚠️  Warning: Low confidence in command understanding")
            elif parsed_command.confidence > 0.8:
                self._log_message(f"✨ High confidence: {parsed_command.confidence:.0%}")

            # Handle OPEN commands with Smart App Opener
            # Skip MACRO commands so they are handled by the registered handler
            is_macro = parsed_command.application == ApplicationType.MACRO
            if not is_macro and parsed_command.target:
                 if "macro" in parsed_command.target.lower():
                     is_macro = True

            if parsed_command.action.value.lower() == "open" and self.has_smart_opener and not is_macro:
                app_name = parsed_command.target or parsed_command.application.value
                if app_name and app_name.lower() != "unknown":
                    self._log_message(f"🔍 Smart opening: {app_name}")
                    result_dict = self.smart_opener.open_app_smart(app_name)

                    if result_dict['status'] == 'completed':
                        self._log_message(f"✅ Success: {result_dict['message']}")
                        self._update_status("Ready", "green")

                        # Update context memory
                        if self.has_context_memory:
                            self.context_memory.add_action('open', {'app': app_name})

                        self._set_buttons_state(True)
                        return
                    elif result_dict['status'] == 'cancelled':
                        self._log_message("❌ Cancelled by user")
                        self._update_status("Ready", "green")
                        self._set_buttons_state(True)
                        return

            # Execute the command normally
            result = self.task_engine.execute_command(parsed_command)

            # Display result
            if result.status == TaskStatus.COMPLETED:
                self._log_message(f"✅ Success: {result.message}")
                self._update_status("Ready", "green")

                # Update context memory
                if self.has_context_memory:
                    self.context_memory.add_action(parsed_command.action.value,
                                                   {'command': command_text})
            else:
                self._log_message(f"❌ Failed: {result.message}")
                self._update_status("Error", "red")

        except Exception as e:
            self._log_message(f"❌ Error: {str(e)}")
            self._update_status("Error", "red")

        finally:
            self._set_buttons_state(True)
    
    def _toggle_voice_listening(self):
        """Toggle JARVIS voice mode on/off."""
        if not self.is_listening:
            self._start_jarvis_mode()
        else:
            self._stop_jarvis_mode()

    def _start_jarvis_mode(self):
        """Start JARVIS conversational mode."""
        try:
            self.is_listening = True
            self.byte_smart_mode = True  # Reusing this flag for JARVIS
            
            print(f"DEBUG: smart_opener available? {self.has_smart_opener}")
            if self.has_smart_opener:
                print(f"DEBUG: smart_opener instance: {self.smart_opener}")
            else:
                print("DEBUG: smart_opener is None")

            # Update UI
            self.voice_button.config(text="🔴 Stop JARVIS")
            self._update_status("JARVIS Active", "blue")

            # Show Overlay
            if not self.overlay:
                self.overlay = JarvisOverlay(master=self.root, on_interrupt=self._stop_jarvis_mode)
                self.overlay.update_status("JARVIS Active", "#00FFFF")

            import random
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from jarvis import JarvisPersonality

            # Initial greeting
            greeting = random.choice(JarvisPersonality.GREETINGS)
            self._log_message(f"🤖 JARVIS: {greeting}")
            self.voice_processor.speak(greeting)
            
            # Start JARVIS loop in separate thread
            threading.Thread(
                target=self._jarvis_loop,
                daemon=True
            ).start()

        except Exception as e:
            self._log_message(f"❌ Error starting JARVIS: {str(e)}")
            self.is_listening = False
            self.voice_button.config(text="🎤 JARVIS")

    def _stop_jarvis_mode(self):
        """Stop JARVIS mode."""
        try:
            self.is_listening = False
            self.byte_smart_mode = False

            # Update UI
            self.voice_button.config(text="🎤 JARVIS")
            self._update_status("Ready", "green")
            self._log_message("😴 JARVIS stopped")

            # Close Overlay
            if self.overlay:
                self.overlay.close()
                self.overlay = None

            # Say goodbye
            self.voice_processor.speak("Goodbye, Lucky!")

        except Exception as e:
            self._log_message(f"❌ Error stopping JARVIS: {str(e)}")
    
    def _jarvis_loop(self):
        """Main JARVIS conversation loop (runs in separate thread)."""
        import random
        import time
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from jarvis import JarvisPersonality, execute_jarvis_command, is_wake_word, is_sleep_command, is_exit_command, is_positive_response, is_negative_response

        task_count = 0

        try:
            while self.byte_smart_mode and self.is_listening:
                # Log listening status
                self.root.after(0, lambda: self._log_message("🎤 Listening... (say 'JARVIS' to start)"))
                if self.overlay:
                    self.overlay.update_status("Listening...", "#00FF00")
                    self.overlay.update_text("Say 'JARVIS' to start...")

                # Listen for wake word or command
                command = self._listen_for_byte_input()

                if not command or not self.byte_smart_mode:
                    continue

                cmd_lower = command.lower().strip()

                # Check for exit
                if is_exit_command(cmd_lower):
                    self.root.after(0, lambda: self._log_message("🤖 JARVIS: Goodbye, Lucky!"))
                    self.voice_processor.speak("Goodbye, Lucky!")
                    self.root.after(0, self._stop_jarvis_mode)
                    break

                # Check for sleep
                if is_sleep_command(cmd_lower):
                    sleep_msg = random.choice(JarvisPersonality.SLEEP_MESSAGES)
                    self.root.after(0, lambda msg=sleep_msg: self._log_message(f"😴 JARVIS: {msg}"))
                    self.voice_processor.speak(sleep_msg)
                    self.root.after(0, self._stop_jarvis_mode)
                    break

                # Check for wake word
                if is_wake_word(cmd_lower):
                    # Check if there's a command after the wake word
                    # e.g., "Jarvis open notepad" -> cmd_lower="jarvis open notepad"
                    # We need to strip the wake word and see if anything remains
                    
                    # Get the wake word used
                    wake_words = ['jarvis', 'hello jarvis', 'hey jarvis', 'hi jarvis']
                    used_wake_word = next((w for w in wake_words if cmd_lower.startswith(w)), None)
                    
                    remaining_command = ""
                    if used_wake_word:
                        remaining_command = cmd_lower[len(used_wake_word):].strip()
                    
                    if remaining_command:
                        # User said "Jarvis [command]", so execute immediately
                        command = remaining_command
                        cmd_lower = command.lower()
                        self._log_message(f"⚡ Fast command detected: {command}")
                    else:
                        # User just said "Jarvis", so greet and wait
                        greeting = random.choice(JarvisPersonality.GREETINGS)
                        self.root.after(0, lambda msg=greeting: self._log_message(f"🤖 JARVIS: {msg}"))
                        self.voice_processor.speak(greeting)

                        if self.overlay:
                            self.overlay.update_status("Listening for command...", "#00FFFF")
                            self.overlay.update_text(greeting)

                        # Listen for actual command
                        self.root.after(0, lambda: self._log_message("🎤 Listening for your command..."))
                        command = self._listen_for_byte_input()

                        if not command or not self.byte_smart_mode:
                            continue

                        cmd_lower = command.lower().strip()

                # Execute command if not sleep/exit
                if not is_sleep_command(cmd_lower) and not is_exit_command(cmd_lower):
                    # Execute command using JARVIS logic
                    self.root.after(0, lambda msg=command: self._log_message(f"📝 Command: {msg}"))
                    
                    if self.overlay:
                        self.overlay.update_status("Processing...", "#FFA500")
                        self.overlay.update_text(f"Command: {command}")
                    
                    intelligent = self._get_intelligent_assistant()

                    success = execute_jarvis_command(
                        command, 
                        self.nlp_processor, 
                        self.task_engine, 
                        self.voice_processor, 
                        intelligent, 
                        self.context_memory if self.has_context_memory else None, 
                        self.smart_opener if self.has_smart_opener else None
                    )

                    if success:
                        self.root.after(0, lambda: self._log_message("✅ Task completed successfully"))
                        if self.overlay:
                            self.overlay.update_status("Success", "#00FF00")
                    else:
                        self.root.after(0, lambda: self._log_message("❌ Task failed"))
                        if self.overlay:
                            self.overlay.update_status("Failed", "#FF0000")

                    # Wait for execution
                    time.sleep(1)

                    # Ask for feedback
                    feedback_q = random.choice(JarvisPersonality.FEEDBACK_QUESTIONS)
                    self.root.after(0, lambda msg=feedback_q: self._log_message(f"🤖 JARVIS: {msg}"))
                    self.voice_processor.speak(feedback_q)

                    if self.overlay:
                        self.overlay.update_status("Waiting for response...", "#00FFFF")
                        self.overlay.update_text(feedback_q)

                    # Listen for response
                    self.root.after(0, lambda: self._log_message("🎤 Listening for response..."))
                    response = self._listen_for_byte_input(timeout=15)

                    if response:
                        resp_lower = response.lower().strip()

                        if is_sleep_command(resp_lower) or is_negative_response(resp_lower):
                            sleep_msg = random.choice(JarvisPersonality.SLEEP_MESSAGES)
                            self.root.after(0, lambda msg=sleep_msg: self._log_message(f"😴 JARVIS: {msg}"))
                            self.voice_processor.speak(sleep_msg)
                            self.root.after(0, self._stop_jarvis_mode)
                            break
                        elif is_wake_word(resp_lower) or is_positive_response(resp_lower):
                            # Continue loop for new command
                            self.root.after(0, lambda: self._log_message("🤖 JARVIS: Standing by."))
                            continue
                        else:
                            # User said a new command directly - execute it!
                            self.root.after(0, lambda msg=response: self._log_message(f"📝 New command: {msg}"))
                            
                            if self.overlay:
                                self.overlay.update_status("Processing...", "#FFA500")
                                self.overlay.update_text(f"Command: {response}")
                            
                            # Execute the new command
                            intelligent = self._get_intelligent_assistant()

                            success = execute_jarvis_command(
                                response, 
                                self.nlp_processor, 
                                self.task_engine, 
                                self.voice_processor, 
                                intelligent, 
                                self.context_memory if self.has_context_memory else None, 
                                self.smart_opener if self.has_smart_opener else None
                            )

                            if success:
                                self.root.after(0, lambda: self._log_message("✅ Task completed successfully"))
                                if self.overlay:
                                    self.overlay.update_status("Success", "#00FF00")
                            else:
                                self.root.after(0, lambda: self._log_message("❌ Task failed"))
                                if self.overlay:
                                    self.overlay.update_status("Failed", "#FF0000")
                            
                            # Wait a bit before continuing
                            time.sleep(1)
                            # Loop back to ask for feedback again
                            continue

                    task_count += 1

        except Exception as e:
            self.root.after(0, lambda err=str(e): self._log_message(f"❌ Error in JARVIS loop: {err}"))
            self.root.after(0, self._stop_jarvis_mode)

    def _listen_for_byte_input(self, timeout=30):
        """Listen for voice input (blocking)."""
        try:
            # Define callback for overlay updates
            def status_callback(msg):
                if self.overlay:
                    # Determine color based on message content
                    color = "#00FFFF"  # Default cyan
                    if "Listening" in msg:
                        color = "#00FF00"  # Green
                    elif "Processing" in msg:
                        color = "#FFA500"  # Orange
                    elif "Heard" in msg:
                        color = "#FFFFFF"  # White
                    elif "No speech" in msg:
                        color = "#FF0000"  # Red
                    
                    self.overlay.update_status(msg, color)
                    # If it's the "Heard" message, also update the text area
                    if "Heard:" in msg:
                        text = msg.replace("Heard:", "").strip()
                        self.overlay.update_text(text)

            # Use listen_once for IndianEnglishVoiceProcessor
            if hasattr(self.voice_processor, 'listen_once'):
                return self.voice_processor.listen_once(timeout=timeout, status_callback=status_callback)
            # Fallback to listen for basic VoiceProcessor
            elif hasattr(self.voice_processor, 'listen'):
                return self.voice_processor.listen(timeout=timeout)
            else:
                self.root.after(0, lambda: self._log_message("⚠️  Voice processor has no listen method"))
                return None
        except Exception as e:
            self.root.after(0, lambda err=str(e): self._log_message(f"⚠️  Listening error: {err}"))
            return None

    def _clear_input(self):
        """Clear the input field."""
        self.text_input.delete(0, tk.END)
    
    def _stop_current_task(self):
        """Stop the currently executing task."""
        if self.task_engine.is_busy():
            self.task_engine.cancel_current_task()
            self._log_message("Task cancelled by user")
            self._update_status("Cancelled", "orange")
    
    def _show_settings(self):
        """Show settings dialog."""
        messagebox.showinfo("Settings", "Settings dialog not implemented yet")
    
    def _show_history(self):
        """Show command history."""
        history = self.task_engine.get_task_history()
        if not history:
            messagebox.showinfo("History", "No command history available")
            return
        
        # Create history window
        history_window = tk.Toplevel(self.root)
        history_window.title("Command History")
        history_window.geometry("600x400")
        
        # History text
        history_text = scrolledtext.ScrolledText(history_window, font=("Consolas", 10))
        history_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Display history
        for i, entry in enumerate(history[-20:], 1):  # Show last 20 entries
            command = entry['command']
            result = entry['result']
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry['timestamp']))
            
            history_text.insert(tk.END, f"{i}. [{timestamp}] {command.raw_text}\n")
            history_text.insert(tk.END, f"   Result: {result.message}\n")
            history_text.insert(tk.END, f"   Status: {result.status.value}\n\n")
    
    def _log_message(self, message: str):
        """Log a message to the output area."""
        self.logger.info(message)
    
    def _get_intelligent_assistant(self):
        """Lazily create (once) the assistant used for follow-up questions."""
        if getattr(self, '_intelligent', None) is None:
            try:
                from ..core.intelligent_assistant import IntelligentAssistant
                self._intelligent = IntelligentAssistant(self.voice_processor, self.nlp_processor)
            except Exception as e:
                self.logger.warning(f"Intelligent assistant unavailable: {e}")
                self._intelligent = None
        return self._intelligent

    def _on_tk_thread(self, func, *args) -> bool:
        """Re-schedule func on the Tk thread when called from a worker thread."""
        if threading.current_thread() is threading.main_thread():
            return False
        self.root.after(0, lambda: func(*args))
        return True

    def _update_status(self, status: str, color: str = "green"):
        """Update the status display."""
        if self._on_tk_thread(self._update_status, status, color):
            return
        self.status_label.config(text=f"Status: {status}")
        self.status_indicator.delete("all")
        self.status_indicator.create_oval(2, 2, 18, 18, fill=color, outline="dark" + color)
    
    def _set_buttons_state(self, enabled: bool):
        """Enable/disable buttons."""
        if self._on_tk_thread(self._set_buttons_state, enabled):
            return
        state = tk.NORMAL if enabled else tk.DISABLED
        self.execute_button.config(state=state)
        self.stop_button.config(state=tk.DISABLED if enabled else tk.NORMAL)
    
    def _start_macro_recording(self):
        """Start recording a macro."""
        if not self.has_macro_support:
            messagebox.showerror("Error", "Macro support not available. Install pynput.")
            return

        if self.is_recording_macro:
            return

        # Generate temporary name
        import time
        macro_name = f"Macro_{int(time.time())}"

        try:
            from ..core.macro_recorder import MacroRecorder

            # Create macro recorder
            self.macro_recorder = MacroRecorder(
                name=macro_name,
                save_dir=self.macro_save_dir
            )

            # Start recording
            self.macro_recorder.start()
            self.is_recording_macro = True

            # Update UI
            self.record_macro_button.config(state=tk.DISABLED)
            self.stop_macro_button.config(state=tk.NORMAL)
            self.macro_status_label.config(text=f"Recording: {macro_name}", foreground="red")

            self._log_message(f"⏺️  Started recording macro: {macro_name}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start recording: {str(e)}")
            self._log_message(f"❌ Error starting macro recording: {str(e)}")

    def _stop_macro_recording(self):
        """Stop recording the current macro."""
        if not self.is_recording_macro or not self.macro_recorder:
            return

        try:
            # Stop recording
            self.macro_recorder.stop()
            
            # Open Editor for trimming
            try:
                from .macro_editor import MacroEditor
                
                # Define callback for successful save
                def on_save(path):
                    self._log_message(f"⏹️  Stopped recording. Saved to: {path}")
                    messagebox.showinfo("Success", f"Macro saved to:\n{path}")
                    self._load_macro_shortcuts() # Reload shortcuts
                    # The cleanup will happen after wait_window returns
                
                # Create and wait for editor
                editor = MacroEditor(self.root, self.macro_recorder, on_save)
                self.root.wait_window(editor.window)
                
            except ImportError:
                # Fallback if editor not found (shouldn't happen)
                saved_path = self.macro_recorder.save()
                self._log_message(f"⏹️  Stopped recording. Saved to: {saved_path}")
                messagebox.showinfo("Success", f"Macro saved to:\n{saved_path}")

            # Cleanup (whether saved or cancelled)
            self.is_recording_macro = False
            self.macro_recorder = None

            # Update UI
            self.record_macro_button.config(state=tk.NORMAL)
            self.stop_macro_button.config(state=tk.DISABLED)
            self.macro_status_label.config(text="Ready to record", foreground="green")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop recording: {str(e)}")
            self._log_message(f"❌ Error stopping macro recording: {str(e)}")
            
            # Force cleanup
            self.is_recording_macro = False
            self.macro_recorder = None
            self.record_macro_button.config(state=tk.NORMAL)
            self.stop_macro_button.config(state=tk.DISABLED)

    def _play_macro(self):
        """Play a recorded macro."""
        if not self.has_macro_support:
            messagebox.showerror("Error", "Macro support not available. Install pynput.")
            return

        # Get list of macros
        import os
        from pathlib import Path

        macro_dir = Path(self.macro_save_dir)
        if not macro_dir.exists():
            messagebox.showinfo("No Macros", "No macros found. Record one first!")
            return

        macro_files = list(macro_dir.glob("*.json"))
        if not macro_files:
            messagebox.showinfo("No Macros", "No macros found. Record one first!")
            return

        # Show selection dialog
        macro_names = [f.stem for f in macro_files]

        # Create selection window
        selection_window = tk.Toplevel(self.root)
        selection_window.title("Select Macro")
        selection_window.geometry("400x300")

        ttk.Label(selection_window, text="Select a macro to play:").pack(pady=10)

        listbox = tk.Listbox(selection_window)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for name in macro_names:
            listbox.insert(tk.END, name)

        def play_selected():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a macro")
                return

            selected_name = macro_names[selection[0]]
            selected_file = macro_dir / f"{selected_name}.json"

            selection_window.destroy()

            # Play the macro
            try:
                from ..core.macro_recorder import MacroRecorder

                self._log_message(f"▶️  Playing macro: {selected_name}")
                self._update_status("Playing macro...", "blue")
                # Play in separate thread
                def play_thread():
                    try:
                        MacroRecorder.play_file(str(selected_file))
                        self._log_message(f"✅ Finished playing macro: {selected_name}")
                        self._update_status("Ready", "green")
                    except Exception as e:
                        self._log_message(f"❌ Error playing macro: {str(e)}")
                        self._update_status("Error", "red")

                threading.Thread(target=play_thread, daemon=True).start()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to play macro: {str(e)}")
                self._log_message(f"❌ Error playing macro: {str(e)}")

        ttk.Button(selection_window, text="Play", command=play_selected).pack(pady=5)
        ttk.Button(selection_window, text="Cancel", command=selection_window.destroy).pack(pady=5)

    def _show_macro_list(self):
        """Show list of recorded macros with options to Play and Trim."""
        import os
        from pathlib import Path
        import json

        macro_dir = Path(self.macro_save_dir)
        if not macro_dir.exists():
            messagebox.showinfo("No Macros", "No macros found. Record one first!")
            return

        macro_files = list(macro_dir.glob("*.json"))
        if not macro_files:
            messagebox.showinfo("No Macros", "No macros found. Record one first!")
            return

        # Create list window
        list_window = tk.Toplevel(self.root)
        list_window.title("Manage Macros")
        list_window.geometry("500x400")

        # Listbox
        list_frame = ttk.Frame(list_window, padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(list_frame, text="Select a macro:").pack(anchor=tk.W)
        
        listbox = tk.Listbox(list_frame, font=("Arial", 10))
        listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Populate list
        macro_map = {}
        for f in macro_files:
            listbox.insert(tk.END, f.stem)
            macro_map[f.stem] = f

        # Buttons
        btn_frame = ttk.Frame(list_window, padding="10")
        btn_frame.pack(fill=tk.X)

        def get_selected():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Selection", "Please select a macro first.")
                return None
            name = listbox.get(selection[0])
            return macro_map[name]

        def play_macro():
            path = get_selected()
            if not path: return
            
            list_window.destroy()
            
            try:
                from ..core.macro_recorder import MacroRecorder
                self._log_message(f"▶️  Playing macro: {path.stem}")
                self._update_status("Playing macro...", "blue")
                
                def play_thread():
                    try:
                        MacroRecorder.play_file(str(path))
                        self._log_message(f"✅ Finished playing macro: {path.stem}")
                        self._update_status("Ready", "green")
                    except Exception as e:
                        self._log_message(f"❌ Error playing macro: {str(e)}")
                        self._update_status("Error", "red")
                
                threading.Thread(target=play_thread, daemon=True).start()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to play: {e}")

        def trim_macro():
            path = get_selected()
            if not path: return
            
            try:
                # Load the macro to create a recorder instance (needed for editor)
                from ..core.macro_recorder import MacroRecorder, MacroEvent
                
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Create a dummy recorder with loaded events
                recorder = MacroRecorder(data['name'], str(path.parent))
                recorder._events = [MacroEvent(**e) for e in data.get('events', [])]
                recorder._start_time = data.get('created_at', 0)
                
                # Define callback
                def on_save(new_path):
                    self._log_message(f"✂️  Trimmed macro saved: {new_path}")
                    messagebox.showinfo("Success", f"Trimmed macro saved to:\n{new_path}")
                    list_window.destroy()
                    self._show_macro_list() # Refresh list
                
                # Open editor
                from .macro_editor import MacroEditor
                editor = MacroEditor(self.root, recorder, on_save)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open editor: {e}")

        def delete_macro():
            path = get_selected()
            if not path: return
            
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{path.stem}'?"):
                try:
                    os.remove(path)
                    listbox.delete(listbox.curselection())
                    self._log_message(f"🗑️  Deleted macro: {path.stem}")
                    self._load_macro_shortcuts() # Reload shortcuts
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete: {e}")

        ttk.Button(btn_frame, text="▶️ Play", command=play_macro).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✂️ Trim/Edit", command=trim_macro).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Delete", command=delete_macro).pack(side=tk.LEFT, padx=5)

    def _setup_global_shortcuts(self):
        """Setup global shortcut listener for macros."""
        if not self.has_macro_support:
            return

        self.macro_shortcuts = {}
        self._load_macro_shortcuts()

        try:
            from pynput import keyboard
            from ..core.macro_recorder import MacroRecorder

            # Store currently pressed keys
            self.pressed_keys = set()

            def on_press(key):
                if self.is_recording_macro:
                    return # Don't trigger while recording
                
                try:
                    # Add key to pressed set
                    self.pressed_keys.add(key)
                    
                    # Check for matches
                    # We need to construct the current combo string
                    # Sort modifiers first
                    modifiers = []
                    non_modifiers = []
                    
                    for k in self.pressed_keys:
                        k_str = str(k)
                        if any(m in k_str for m in ['ctrl', 'shift', 'alt', 'cmd', 'win']):
                            modifiers.append(k)
                        else:
                            non_modifiers.append(k)
                    
                    # If we have a non-modifier key, check for combo
                    if non_modifiers:
                        # Construct combo string
                        # Helper to clean key name (duplicate logic from editor, should be shared but inline for now)
                        def clean_key(k):
                            s = str(k).replace("'", "")
                            if s.startswith("Key."): s = s.replace("Key.", "")
                            replacements = {
                                "ctrl_l": "Ctrl", "ctrl_r": "Ctrl",
                                "alt_l": "Alt", "alt_r": "Alt",
                                "shift": "Shift", "shift_r": "Shift",
                                "cmd": "Win", "cmd_r": "Win",
                                "caps_lock": "CapsLock", "print_screen": "PrtSc",
                                "delete": "Del", "insert": "Ins",
                                "page_up": "PgUp", "page_down": "PgDn"
                            }
                            return replacements.get(s, s.title())

                        # Sort modifiers
                        modifiers.sort(key=lambda k: str(k))
                        
                        combo_parts = [clean_key(m) for m in modifiers]
                        # Use the last pressed non-modifier as the trigger? 
                        # Or check all combinations?
                        # Usually hotkey is Modifiers + Key
                        # We'll take the most recently pressed non-modifier
                        trigger_key = non_modifiers[-1]
                        combo_parts.append(clean_key(trigger_key))
                        
                        current_combo = "+".join(combo_parts)
                        
                        # Check exact match
                        if current_combo in self.macro_shortcuts:
                            macro_path = self.macro_shortcuts[current_combo]
                            self.root.after(0, lambda: self._play_macro_by_path(macro_path))
                            
                except Exception as e:
                    pass

            def on_release(key):
                try:
                    if key in self.pressed_keys:
                        self.pressed_keys.remove(key)
                except:
                    pass

            self.shortcut_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            self.shortcut_listener.start()
            
        except Exception as e:
            self._log_message(f"⚠️ Failed to start shortcut listener: {e}")

    def _load_macro_shortcuts(self):
        """Load shortcuts from saved macros."""
        import json
        from pathlib import Path
        
        self.macro_shortcuts = {}
        macro_dir = Path(self.macro_save_dir)
        
        if not macro_dir.exists():
            return

        try:
            for f in macro_dir.glob("*.json"):
                try:
                    with open(f, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        shortcut = data.get('shortcut_key')
                        if shortcut:
                            self.macro_shortcuts[shortcut] = f
                except Exception:
                    continue
        except Exception as e:
            self._log_message(f"⚠️ Error loading shortcuts: {e}")

    def _play_macro_by_path(self, path):
        """Play a macro given its path."""
        try:
            from ..core.macro_recorder import MacroRecorder
            
            # Check if already playing? (Optional)
            
            self._log_message(f"⚡ Shortcut triggered: {path.stem}")
            self._update_status("Playing macro...", "blue")
            
            def play_thread():
                try:
                    MacroRecorder.play_file(str(path))
                    self._log_message(f"✅ Finished playing macro: {path.stem}")
                    self._update_status("Ready", "green")
                except Exception as e:
                    self._log_message(f"❌ Error playing macro: {str(e)}")
                    self._update_status("Error", "red")
            
            threading.Thread(target=play_thread, daemon=True).start()
            
        except Exception as e:
            self._log_message(f"❌ Error playing macro: {str(e)}")

    def _on_closing(self):
        """Handle window closing."""
        # Stop macro recording if active
        if self.is_recording_macro:
            self._stop_macro_recording()

        if self.is_listening:
            self._stop_jarvis_mode()

        # Close any open browser instances
        try:
            for handler in [self.task_engine.app_handlers.get(app) for app in self.task_engine.app_handlers]:
                if hasattr(handler, 'close_browser'):
                    handler.close_browser()
        except:
            pass

        self.root.destroy()

    def run(self):
        """Start the GUI application."""
        welcome_msg = "🤖 AI-Powered Screen Agent - Byte Smart Started!"
        self._log_message(welcome_msg)

        if self.has_byte_smart:
            self._log_message("✅ Byte Smart voice mode enabled")

        if self.has_smart_opener:
            self._log_message("✅ Smart App Opener enabled (taskbar → installed → browser)")

        if self.has_context_memory:
            self._log_message("✅ Context memory enabled")

        if self.has_macro_support:
            self._log_message("✅ Macro recording enabled")

        self._log_message("\n💡 You can type commands or use voice input")
        self._log_message("💡 Examples:")
        self._log_message("   - 'open chatgpt' (smart opens)")
        self._log_message("   - 'Create a new folder named auto_work in VSCode'")
        self._log_message("   - Record macros for repetitive tasks")

        self.root.mainloop()
