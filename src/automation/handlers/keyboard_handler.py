"""
Keyboard automation handler.
Handles keyboard shortcuts, key presses, and combinations.
"""

import logging
import time
from typing import Dict, Any
import pyautogui

from ...core.nlp_processor import ParsedCommand, ActionType


class KeyboardHandler:
    """Handler for keyboard automation."""
    
    def __init__(self, screen_agent=None):
        """
        Initialize keyboard handler.
        
        Args:
            screen_agent: Screen agent for keyboard control
        """
        self.screen_agent = screen_agent
        self.logger = logging.getLogger(__name__)
        
        # Key mappings for common commands
        self.key_mappings = {
            # Windows keys
            'windows': 'win',
            'windows key': 'win',
            'win': 'win',
            'start': 'win',
            'start menu': 'win',
            
            # Special keys
            'enter': 'enter',
            'return': 'enter',
            'escape': 'esc',
            'esc': 'esc',
            'space': 'space',
            'spacebar': 'space',
            'tab': 'tab',
            'backspace': 'backspace',
            'delete': 'delete',
            'del': 'delete',
            
            # Arrow keys
            'up': 'up',
            'down': 'down',
            'left': 'left',
            'right': 'right',
            'up arrow': 'up',
            'down arrow': 'down',
            'left arrow': 'left',
            'right arrow': 'right',
            
            # Modifier keys
            'ctrl': 'ctrl',
            'control': 'ctrl',
            'alt': 'alt',
            'shift': 'shift',
            
            # Function keys
            'f1': 'f1', 'f2': 'f2', 'f3': 'f3', 'f4': 'f4',
            'f5': 'f5', 'f6': 'f6', 'f7': 'f7', 'f8': 'f8',
            'f9': 'f9', 'f10': 'f10', 'f11': 'f11', 'f12': 'f12',
            
            # Other keys
            'home': 'home',
            'end': 'end',
            'pageup': 'pageup',
            'pagedown': 'pagedown',
            'insert': 'insert',
            'printscreen': 'printscreen',
            'pause': 'pause',
        }
        
        # Common keyboard shortcuts
        self.shortcuts = {
            'copy': ['ctrl', 'c'],
            'paste': ['ctrl', 'v'],
            'cut': ['ctrl', 'x'],
            'undo': ['ctrl', 'z'],
            'redo': ['ctrl', 'y'],
            'save': ['ctrl', 's'],
            'select all': ['ctrl', 'a'],
            'find': ['ctrl', 'f'],
            'new tab': ['ctrl', 't'],
            'close tab': ['ctrl', 'w'],
            'new window': ['ctrl', 'n'],
            'refresh': ['f5'],
            'task manager': ['ctrl', 'shift', 'esc'],
            'screenshot': ['win', 'shift', 's'],
            'lock screen': ['win', 'l'],
            'minimize all': ['win', 'd'],
            'file explorer': ['win', 'e'],
            'settings': ['win', 'i'],
            'search': ['win', 's'],
        }
    
    def handle_command(self, command: ParsedCommand) -> Dict[str, Any]:
        """
        Handle a keyboard automation command.
        
        Args:
            command: Parsed command
            
        Returns:
            Result dictionary with status and message
        """
        try:
            action = command.action.value.lower()
            params = command.parameters
            
            # Get the key or shortcut from parameters or target
            key_text = params.get('key', command.target or '').lower()
            
            if not key_text:
                return {
                    'status': 'failed',
                    'message': 'No key specified'
                }
            
            # Check if it's a known shortcut
            if key_text in self.shortcuts:
                return self.press_shortcut(key_text)
            
            # Check if it's a key combination (e.g., "ctrl+c")
            if '+' in key_text or ' and ' in key_text:
                return self.press_combination(key_text)
            
            # Single key press
            return self.press_key(key_text)
        
        except Exception as e:
            self.logger.error(f"Keyboard handler error: {e}")
            return {
                'status': 'error',
                'message': f'Keyboard error: {str(e)}'
            }
    
    def press_key(self, key: str) -> Dict[str, Any]:
        """
        Press a single key.
        
        Args:
            key: Key name
            
        Returns:
            Result dictionary
        """
        try:
            # Map to pyautogui key name
            mapped_key = self.key_mappings.get(key.lower(), key.lower())
            
            self.logger.info(f"Pressing key: {mapped_key}")
            pyautogui.press(mapped_key)
            
            return {
                'status': 'completed',
                'message': f'Pressed key: {key}',
                'data': {'key': mapped_key}
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Failed to press key {key}: {str(e)}'
            }
    
    def press_combination(self, combination: str) -> Dict[str, Any]:
        """
        Press a key combination.
        
        Args:
            combination: Key combination (e.g., "ctrl+c" or "ctrl and c")
            
        Returns:
            Result dictionary
        """
        try:
            # Parse combination
            if '+' in combination:
                keys = [k.strip() for k in combination.split('+')]
            elif ' and ' in combination:
                keys = [k.strip() for k in combination.split(' and ')]
            else:
                keys = [combination]
            
            # Map keys
            mapped_keys = [self.key_mappings.get(k.lower(), k.lower()) for k in keys]
            
            self.logger.info(f"Pressing combination: {'+'.join(mapped_keys)}")
            pyautogui.hotkey(*mapped_keys)
            
            return {
                'status': 'completed',
                'message': f'Pressed combination: {combination}',
                'data': {'keys': mapped_keys}
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Failed to press combination {combination}: {str(e)}'
            }
    
    def press_shortcut(self, shortcut_name: str) -> Dict[str, Any]:
        """
        Press a named shortcut.
        
        Args:
            shortcut_name: Name of shortcut (e.g., "copy", "paste")
            
        Returns:
            Result dictionary
        """
        try:
            if shortcut_name not in self.shortcuts:
                return {
                    'status': 'failed',
                    'message': f'Unknown shortcut: {shortcut_name}'
                }
            
            keys = self.shortcuts[shortcut_name]
            
            self.logger.info(f"Pressing shortcut '{shortcut_name}': {'+'.join(keys)}")
            pyautogui.hotkey(*keys)
            
            return {
                'status': 'completed',
                'message': f'Pressed shortcut: {shortcut_name}',
                'data': {'shortcut': shortcut_name, 'keys': keys}
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Failed to press shortcut {shortcut_name}: {str(e)}'
            }
    
    def type_text(self, text: str, interval: float = 0.05) -> Dict[str, Any]:
        """
        Type text.
        
        Args:
            text: Text to type
            interval: Interval between keystrokes
            
        Returns:
            Result dictionary
        """
        try:
            self.logger.info(f"Typing text: {text}")
            pyautogui.write(text, interval=interval)
            
            return {
                'status': 'completed',
                'message': f'Typed text: {text}',
                'data': {'text': text}
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Failed to type text: {str(e)}'
            }

