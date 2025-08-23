"""
Main GUI window for the AI-Powered Screen Agent.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import logging
from typing import Optional
import time

from ..core.screen_agent import ScreenAgent
from ..core.voice_processor import VoiceProcessor
from ..core.nlp_processor import NLPProcessor, ParsedCommand
from ..automation.task_engine import TaskEngine, TaskResult, TaskStatus
from ..automation.handlers import VSCodeHandler, GmailHandler, LinkedInHandler, BrowserHandler

class MainWindow:
    """Main application window."""
    
    def __init__(self):
        """Initialize the main window."""
        self.root = tk.Tk()
        self.root.title("AI-Powered Screen Agent")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Initialize core components
        self.screen_agent = ScreenAgent()
        self.voice_processor = VoiceProcessor()
        self.nlp_processor = NLPProcessor()
        self.task_engine = TaskEngine(self.screen_agent)
        
        # Initialize handlers
        self._setup_handlers()
        
        # GUI state
        self.is_listening = False
        self.current_task = None
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Create GUI elements
        self._create_widgets()
        self._setup_layout()
        self._setup_bindings()
        
        # Start the application
        self._setup_logging_display()
    
    def _setup_handlers(self):
        """Setup application-specific handlers."""
        from ..core.nlp_processor import ApplicationType
        
        # Register handlers with the task engine
        vscode_handler = VSCodeHandler(self.screen_agent)
        gmail_handler = GmailHandler(self.screen_agent)
        linkedin_handler = LinkedInHandler(self.screen_agent)
        browser_handler = BrowserHandler(self.screen_agent)
        
        self.task_engine.register_app_handler(ApplicationType.VSCODE, vscode_handler.handle_command)
        self.task_engine.register_app_handler(ApplicationType.GMAIL, gmail_handler.handle_command)
        self.task_engine.register_app_handler(ApplicationType.LINKEDIN, linkedin_handler.handle_command)
        self.task_engine.register_app_handler(ApplicationType.CHROME, browser_handler.handle_command)
    
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
        self.voice_button = ttk.Button(
            self.buttons_frame, 
            text="🎤 Voice", 
            command=self._toggle_voice_listening
        )
        self.clear_button = ttk.Button(
            self.buttons_frame, 
            text="Clear", 
            command=self._clear_input
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
        
        # Output frame
        self.output_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        self.output_frame.columnconfigure(0, weight=1)
        self.output_frame.rowconfigure(0, weight=1)
        
        # Output text
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Control frame
        self.control_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
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
        """Execute command in separate thread."""
        try:
            # Update status
            self._update_status("Processing...", "orange")
            self._set_buttons_state(False)
            
            # Parse the command
            parsed_command = self.nlp_processor.parse_command(command_text)
            self._log_message(f"Parsed: {parsed_command.action.value} on {parsed_command.application.value}")
            
            if parsed_command.confidence < 0.3:
                self._log_message("Warning: Low confidence in command understanding")
            
            # Execute the command
            result = self.task_engine.execute_command(parsed_command)
            
            # Display result
            if result.status == TaskStatus.COMPLETED:
                self._log_message(f"✅ Success: {result.message}")
                self._update_status("Ready", "green")
            else:
                self._log_message(f"❌ Failed: {result.message}")
                self._update_status("Error", "red")
            
        except Exception as e:
            self._log_message(f"❌ Error: {str(e)}")
            self._update_status("Error", "red")
        
        finally:
            self._set_buttons_state(True)
    
    def _toggle_voice_listening(self):
        """Toggle voice listening on/off."""
        if not self.is_listening:
            self._start_voice_listening()
        else:
            self._stop_voice_listening()
    
    def _start_voice_listening(self):
        """Start voice listening."""
        try:
            self.is_listening = True
            self.voice_button.config(text="🔴 Stop")
            self._update_status("Listening...", "blue")
            self._log_message("Started voice listening...")
            
            # Start continuous listening
            self.voice_processor.start_continuous_listening(self._on_voice_command)
            
        except Exception as e:
            self._log_message(f"Error starting voice listening: {str(e)}")
            self.is_listening = False
            self.voice_button.config(text="🎤 Voice")
            self._update_status("Ready", "green")
    
    def _stop_voice_listening(self):
        """Stop voice listening."""
        self.is_listening = False
        self.voice_button.config(text="🎤 Voice")
        self._update_status("Ready", "green")
        self._log_message("Stopped voice listening")
        
        self.voice_processor.stop_continuous_listening()
    
    def _on_voice_command(self, command_text: str):
        """Handle voice command."""
        # Update GUI in main thread
        self.root.after(0, lambda: self._process_voice_command(command_text))
    
    def _process_voice_command(self, command_text: str):
        """Process voice command in main thread."""
        self.text_input.delete(0, tk.END)
        self.text_input.insert(0, command_text)
        self._log_message(f"Voice command: {command_text}")
        
        # Auto-execute voice commands
        self._on_execute_command()
    
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
    
    def _update_status(self, status: str, color: str = "green"):
        """Update the status display."""
        self.status_label.config(text=f"Status: {status}")
        self.status_indicator.delete("all")
        self.status_indicator.create_oval(2, 2, 18, 18, fill=color, outline="dark" + color)
    
    def _set_buttons_state(self, enabled: bool):
        """Enable/disable buttons."""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.execute_button.config(state=state)
        self.stop_button.config(state=tk.DISABLED if enabled else tk.NORMAL)
    
    def _on_closing(self):
        """Handle window closing."""
        if self.is_listening:
            self._stop_voice_listening()
        
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
        self._log_message("AI-Powered Screen Agent started")
        self._log_message("You can type commands or use voice input")
        self._log_message("Example: 'Create a new folder named auto_work in VSCode'")
        self.root.mainloop()
