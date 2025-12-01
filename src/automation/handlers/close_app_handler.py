"""
Close Application Handler.
Handles closing applications and windows.
"""

import logging
import time
import subprocess
from typing import Dict, Any, Optional

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False
    pyautogui = None

try:
    import pygetwindow as gw
    HAS_PYGETWINDOW = True
except ImportError:
    HAS_PYGETWINDOW = False
    gw = None


class CloseAppHandler:
    """Handler for closing applications."""
    
    def __init__(self, voice_processor=None):
        """
        Initialize close app handler.
        
        Args:
            voice_processor: Voice processor for user interaction
        """
        self.voice_processor = voice_processor
        self.logger = logging.getLogger(__name__)
    
    def close_application(self, app_name: str) -> Dict[str, Any]:
        """
        Close an application by name.

        Args:
            app_name: Name of the application to close

        Returns:
            Result dictionary
        """
        try:
            self.logger.info(f"Attempting to close application: {app_name}")

            # Normalize app name and create variations
            app_name_lower = app_name.lower()

            # Create variations of the app name
            variations = [
                app_name_lower,
                app_name_lower.replace(' ', ''),  # Remove spaces: "nfs 13" -> "nfs13"
                app_name_lower.replace(' ', '_'),  # Replace with underscore: "nfs 13" -> "nfs_13"
                app_name_lower.replace(' ', '-'),  # Replace with dash: "nfs 13" -> "nfs-13"
            ]

            # Add individual words for partial matching
            words = app_name_lower.split()
            variations.extend(words)

            self.logger.info(f"Searching for windows with variations: {variations}")

            # Get all windows
            all_windows = gw.getAllWindows()

            # Find windows matching the app name
            matching_windows = []
            for window in all_windows:
                if not window.title.strip():
                    continue

                window_title_lower = window.title.lower()

                # Check for match with any variation
                for variation in variations:
                    if variation in window_title_lower or window_title_lower in variation:
                        if window not in matching_windows:
                            matching_windows.append(window)
                            self.logger.info(f"Found matching window: {window.title}")
                        break
            
            if not matching_windows:
                self.logger.warning(f"No windows found for: {app_name}")
                
                if self.voice_processor:
                    self.voice_processor.speak(f"Lucky, I couldn't find {app_name} running.")
                
                return {
                    'status': 'failed',
                    'message': f'{app_name} is not running'
                }
            
            # Close all matching windows
            closed_count = 0
            for window in matching_windows:
                try:
                    self.logger.info(f"Closing window: {window.title}")
                    
                    # Activate the window first
                    window.activate()
                    time.sleep(0.3)
                    
                    # Try to close using Alt+F4
                    pyautogui.hotkey('alt', 'f4')
                    time.sleep(0.5)
                    
                    closed_count += 1
                
                except Exception as e:
                    self.logger.error(f"Error closing window {window.title}: {e}")
            
            if closed_count > 0:
                self.logger.info(f"Closed {closed_count} window(s) for {app_name}")
                
                if self.voice_processor:
                    self.voice_processor.speak(f"Closed {app_name}.")
                
                return {
                    'status': 'completed',
                    'message': f'Closed {closed_count} window(s) for {app_name}'
                }
            else:
                return {
                    'status': 'failed',
                    'message': f'Failed to close {app_name}'
                }
        
        except Exception as e:
            self.logger.error(f"Error closing application: {e}")
            return {
                'status': 'failed',
                'message': f'Error: {str(e)}'
            }
    
    def close_current_window(self) -> Dict[str, Any]:
        """
        Close the currently active window.
        
        Returns:
            Result dictionary
        """
        try:
            self.logger.info("Closing current window")
            
            # Press Alt+F4
            pyautogui.hotkey('alt', 'f4')
            time.sleep(0.5)
            
            if self.voice_processor:
                self.voice_processor.speak("Closed the current window.")
            
            return {
                'status': 'completed',
                'message': 'Closed current window'
            }
        
        except Exception as e:
            self.logger.error(f"Error closing current window: {e}")
            return {
                'status': 'failed',
                'message': f'Error: {str(e)}'
            }
    
    def force_close_application(self, app_name: str) -> Dict[str, Any]:
        """
        Force close an application using taskkill.

        Args:
            app_name: Name of the application to force close

        Returns:
            Result dictionary
        """
        try:
            self.logger.info(f"Force closing application: {app_name}")

            # Try to kill the process
            # Common process names
            process_names = {
                'chrome': 'chrome.exe',
                'edge': 'msedge.exe',
                'firefox': 'firefox.exe',
                'opera': 'opera.exe',
                'word': 'WINWORD.EXE',
                'excel': 'EXCEL.EXE',
                'powerpoint': 'POWERPNT.EXE',
                'notepad': 'notepad.exe',
                'calculator': 'CalculatorApp.exe',
                'dolby': 'DolbyAccess.exe',
            }

            app_name_lower = app_name.lower()

            # Create variations of process names to try
            process_variations = []

            # Check if it's a known app
            if app_name_lower in process_names:
                process_variations.append(process_names[app_name_lower])

            # Try different variations
            process_variations.extend([
                f"{app_name}.exe",
                f"{app_name_lower}.exe",
                f"{app_name.replace(' ', '')}.exe",  # Remove spaces: "nfs 13" -> "nfs13.exe"
                f"{app_name_lower.replace(' ', '')}.exe",
                f"{app_name.replace(' ', '_')}.exe",  # Replace with underscore
                f"{app_name.replace(' ', '-')}.exe",  # Replace with dash
            ])

            # Try each variation
            for process_name in process_variations:
                self.logger.info(f"Trying to kill process: {process_name}")

                # Use taskkill command
                result = subprocess.run(
                    ['taskkill', '/F', '/IM', process_name],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    self.logger.info(f"Force closed {app_name} (process: {process_name})")

                    if self.voice_processor:
                        self.voice_processor.speak(f"Force closed {app_name}.")

                    return {
                        'status': 'completed',
                        'message': f'Force closed {app_name}'
                    }

            # If all variations failed
            self.logger.warning(f"Failed to force close {app_name} with any process name variation")
            return {
                'status': 'failed',
                'message': f'Failed to force close {app_name}'
            }
        
        except Exception as e:
            self.logger.error(f"Error force closing application: {e}")
            return {
                'status': 'failed',
                'message': f'Error: {str(e)}'
            }

