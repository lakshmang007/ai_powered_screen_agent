"""
Core task automation engine for executing parsed commands.
"""

import time
import logging
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import psutil
import pygetwindow as gw

from ..core.screen_agent import ScreenAgent
from ..core.nlp_processor import ParsedCommand, ActionType, ApplicationType

class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

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
        elif command.action == ActionType.SEARCH:
            return self._handle_search_action(command)
        elif command.action == ActionType.SCROLL:
            return self._handle_scroll_action(command)
        elif command.action == ActionType.CLOSE:
            return self._handle_close_action(command)
        else:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Unsupported action: {command.action.value}"
            )
    
    def _handle_open_action(self, command: ParsedCommand) -> TaskResult:
        """Handle open/launch actions."""
        app_name = command.target or command.application.value
        
        try:
            # Try to find if application is already running
            windows = gw.getWindowsWithTitle(app_name)
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
        """Handle click actions."""
        if not command.target:
            return TaskResult(
                status=TaskStatus.FAILED,
                message="No target specified for click action"
            )
        
        # Try to find element by text
        text_matches = self.screen_agent.find_text_on_screen(command.target)
        if text_matches:
            x, y, w, h = text_matches[0]
            center_x = x + w // 2
            center_y = y + h // 2
            
            if self.screen_agent.click_element(center_x, center_y):
                return TaskResult(
                    status=TaskStatus.COMPLETED,
                    message=f"Clicked on '{command.target}'"
                )
        
        return TaskResult(
            status=TaskStatus.FAILED,
            message=f"Could not find '{command.target}' to click"
        )
    
    def _handle_type_action(self, command: ParsedCommand) -> TaskResult:
        """Handle typing actions."""
        if not command.target:
            return TaskResult(
                status=TaskStatus.FAILED,
                message="No text specified for type action"
            )
        
        if self.screen_agent.type_text(command.target):
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message=f"Typed: '{command.target}'"
            )
        
        return TaskResult(
            status=TaskStatus.FAILED,
            message="Failed to type text"
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
    
    def _launch_vscode(self) -> TaskResult:
        """Launch Visual Studio Code."""
        import subprocess
        try:
            subprocess.Popen(['code'], shell=True)
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
            subprocess.Popen(['chrome'], shell=True)
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
            subprocess.Popen(['notepad'], shell=True)
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
            subprocess.Popen(['explorer'], shell=True)
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
            subprocess.Popen(['cmd'], shell=True)
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
            subprocess.Popen([app_name], shell=True)
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
