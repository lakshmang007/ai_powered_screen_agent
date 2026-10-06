"""
Core task automation engine for executing parsed commands.
"""

import time
import logging
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    psutil = None

try:
    import pygetwindow as gw
    HAS_PYGETWINDOW = True
except ImportError:
    HAS_PYGETWINDOW = False
    gw = None

from ..core.screen_agent import ScreenAgent
from ..core.nlp_processor import ParsedCommand, ActionType, ApplicationType

class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    AMBIGUOUS = "ambiguous"

@dataclass
class TaskResult:
    """Result of task execution."""
    status: TaskStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0

class TaskEngine:
    """Core automation engine for executing tasks."""
    
    def __init__(self, screen_agent: ScreenAgent):
        """
        Initialize the Task Engine.
        
        Args:
            screen_agent: Screen agent for UI interactions
        """
        self.screen_agent = screen_agent
        self.logger = logging.getLogger(__name__)
        
        # Task execution state
        self.current_task = None
        self.task_history = []
        self.is_executing = False
        
        # Application handlers registry
        self.app_handlers = {}
        
        # Default timeouts and retries
        self.default_timeout = 30
        self.default_retries = 3
        self.retry_delay = 1.0

        # Lazily-created regex-only parser for multi-step plans
        self._step_parser = None
    
    def register_app_handler(self, app_type: ApplicationType, handler: Callable):
        """
        Register an application-specific handler.
        
        Args:
            app_type: Application type
            handler: Handler function
        """
        self.app_handlers[app_type] = handler
        self.logger.info(f"Registered handler for {app_type.value}")
    
    def execute_command(self, command: ParsedCommand) -> TaskResult:
        """
        Execute a parsed command.
        
        Args:
            command: Parsed command to execute
            
        Returns:
            TaskResult with execution status and details
        """
        start_time = time.time()
        self.current_task = command
        self.is_executing = True
        
        try:
            self.logger.info(f"Executing command: {command.action.value} on {command.application.value}")
            
            # Check if we have a specific handler for this application
            if command.application in self.app_handlers:
                result = self.app_handlers[command.application](command)
            else:
                # Use generic execution logic
                result = self._execute_generic_command(command)
            
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            # Add to history
            self.task_history.append({
                'command': command,
                'result': result,
                'timestamp': time.time()
            })
            
            self.logger.info(f"Command completed in {execution_time:.2f}s: {result.message}")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error executing command: {str(e)}",
                execution_time=execution_time
            )
            
            self.task_history.append({
                'command': command,
                'result': error_result,
                'timestamp': time.time()
            })
            
            self.logger.error(f"Command failed: {str(e)}")
            return error_result
            
        finally:
            self.is_executing = False
            self.current_task = None
    
    def _execute_generic_command(self, command: ParsedCommand) -> TaskResult:
        """Execute command using generic logic."""

        if command.action == ActionType.OPEN:
            return self._handle_open_action(command)
        elif command.action == ActionType.CREATE:
            return self._handle_create_action(command)
        elif command.action == ActionType.CLICK:
            return self._handle_click_action(command)
        elif command.action == ActionType.TYPE:
            return self._handle_type_action(command)
        elif command.action == ActionType.PRESS:
            return self._handle_press_action(command)
        elif command.action == ActionType.SEARCH:
            return self._handle_search_action(command)
        elif command.action == ActionType.SCROLL:
            return self._handle_scroll_action(command)
        elif command.action == ActionType.CLOSE:
            return self._handle_close_action(command)
        elif command.action == ActionType.MINIMIZE:
            return self._handle_minimize_action(command)
        elif command.action == ActionType.NAVIGATE:
            return self._handle_navigate_action(command)
        elif command.action in (ActionType.ERASE, ActionType.CLEAR, ActionType.DELETE):
            return self._handle_erase_action(command)
        elif command.action == ActionType.ERASE_AND_TYPE:
            command.parameters.setdefault('type_after', command.target)
            return self._handle_erase_action(command)
        elif command.action == ActionType.SELECT:
            return self._handle_select_action(command)
        elif command.action == ActionType.WAIT:
            return self._handle_wait_action(command)
        elif command.action == ActionType.MULTI_STEP:
            return self._handle_multi_step_action(command)
        elif command.action == ActionType.CHAT:
            return TaskResult(status=TaskStatus.COMPLETED,
                              message=command.target or "I'm here, Lucky. What should I do?",
                              data={'reply': True})
        else:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Unsupported action: {command.action.value}"
            )

    def _handle_navigate_action(self, command: ParsedCommand) -> TaskResult:
        """Open a URL (or a bare site name like 'youtube') in the default browser."""
        import re
        import webbrowser

        target = (command.target or '').strip()
        if not target:
            return TaskResult(status=TaskStatus.FAILED, message="No website specified")

        url = target
        if not re.match(r'^[a-z]+://', url, re.IGNORECASE):
            if ' ' in url:
                from urllib.parse import quote_plus
                url = f"https://www.google.com/search?q={quote_plus(url)}"
            else:
                if '.' not in url:
                    url = f"{url}.com"
                url = f"https://{url}"

        if webbrowser.open(url):
            return TaskResult(status=TaskStatus.COMPLETED, message=f"Opened {url}", data={'url': url})
        return TaskResult(status=TaskStatus.FAILED, message=f"Could not open browser for {url}")

    def _handle_erase_action(self, command: ParsedCommand) -> TaskResult:
        """Select everything in the focused field, delete it, optionally type replacement text."""
        if not (self.screen_agent.key_combination('ctrl', 'a') and self.screen_agent.press_key('delete')):
            return TaskResult(status=TaskStatus.FAILED, message="Failed to erase text")

        type_after = command.parameters.get('type_after')
        if type_after:
            time.sleep(0.2)
            if not self.screen_agent.type_text(type_after):
                return TaskResult(status=TaskStatus.FAILED, message="Erased text but failed to type replacement")
            return TaskResult(status=TaskStatus.COMPLETED, message=f"Replaced text with: '{type_after}'")

        return TaskResult(status=TaskStatus.COMPLETED, message="Erased text")

    def _handle_select_action(self, command: ParsedCommand) -> TaskResult:
        """Select all in the focused window."""
        if self.screen_agent.key_combination('ctrl', 'a'):
            return TaskResult(status=TaskStatus.COMPLETED, message="Selected all")
        return TaskResult(status=TaskStatus.FAILED, message="Failed to select all")

    def _handle_wait_action(self, command: ParsedCommand) -> TaskResult:
        """Pause between steps (capped so a misheard number can't hang the agent)."""
        import re
        seconds = command.parameters.get('seconds')
        if seconds is None:
            # The AI parser may put the duration in target ("5 seconds") instead
            match = re.search(r'\d+(?:\.\d+)?', f"{command.target or ''} {command.raw_text or ''}")
            seconds = float(match.group(0)) if match else 1.0
        seconds = min(float(seconds), 60.0)
        time.sleep(seconds)
        return TaskResult(status=TaskStatus.COMPLETED, message=f"Waited {seconds:g}s")

    def _handle_multi_step_action(self, command: ParsedCommand) -> TaskResult:
        """Run each step of a multi-step plan (e.g. from the AI parser) in order."""
        steps = command.parameters.get('steps') or []
        if not steps:
            return TaskResult(status=TaskStatus.FAILED, message="Multi-step command had no steps")

        # Steps are short ("press win", "type chatgpt"); the regex parser handles them
        # reliably and avoids one AI round-trip per step.
        if self._step_parser is None:
            from ..core.nlp_processor import NLPProcessor
            self._step_parser = NLPProcessor(use_ai=False)

        messages = []
        for i, step in enumerate(steps, 1):
            parsed = self._step_parser.parse_command(str(step))
            if parsed.action == ActionType.MULTI_STEP:
                return TaskResult(status=TaskStatus.FAILED, message=f"Step {i} is itself multi-step: {step}")

            if parsed.application in self.app_handlers:
                result = self.app_handlers[parsed.application](parsed)
            else:
                result = self._execute_generic_command(parsed)

            messages.append(f"{i}. {result.message}")
            if result.status != TaskStatus.COMPLETED:
                return TaskResult(
                    status=TaskStatus.FAILED,
                    message=f"Step {i}/{len(steps)} failed ({step}): {result.message}",
                    data={'completed_steps': i - 1}
                )
            time.sleep(0.5)

        return TaskResult(status=TaskStatus.COMPLETED, message="; ".join(messages),
                          data={'completed_steps': len(steps)})

    def _handle_open_action(self, command: ParsedCommand) -> TaskResult:
        """Handle open/launch actions."""
        app_name = command.target or command.application.value

        try:
            # Try to find if application is already running
            windows = gw.getWindowsWithTitle(app_name) if HAS_PYGETWINDOW and app_name != 'unknown' else []
            if windows:
                # Application is running, bring to front
                windows[0].activate()
                return TaskResult(
                    status=TaskStatus.COMPLETED,
                    message=f"Activated existing {app_name} window"
                )
            
            # Launch application based on type
            if command.application == ApplicationType.VSCODE:
                return self._launch_vscode()
            elif command.application == ApplicationType.CHROME:
                return self._launch_chrome()
            elif command.application == ApplicationType.NOTEPAD:
                return self._launch_notepad()
            elif command.application == ApplicationType.EXPLORER:
                return self._launch_explorer()
            elif command.application == ApplicationType.TERMINAL:
                return self._launch_terminal()
            else:
                # Generic application launch
                return self._launch_generic_app(app_name)
                
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Failed to open {app_name}: {str(e)}"
            )

    def _handle_minimize_action(self, command: ParsedCommand) -> TaskResult:
        """Handle minimize actions."""
        target = command.target
        raw_text = command.raw_text.lower()
        
        # Check for "minimize all"
        minimize_all = "all" in raw_text and ("window" in raw_text or "app" in raw_text or "everything" in raw_text or "minimize all" in raw_text)
        
        if minimize_all:
            if HAS_PYGETWINDOW:
                try:
                    windows = gw.getAllWindows()
                    count = 0
                    for window in windows:
                        if window.title and not window.isMinimized:
                            window.minimize()
                            count += 1
                    return TaskResult(
                        status=TaskStatus.COMPLETED,
                        message=f"Minimized {count} windows"
                    )
                except Exception as e:
                    # Fallback to Win+D or Win+M
                    self.screen_agent.key_combination('win', 'd')
                    return TaskResult(
                        status=TaskStatus.COMPLETED,
                        message="Minimized all windows (Win+D)"
                    )
            else:
                self.screen_agent.key_combination('win', 'd')
                return TaskResult(
                    status=TaskStatus.COMPLETED,
                    message="Minimized all windows (Win+D)"
                )

        if target:
            if HAS_PYGETWINDOW:
                try:
                    windows = gw.getAllWindows()
                    minimized_count = 0
                    for window in windows:
                        if window.title and target.lower() in window.title.lower():
                            window.minimize()
                            minimized_count += 1
                    
                    if minimized_count > 0:
                        return TaskResult(
                            status=TaskStatus.COMPLETED,
                            message=f"Minimized {minimized_count} window(s) matching '{target}'"
                        )
                    else:
                        return TaskResult(
                            status=TaskStatus.FAILED,
                            message=f"No open windows found matching '{target}'"
                        )
                except Exception as e:
                    return TaskResult(
                        status=TaskStatus.FAILED,
                        message=f"Error minimizing '{target}': {str(e)}"
                    )
        
        # Minimize active window
        if HAS_PYGETWINDOW:
            try:
                window = gw.getActiveWindow()
                if window:
                    window.minimize()
                    return TaskResult(
                        status=TaskStatus.COMPLETED,
                        message="Minimized active window"
                    )
            except:
                pass
        
        # Fallback
        self.screen_agent.key_combination('win', 'down')
        return TaskResult(
            status=TaskStatus.COMPLETED,
            message="Minimized active window"
        )

    def _handle_create_action(self, command: ParsedCommand) -> TaskResult:
        """Handle create actions (files, folders, etc.)."""
        if not command.target:
            return TaskResult(
                status=TaskStatus.FAILED,
                message="No target specified for create action"
            )
        
        # For now, implement basic folder creation in VSCode
        if command.application == ApplicationType.VSCODE:
            return self._create_folder_in_vscode(command.target)
        
        return TaskResult(
            status=TaskStatus.FAILED,
            message=f"Create action not implemented for {command.application.value}"
        )
    
    def _handle_click_action(self, command: ParsedCommand) -> TaskResult:
        """Handle click actions with spatial reasoning and template matching."""
        if not command.target:
            return TaskResult(
                status=TaskStatus.FAILED,
                message="No target specified for click action"
            )
        
        # Check for window controls (minimize, maximize, close)
        window_controls = {
            'minimize': 'minimize.png',
            'maximize': 'maximize.png',
            'close': 'close.png',
            'close button': 'close.png',
            'minimize button': 'minimize.png',
            'maximize button': 'maximize.png'
        }
        
        target_lower = command.target.lower()

        # 1. Ask the foreground app for a control with that name (accessibility tree).
        #    Far more reliable than OCR: "click type a message", "click the text box".
        if target_lower not in window_controls:
            from ..core import ui_automation
            control = ui_automation.find_control(command.target)
            if control:
                x, y, w, h = control['rect']
                label = control['name'] or 'text box'
                if self.screen_agent.click_element(x + w // 2, y + h // 2):
                    return TaskResult(status=TaskStatus.COMPLETED, message=f"Clicked '{label}'",
                                      data={'method': 'ui_automation', 'control': control})

        if target_lower in window_controls:
            import os
            template_name = window_controls[target_lower]
            template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', template_name)
            
            if os.path.exists(template_path):
                self.logger.info(f"Looking for window control: {template_name}")
                match = self.screen_agent.find_element_by_image(template_path)
                if match:
                    return self._click_match(match, command.target)
                else:
                    # Fallback to text search if template fails (e.g. "Close" text)
                    self.logger.info("Template match failed, falling back to text search")
            else:
                self.logger.warning(f"Template not found: {template_path}")

        # Try to find element by text
        matches = self.screen_agent.find_text_on_screen(command.target)
        
        if not matches:
             return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Could not find '{command.target}' to click"
            )

        # Handle single match
        if len(matches) == 1:
            return self._click_match(matches[0], command.target)

        # Handle multiple matches
        # Check for spatial context in the command
        spatial_context = self._extract_spatial_context(command.raw_text)
        
        if spatial_context:
            best_match = self._resolve_spatial_ambiguity(matches, spatial_context)
            if best_match:
                return self._click_match(best_match, command.target)
            else:
                return TaskResult(
                    status=TaskStatus.FAILED,
                    message=f"Found multiple '{command.target}' but couldn't resolve '{spatial_context['relation']}' '{spatial_context['reference']}'"
                )
        
        # If no spatial context, return ambiguous status
        return TaskResult(
            status=TaskStatus.AMBIGUOUS,
            message=f"Found {len(matches)} instances of '{command.target}'. Please specify which one (e.g., 'near File').",
            data={'matches': matches, 'target': command.target, 'count': len(matches)}
        )

    def _click_match(self, match, target_name):
        """Helper to click a specific match."""
        x, y, w, h = match
        center_x = x + w // 2
        center_y = y + h // 2
        
        if self.screen_agent.click_element(center_x, center_y):
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message=f"Clicked on '{target_name}'"
            )
        return TaskResult(
            status=TaskStatus.FAILED,
            message=f"Failed to click '{target_name}'"
        )

    def _extract_spatial_context(self, text: str) -> Optional[Dict[str, str]]:
        """Extract spatial relation and reference object from text."""
        import re
        text = text.lower()
        
        # Define spatial patterns
        patterns = [
            (r'\b(near|beside|next to|by)\s+(.+)', 'near'),
            (r'\b(below|under|underneath)\s+(.+)', 'below'),
            (r'\b(above|over)\s+(.+)', 'above'),
            (r'\b(right of|to the right of)\s+(.+)', 'right'),
            (r'\b(left of|to the left of)\s+(.+)', 'left')
        ]
        
        for pattern, relation in patterns:
            match = re.search(pattern, text)
            if match:
                reference = match.group(2).strip()
                # Clean up reference (remove common words if needed)
                return {'relation': relation, 'reference': reference}
        
        return None

    def _resolve_spatial_ambiguity(self, matches, context):
        """Resolve ambiguity using spatial context."""
        relation = context['relation']
        reference_text = context['reference']
        
        # Find the reference object
        ref_matches = self.screen_agent.find_text_on_screen(reference_text)
        if not ref_matches:
            return None
            
        # Use the first found reference object (simplification)
        ref_x, ref_y, ref_w, ref_h = ref_matches[0]
        ref_center_x = ref_x + ref_w // 2
        ref_center_y = ref_y + ref_h // 2
        
        best_match = None
        min_dist = float('inf')
        
        for match in matches:
            x, y, w, h = match
            center_x = x + w // 2
            center_y = y + h // 2
            
            # Calculate distance
            dist = ((center_x - ref_center_x)**2 + (center_y - ref_center_y)**2)**0.5
            
            # Check directional constraints
            valid = True
            if relation == 'below' and center_y <= ref_center_y: valid = False
            if relation == 'above' and center_y >= ref_center_y: valid = False
            if relation == 'right' and center_x <= ref_center_x: valid = False
            if relation == 'left' and center_x >= ref_center_x: valid = False
            
            if valid and dist < min_dist:
                min_dist = dist
                best_match = match
                
        return best_match
    
    def _handle_type_action(self, command: ParsedCommand) -> TaskResult:
        """Handle typing actions."""
        target_text = command.target
        
        if not target_text:
            return TaskResult(
                status=TaskStatus.FAILED,
                message="No text specified for type action"
            )

        # Check for code generation request
        # e.g., "type a code of adding two numbers", "write code for hello world"
        lower_text = target_text.lower()
        if "code" in lower_text and ("type" in lower_text or "write" in lower_text or "generate" in lower_text or "of" in lower_text or "for" in lower_text):
            # Attempt to generate code
            generated_code = self._generate_code_snippet(target_text)
            if generated_code:
                target_text = generated_code
                self.logger.info(f"Generated code: {target_text}")

        if self.screen_agent.type_text(target_text):
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message=f"Typed: '{target_text}'"
            )

        return TaskResult(
            status=TaskStatus.FAILED,
            message="Failed to type text"
        )

    def _generate_code_snippet(self, request: str) -> Optional[str]:
        """
        Generate simple code snippets based on request.
        In a full implementation, this would call an LLM.
        """
        request = request.lower()
        
        # Python snippets
        if "python" in request or "code" in request:
            if "add" in request and "two number" in request:
                return "def add(a, b):\n    return a + b\n\nresult = add(5, 3)\nprint(result)"
            elif "hello world" in request:
                return "print('Hello, World!')"
            elif "factorial" in request:
                return "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)"
            elif "fibonacci" in request:
                return "def fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        print(a)\n        a, b = b, a + b"
            elif "loop" in request or "for loop" in request:
                return "for i in range(10):\n    print(i)"
            elif "if else" in request:
                return "if x > 0:\n    print('Positive')\nelse:\n    print('Non-positive')"
        
        # HTML snippets
        if "html" in request:
            if "boilerplate" in request or "structure" in request:
                return "<!DOCTYPE html>\n<html>\n<head>\n    <title>Page</title>\n</head>\n<body>\n    <h1>Hello</h1>\n</body>\n</html>"
            elif "button" in request:
                return "<button onclick='alert(\"Clicked!\")'>Click Me</button>"
        
        # If it looks like a code request but we don't have a template, 
        # try to extract the subject and make a best guess or return None
        # to fall back to typing the literal text (or maybe a comment)
        if "code of" in request:
            subject = request.split("code of")[-1].strip()
            return f"# Code for {subject}\n# (AI generation not fully connected)"
            
        return None

    def _handle_press_action(self, command: ParsedCommand) -> TaskResult:
        """Handle pressing keyboard keys."""
        # Extract the key to press
        key = command.target or command.parameters.get('key', '')

        if not key:
            # Try to extract from raw text
            import re
            # Check for Windows key patterns
            if re.search(r'(windows\s+key|win\s+key)', command.raw_text.lower()):
                key = 'win'
            else:
                match = re.search(r'press\s+(\w+)', command.raw_text.lower())
                if match:
                    key = match.group(1)

        if not key:
            return TaskResult(
                status=TaskStatus.FAILED,
                message="No key specified for press action"
            )

        # Map common key names
        key_map = {
            'return': 'enter',
            'esc': 'escape',
            'del': 'delete',
            'spacebar': 'space',
            'windows': 'win',
            'windows key': 'win',
            'win key': 'win'
        }
        key = key_map.get(key.lower(), key.lower())

        try:
            if self.screen_agent.press_key(key):
                return TaskResult(
                    status=TaskStatus.COMPLETED,
                    message=f"Pressed key: {key}"
                )
        except Exception as e:
            self.logger.error(f"Error pressing key: {e}")

        return TaskResult(
            status=TaskStatus.FAILED,
            message=f"Failed to press key: {key}"
        )
    
    def _handle_search_action(self, command: ParsedCommand) -> TaskResult:
        """Handle search actions."""
        if not command.target:
            return TaskResult(
                status=TaskStatus.FAILED,
                message="No search term specified"
            )
        
        # Generic search: Ctrl+F and type
        if self.screen_agent.key_combination('ctrl', 'f'):
            time.sleep(0.5)
            if self.screen_agent.type_text(command.target):
                return TaskResult(
                    status=TaskStatus.COMPLETED,
                    message=f"Searched for: '{command.target}'"
                )
        
        return TaskResult(
            status=TaskStatus.FAILED,
            message="Failed to perform search"
        )
    
    def _handle_scroll_action(self, command: ParsedCommand) -> TaskResult:
        """Handle scroll actions."""
        direction = command.parameters.get('direction', 'down') if command.parameters else 'down'
        clicks = 3 if direction == 'down' else -3
        
        if self.screen_agent.scroll(clicks):
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message=f"Scrolled {direction}"
            )
        
        return TaskResult(
            status=TaskStatus.FAILED,
            message="Failed to scroll"
        )
    
    def _handle_close_action(self, command: ParsedCommand) -> TaskResult:
        """Handle close actions."""
        target = command.target
        
        # If target is not explicitly set but application is known, use application name
        if not target and command.application != ApplicationType.UNKNOWN:
            target = command.application.value

        if target:
            # Try to close specific application/window
            if HAS_PYGETWINDOW:
                try:
                    # Get all windows
                    windows = gw.getAllWindows()
                    closed_count = 0
                    
                    for window in windows:
                        # Check if target is in window title (case insensitive)
                        if window.title and target.lower() in window.title.lower():
                            self.logger.info(f"Closing window: {window.title}")
                            window.close()
                            closed_count += 1
                    
                    if closed_count > 0:
                        return TaskResult(
                            status=TaskStatus.COMPLETED,
                            message=f"Closed {closed_count} window(s) matching '{target}'"
                        )
                    else:
                        return TaskResult(
                            status=TaskStatus.FAILED,
                            message=f"No open windows found matching '{target}'"
                        )
                except Exception as e:
                    self.logger.error(f"Error closing window: {e}")
                    return TaskResult(
                        status=TaskStatus.FAILED,
                        message=f"Error closing '{target}': {str(e)}"
                    )
            else:
                 return TaskResult(
                    status=TaskStatus.FAILED,
                    message="Window management library not available"
                )

        # If no target specified, close current window
        # Try Alt+F4 to close current window
        if self.screen_agent.key_combination('alt', 'f4'):
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message="Closed current window"
            )
        
        return TaskResult(
            status=TaskStatus.FAILED,
            message="Failed to close window"
        )
    
    @staticmethod
    def _start_process(name: str):
        """Launch via the shell's `start`, which also resolves registered App Paths
        (chrome, excel, ...). Passing a list keeps the name quoted as one argument."""
        import subprocess
        subprocess.Popen(['cmd', '/c', 'start', '', name],
                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))

    def _launch_vscode(self) -> TaskResult:
        """Launch Visual Studio Code."""
        import subprocess
        try:
            self._start_process('code')
            time.sleep(3)  # Wait for application to start
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message="Launched Visual Studio Code"
            )
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Failed to launch VSCode: {str(e)}"
            )
    
    def _launch_chrome(self) -> TaskResult:
        """Launch Google Chrome."""
        import subprocess
        try:
            self._start_process('chrome')
            time.sleep(3)
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message="Launched Google Chrome"
            )
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Failed to launch Chrome: {str(e)}"
            )
    
    def _launch_notepad(self) -> TaskResult:
        """Launch Notepad."""
        import subprocess
        try:
            self._start_process('notepad')
            time.sleep(2)
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message="Launched Notepad"
            )
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Failed to launch Notepad: {str(e)}"
            )
    
    def _launch_explorer(self) -> TaskResult:
        """Launch File Explorer."""
        import subprocess
        try:
            self._start_process('explorer')
            time.sleep(2)
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message="Launched File Explorer"
            )
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Failed to launch Explorer: {str(e)}"
            )
    
    def _launch_terminal(self) -> TaskResult:
        """Launch Terminal/Command Prompt."""
        import subprocess
        try:
            self._start_process('cmd')
            time.sleep(2)
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message="Launched Terminal"
            )
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Failed to launch Terminal: {str(e)}"
            )
    
    def _launch_generic_app(self, app_name: str) -> TaskResult:
        """Launch a generic application by name."""
        import subprocess
        try:
            self._start_process(app_name)
            time.sleep(3)
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message=f"Launched {app_name}"
            )
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Failed to launch {app_name}: {str(e)}"
            )
    
    def _create_folder_in_vscode(self, folder_name: str) -> TaskResult:
        """Create a folder in VSCode."""
        try:
            # Right-click in explorer panel and select "New Folder"
            # This is a simplified implementation
            if self.screen_agent.key_combination('ctrl', 'shift', 'e'):  # Open explorer
                time.sleep(1)
                if self.screen_agent.key_combination('ctrl', 'shift', 'n'):  # New folder shortcut
                    time.sleep(0.5)
                    if self.screen_agent.type_text(folder_name):
                        self.screen_agent.press_key('enter')
                        return TaskResult(
                            status=TaskStatus.COMPLETED,
                            message=f"Created folder '{folder_name}' in VSCode"
                        )
            
            return TaskResult(
                status=TaskStatus.FAILED,
                message="Failed to create folder in VSCode"
            )
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error creating folder: {str(e)}"
            )
    
    def get_task_history(self) -> List[Dict[str, Any]]:
        """Get task execution history."""
        return self.task_history.copy()
    
    def is_busy(self) -> bool:
        """Check if engine is currently executing a task."""
        return self.is_executing
    
    def cancel_current_task(self):
        """Cancel the currently executing task."""
        if self.is_executing:
            self.is_executing = False
            self.logger.info("Task execution cancelled")
    
    def get_running_applications(self) -> List[str]:
        """Get list of currently running applications."""
        try:
            apps = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    apps.append(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return list(set(apps))  # Remove duplicates
        except Exception as e:
            self.logger.error(f"Error getting running applications: {e}")
            return []
