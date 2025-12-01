"""
VSCode-specific automation handler.
"""

import time
import logging
import subprocess
from typing import Optional

try:
    import pygetwindow as gw
    HAS_PYGETWINDOW = True
except ImportError:
    HAS_PYGETWINDOW = False
    gw = None

from ...core.screen_agent import ScreenAgent
from ...core.nlp_processor import ParsedCommand, ActionType
from ..task_engine import TaskResult, TaskStatus

class VSCodeHandler:
    """Handler for Visual Studio Code automation."""
    
    def __init__(self, screen_agent: ScreenAgent):
        """
        Initialize VSCode handler.
        
        Args:
            screen_agent: Screen agent for UI interactions
        """
        self.screen_agent = screen_agent
        self.logger = logging.getLogger(__name__)
        self.vscode_window = None
    
    def handle_command(self, command: ParsedCommand) -> TaskResult:
        """
        Handle VSCode-specific commands.
        
        Args:
            command: Parsed command to execute
            
        Returns:
            TaskResult with execution status
        """
        try:
            # For CLOSE action, we don't want to launch VSCode if it's not running
            allow_launch = command.action != ActionType.CLOSE
            
            # Ensure VSCode is open and focused
            if not self._ensure_vscode_active(allow_launch=allow_launch):
                if command.action == ActionType.CLOSE:
                    return TaskResult(
                        status=TaskStatus.COMPLETED,
                        message="VSCode is not running"
                    )
                return TaskResult(
                    status=TaskStatus.FAILED,
                    message="Could not open or focus VSCode"
                )
            
            if command.action == ActionType.CREATE:
                return self._handle_create_action(command)
            elif command.action == ActionType.OPEN:
                return self._handle_open_action(command)
            elif command.action == ActionType.SEARCH:
                return self._handle_search_action(command)
            elif command.action == ActionType.TYPE:
                return self._handle_type_action(command)
            elif command.action == ActionType.CLOSE:
                return self._handle_close_action(command)
            else:
                return TaskResult(
                    status=TaskStatus.FAILED,
                    message=f"Unsupported VSCode action: {command.action.value}"
                )
                
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"VSCode handler error: {str(e)}"
            )
    
    def _ensure_vscode_active(self, allow_launch: bool = True) -> bool:
        """Ensure VSCode is open and active."""
        try:
            # Look for VSCode windows
            vscode_windows = []
            if gw:
                for window in gw.getAllWindows():
                    if 'visual studio code' in window.title.lower() or 'code' in window.title.lower():
                        vscode_windows.append(window)
            
            if vscode_windows:
                # Activate the first VSCode window found
                self.vscode_window = vscode_windows[0]
                try:
                    if self.vscode_window.isMinimized:
                        self.vscode_window.restore()
                        time.sleep(0.5)
                    self.vscode_window.activate()
                except Exception as e:
                    # Ignore "Error code from Windows: 0" which actually means success sometimes
                    if "Error code from Windows: 0" in str(e):
                        pass
                    else:
                        self.logger.warning(f"Error activating VSCode window: {e}")
                
                time.sleep(1)
                return True
            elif allow_launch:
                # Launch VSCode
                self.logger.info("Launching VSCode...")
                subprocess.Popen(['code'], shell=True)
                time.sleep(4)  # Wait for VSCode to start
                
                # Try to find the window again
                if gw:
                    for _ in range(10):  # Try for 10 seconds
                        for window in gw.getAllWindows():
                            if 'visual studio code' in window.title.lower():
                                self.vscode_window = window
                                try:
                                    self.vscode_window.activate()
                                except:
                                    pass
                                time.sleep(1)
                                return True
                        time.sleep(1)
                
                return False
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error ensuring VSCode active: {e}")
            return False
    
    def _handle_create_action(self, command: ParsedCommand) -> TaskResult:
        """Handle create actions in VSCode."""
        if not command.target:
            return TaskResult(
                status=TaskStatus.FAILED,
                message="No target specified for create action"
            )
        
        target = command.target.strip()
        
        # Determine if creating file or folder
        is_folder = any(keyword in command.raw_text.lower() 
                       for keyword in ['folder', 'directory', 'dir'])
        
        try:
            if is_folder:
                return self._create_folder(target)
            else:
                return self._create_file(target)
                
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error creating {target}: {str(e)}"
            )
    
    def _create_folder(self, folder_name: str) -> TaskResult:
        """Create a new folder in VSCode."""
        try:
            # Open explorer panel
            self.screen_agent.key_combination('ctrl', 'shift', 'e')
            time.sleep(1)
            
            # Right-click in explorer to open context menu
            # First, try to find the explorer panel
            explorer_found = False
            
            # Look for "Explorer" text or use a general area
            text_matches = self.screen_agent.find_text_on_screen("EXPLORER")
            if text_matches:
                x, y, w, h = text_matches[0]
                # Click below the explorer title
                self.screen_agent.click_element(x + 50, y + 50, button='right')
                explorer_found = True
            else:
                # Fallback: right-click in the left panel area
                screen_width, screen_height = self.screen_agent.get_screen_size()
                self.screen_agent.click_element(200, 300, button='right')
                explorer_found = True
            
            if explorer_found:
                time.sleep(0.5)
                
                # Look for "New Folder" option and click it
                new_folder_matches = self.screen_agent.find_text_on_screen("New Folder")
                if new_folder_matches:
                    x, y, w, h = new_folder_matches[0]
                    self.screen_agent.click_element(x + w//2, y + h//2)
                    time.sleep(0.5)
                    
                    # Type the folder name
                    self.screen_agent.type_text(folder_name)
                    self.screen_agent.press_key('enter')
                    
                    return TaskResult(
                        status=TaskStatus.COMPLETED,
                        message=f"Created folder '{folder_name}' in VSCode"
                    )
                else:
                    # Try keyboard shortcut as fallback
                    self.screen_agent.press_key('escape')  # Close context menu
                    time.sleep(0.2)
                    
                    # Use Ctrl+Shift+N for new folder (if available)
                    self.screen_agent.key_combination('ctrl', 'shift', 'n')
                    time.sleep(0.5)
                    self.screen_agent.type_text(folder_name)
                    self.screen_agent.press_key('enter')
                    
                    return TaskResult(
                        status=TaskStatus.COMPLETED,
                        message=f"Created folder '{folder_name}' in VSCode (using shortcut)"
                    )
            
            return TaskResult(
                status=TaskStatus.FAILED,
                message="Could not find explorer panel to create folder"
            )
            
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error creating folder: {str(e)}"
            )
    
    def _create_file(self, file_name: str) -> TaskResult:
        """Create a new file in VSCode."""
        try:
            # Use Ctrl+N to create new file
            self.screen_agent.key_combination('ctrl', 'n')
            time.sleep(1)
            
            # Save the file with the specified name
            self.screen_agent.key_combination('ctrl', 's')
            time.sleep(1)
            
            # Type the filename
            self.screen_agent.type_text(file_name)
            self.screen_agent.press_key('enter')
            
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message=f"Created file '{file_name}' in VSCode"
            )
            
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error creating file: {str(e)}"
            )
    
    def _handle_open_action(self, command: ParsedCommand) -> TaskResult:
        """Handle open actions in VSCode."""
        if command.target:
            # Open specific file/folder
            self.screen_agent.key_combination('ctrl', 'o')
            time.sleep(1)
            self.screen_agent.type_text(command.target)
            self.screen_agent.press_key('enter')
            
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message=f"Opened '{command.target}' in VSCode"
            )
        else:
            # Just open VSCode (already handled by _ensure_vscode_active)
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message="VSCode is now active"
            )
    
    def _handle_search_action(self, command: ParsedCommand) -> TaskResult:
        """Handle search actions in VSCode."""
        if not command.target:
            return TaskResult(
                status=TaskStatus.FAILED,
                message="No search term specified"
            )
        
        # Use Ctrl+Shift+F for global search
        self.screen_agent.key_combination('ctrl', 'shift', 'f')
        time.sleep(1)
        
        # Type search term
        self.screen_agent.type_text(command.target)
        self.screen_agent.press_key('enter')
        
        return TaskResult(
            status=TaskStatus.COMPLETED,
            message=f"Searched for '{command.target}' in VSCode"
        )
    
    def _handle_type_action(self, command: ParsedCommand) -> TaskResult:
        """Handle typing actions in VSCode."""
        if not command.target:
            return TaskResult(
                status=TaskStatus.FAILED,
                message="No text specified to type"
            )
        
        # Simply type the text
        self.screen_agent.type_text(command.target)
        
        return TaskResult(
            status=TaskStatus.COMPLETED,
            message=f"Typed '{command.target}' in VSCode"
        )
    
    def open_terminal(self) -> TaskResult:
        """Open integrated terminal in VSCode."""
        try:
            self.screen_agent.key_combination('ctrl', 'shift', '`')
            time.sleep(1)
            
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message="Opened integrated terminal in VSCode"
            )
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error opening terminal: {str(e)}"
            )
    
    def run_command_in_terminal(self, command: str) -> TaskResult:
        """Run a command in VSCode's integrated terminal."""
        try:
            # First ensure terminal is open
            terminal_result = self.open_terminal()
            if terminal_result.status != TaskStatus.COMPLETED:
                return terminal_result
            
            # Type and execute command
            self.screen_agent.type_text(command)
            self.screen_agent.press_key('enter')
            
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message=f"Executed command '{command}' in VSCode terminal"
            )
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error running terminal command: {str(e)}"
            )

    def _handle_close_action(self, command: ParsedCommand) -> TaskResult:
        """Handle close actions in VSCode."""
        try:
            # Use Alt+F4 to close VSCode
            self.screen_agent.key_combination('alt', 'f4')
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message="Closed Visual Studio Code"
            )
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error closing VSCode: {str(e)}"
            )
