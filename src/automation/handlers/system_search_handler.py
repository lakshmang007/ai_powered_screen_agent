"""
System Search Handler.
Searches for applications in the system using multiple methods.
"""

import logging
import os
import subprocess
import time
import winreg
from typing import Dict, Any, List, Optional, Tuple
import pyautogui


class SystemSearchHandler:
    """Handler for searching applications in the system."""
    
    def __init__(self, voice_processor=None, interrupt_event=None):
        """
        Initialize system search handler.
        
        Args:
            voice_processor: Voice processor for user interaction
            interrupt_event: Threading event to check for interruption
        """
        self.voice_processor = voice_processor
        self.interrupt_event = interrupt_event
        self.logger = logging.getLogger(__name__)

        # Configure Tesseract path for OCR
        try:
            import pytesseract

            # Check if tesseract is in PATH
            tesseract_cmd = None

            # Try common installation paths
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Tesseract-OCR\tesseract.exe',
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    tesseract_cmd = path
                    self.logger.info(f"Found Tesseract at: {path}")
                    break

            if tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
                self.logger.info(f"Configured Tesseract path: {tesseract_cmd}")
            else:
                self.logger.warning("Tesseract not found in common paths, will try system PATH")

        except ImportError:
            self.logger.warning("pytesseract not installed, OCR features will not work")

        # Common application paths
        self.search_paths = [
            r'C:\Program Files',
            r'C:\Program Files (x86)',
            os.path.expanduser(r'~\AppData\Local'),
            os.path.expanduser(r'~\AppData\Roaming'),
            os.path.expanduser(r'~\Desktop'),
            os.path.expanduser(r'~\Downloads'),
        ]
        
        # Common download URLs for popular apps
        self.download_urls = {
            'spotify': 'https://www.spotify.com/download',
            'discord': 'https://discord.com/download',
            'slack': 'https://slack.com/downloads',
            'zoom': 'https://zoom.us/download',
            'teams': 'https://www.microsoft.com/en-us/microsoft-teams/download-app',
            'vlc': 'https://www.videolan.org/vlc/',
            'notepad++': 'https://notepad-plus-plus.org/downloads/',
            'vscode': 'https://code.visualstudio.com/download',
            'visual studio code': 'https://code.visualstudio.com/download',
            'pycharm': 'https://www.jetbrains.com/pycharm/download/',
            'sublime': 'https://www.sublimetext.com/download',
            'gimp': 'https://www.gimp.org/downloads/',
            'obs': 'https://obsproject.com/download',
            'audacity': 'https://www.audacityteam.org/download/',
        }
    
    def search_application(self, app_name: str, force_windows_search: bool = False) -> Dict[str, Any]:
        """
        Search for an application in the system.

        Args:
            app_name: Name of the application to search
            force_windows_search: Whether to force using Windows Search

        Returns:
            Result dictionary with status and data
        """
        try:
            self.logger.info(f"Searching for application: {app_name} (Force Windows Search: {force_windows_search})")

            # If forced, skip other methods and go straight to Windows Search
            if force_windows_search:
                self.logger.info(f"Forcing Windows Search for: {app_name}")
                return self._windows_search_with_vision(app_name)

            # Special handling for Microsoft Store (UWP app)
            if 'store' in app_name.lower() and 'microsoft' not in app_name.lower():
                app_name = 'microsoft store'
                self.logger.info(f"Detected Microsoft Store, searching for: {app_name}")

            # Special handling for built-in Windows apps
            builtin_apps = {
                'microsoft store': 'ms-windows-store:',
                'store': 'ms-windows-store:',
                'settings': 'ms-settings:',
                'calculator': 'calculator:',
                'calendar': 'outlookcal:',
                'mail': 'outlookmail:',
                'photos': 'ms-photos:',
                'camera': 'microsoft.windows.camera:',
            }

            app_name_lower = app_name.lower()
            if app_name_lower in builtin_apps:
                self.logger.info(f"Found built-in Windows app: {app_name}")
                return {
                    'status': 'found',
                    'method': 'builtin',
                    'app_name': app_name,
                    'path': builtin_apps[app_name_lower],
                    'name': app_name.title(),
                    'message': f'Found {app_name.title()}'
                }

            # Collect ALL matches from all methods
            all_matches = []

            # Method 1: Search in Start Menu
            start_menu_results = self._search_start_menu_all(app_name)
            all_matches.extend(start_menu_results)

            # Method 2: Search in common paths
            path_results = self._search_in_paths_all(app_name)
            all_matches.extend(path_results)

            # Method 3: Search Windows Apps (UWP apps)
            windows_apps_results = self._search_windows_apps(app_name)
            all_matches.extend(windows_apps_results)

            # Method 4: Check registry
            registry_results = self._search_registry_all(app_name)
            all_matches.extend(registry_results)

            # Remove duplicates based on path
            unique_matches = []
            seen_paths = set()
            for match in all_matches:
                path_lower = match['path'].lower()
                if path_lower not in seen_paths:
                    seen_paths.add(path_lower)
                    unique_matches.append(match)

            if unique_matches:
                if len(unique_matches) == 1:
                    # Single match - return it
                    return {
                        'status': 'found',
                        'method': unique_matches[0]['method'],
                        'app_name': app_name,
                        'path': unique_matches[0]['path'],
                        'name': unique_matches[0]['name'],
                        'message': f'Found {unique_matches[0]["name"]}'
                    }
                else:
                    # Multiple matches - ask user which one
                    return self._handle_multiple_matches(app_name, unique_matches)

            # Not found in file system - try Windows Search with vision
            self.logger.info(f"Not found in file system, trying Windows Search with vision for: {app_name}")
            windows_search_result = self._windows_search_with_vision(app_name)

            if windows_search_result.get('status') == 'found':
                return windows_search_result

            # Still not found - ask follow-up question
            return self._handle_not_found(app_name)

        except Exception as e:
            self.logger.error(f"Error searching for application: {e}")
            return {
                'status': 'error',
                'message': f'Error searching for {app_name}: {str(e)}'
            }
    
    # ... (omitted methods) ...

    def _windows_search_with_vision(self, app_name: str) -> Dict[str, Any]:
        """Use Windows Search to find and open application."""
        try:
            import pyautogui
            import time

            self.logger.info(f"Using Windows Search for: {app_name}")
            
            if self.interrupt_event and self.interrupt_event.is_set():
                return {'status': 'cancelled', 'message': 'Interrupted'}

            if self.voice_processor:
                self.voice_processor.speak(f"Lucky, let me search for {app_name} in Windows Search.")

            # Press Win+S to open Windows Search
            pyautogui.hotkey('win', 's')
            
            # Wait with interruption check
            for _ in range(15): # 1.5 seconds
                if self.interrupt_event and self.interrupt_event.is_set():
                    return {'status': 'cancelled', 'message': 'Interrupted'}
                time.sleep(0.1)

            # Type the application name
            pyautogui.write(app_name, interval=0.1)
            
            # Wait with interruption check
            for _ in range(20): # 2 seconds
                if self.interrupt_event and self.interrupt_event.is_set():
                    return {'status': 'cancelled', 'message': 'Interrupted'}
                time.sleep(0.1)

            # Ask user if they can see the app
            if self.voice_processor:
                message = f"Lucky, I opened Windows Search and typed {app_name}. Can you see it in the results? Say yes to open it, or no if it's not there. Say stop to cancel."
                self.logger.info(f"Asking user: {message}")
                self.voice_processor.speak(message)

                # Listen for response
                # We can't easily interrupt listen_once from here unless voice_processor supports it
                # But we can check immediately after
                response = self.voice_processor.listen_once(timeout=20, phrase_time_limit=10)
                
                if self.interrupt_event and self.interrupt_event.is_set():
                    return {'status': 'cancelled', 'message': 'Interrupted'}

                if response:
                    response_lower = response.lower()
                    self.logger.info(f"User response: {response}")

                    # Check for stop/cancel
                    if any(word in response_lower for word in ['stop', 'cancel', 'wait', 'don\'t', 'abort']):
                        self.logger.info("User cancelled operation")
                        if self.voice_processor:
                            self.voice_processor.speak("Okay, stopping.")
                        pyautogui.press('escape')
                        return {'status': 'cancelled', 'message': 'User cancelled'}

                    # Check if user wants to open it
                    if any(word in response_lower for word in ['yes', 'yeah', 'sure', 'ok', 'okay', 'haan', 'open', 'found']):
                        self.logger.info(f"User confirmed, opening {app_name}")

                        if self.voice_processor:
                            self.voice_processor.speak(f"Great! Opening {app_name} now.")

                        # Press Enter to open first result
                        pyautogui.press('enter')
                        time.sleep(1)

                        return {
                            'status': 'found',
                            'method': 'windows_search',
                            'name': app_name,
                            'path': 'windows_search_opened',
                            'message': f'Opened {app_name} via Windows Search'
                        }
                    else:
                        # User said no
                        self.logger.info(f"User said {app_name} is not in search results")

                        if self.voice_processor:
                            self.voice_processor.speak(f"Okay Lucky, closing the search.")

                        pyautogui.press('escape')
                        return {'status': 'not_found'}

            # No voice processor - just open first result
            pyautogui.press('enter')
            time.sleep(1)
            pyautogui.press('escape')

            return {
                'status': 'found',
                'method': 'windows_search',
                'name': app_name,
                'path': 'windows_search_opened',
                'message': f'Opened {app_name} via Windows Search'
            }
        except Exception as e:
            self.logger.error(f"Error in Windows Search: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _search_start_menu_all(self, app_name: str) -> List[Dict[str, Any]]:
        """Search in Start Menu shortcuts and return ALL matches."""
        matches = []
        try:
            start_menu_paths = [
                os.path.expanduser(r'~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs'),
                r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs'
            ]

            # Split app_name into words for better matching
            search_words = app_name.lower().split()

            for base_path in start_menu_paths:
                if not os.path.exists(base_path):
                    continue

                for root, dirs, files in os.walk(base_path):
                    for file in files:
                        if file.lower().endswith('.lnk') or file.lower().endswith('.exe'):
                            file_lower = file.lower()

                            # Check if ANY search word is in the filename
                            # OR if the entire app_name is a substring
                            match = False
                            if app_name.lower() in file_lower:
                                match = True
                            else:
                                # Check if any word from search matches
                                for word in search_words:
                                    if len(word) > 2 and word in file_lower:
                                        match = True
                                        break

                            if match:
                                # Extract clean name
                                clean_name = file.replace('.lnk', '').replace('.exe', '')
                                matches.append({
                                    'name': clean_name,
                                    'path': os.path.join(root, file),
                                    'method': 'start_menu'
                                })

            return matches

        except Exception as e:
            self.logger.warning(f"Start menu search failed: {e}")
            return []
    
    def _search_in_paths_all(self, app_name: str) -> List[Dict[str, Any]]:
        """Search in common installation paths and return ALL matches."""
        matches = []
        try:
            # Split app_name into words for better matching
            search_words = app_name.lower().split()

            for base_path in self.search_paths:
                if not os.path.exists(base_path):
                    continue

                # Search only top 2 levels to avoid deep recursion
                for root, dirs, files in os.walk(base_path):
                    # Limit depth
                    depth = root[len(base_path):].count(os.sep)
                    if depth > 2:
                        continue

                    for file in files:
                        if file.lower().endswith('.exe'):
                            file_lower = file.lower()

                            # Check if ANY search word is in the filename
                            # OR if the entire app_name is a substring
                            match = False
                            if app_name.lower() in file_lower:
                                match = True
                            else:
                                # Check if any word from search matches
                                for word in search_words:
                                    if len(word) > 2 and word in file_lower:
                                        match = True
                                        break

                            if match:
                                # Extract clean name
                                clean_name = file.replace('.exe', '')
                                matches.append({
                                    'name': clean_name,
                                    'path': os.path.join(root, file),
                                    'method': 'file_search'
                                })

            return matches

        except Exception as e:
            self.logger.warning(f"Path search failed: {e}")
            return []
    
    def _windows_search(self, app_name: str) -> Optional[str]:
        """Use Windows Search by simulating Win+S and typing."""
        try:
            self.logger.info(f"Using Windows Search for: {app_name}")
            
            # Press Windows key + S to open search
            pyautogui.hotkey('win', 's')
            time.sleep(1)
            
            # Type the application name
            pyautogui.write(app_name, interval=0.1)
            time.sleep(2)
            
            # Take screenshot to check if results appeared
            # For now, we'll just return None and let other methods handle it
            # In a full implementation, we could use OCR to read search results
            
            # Close search (press Escape)
            pyautogui.press('escape')
            
            return None
        
        except Exception as e:
            self.logger.warning(f"Windows search failed: {e}")
            return None
    
    def _search_windows_apps(self, app_name: str) -> List[Dict[str, Any]]:
        """Search for Windows Store/UWP apps."""
        matches = []
        try:
            # Split app_name into words for better matching
            search_words = app_name.lower().split()

            # Windows Apps are in WindowsApps folder
            windows_apps_path = os.path.expanduser(r'~\AppData\Local\Microsoft\WindowsApps')

            if os.path.exists(windows_apps_path):
                for file in os.listdir(windows_apps_path):
                    if file.lower().endswith('.exe'):
                        file_lower = file.lower()

                        # Check if ANY search word is in the filename
                        # OR if the entire app_name is a substring
                        match = False
                        if app_name.lower() in file_lower:
                            match = True
                        else:
                            # Check if any word from search matches
                            for word in search_words:
                                if len(word) > 2 and word in file_lower:
                                    match = True
                                    break

                        if match:
                            # Extract clean name
                            clean_name = file.replace('.exe', '')
                            # Make it more readable (remove package names)
                            if '!' in clean_name:
                                clean_name = clean_name.split('!')[-1]

                            matches.append({
                                'name': clean_name,
                                'path': os.path.join(windows_apps_path, file),
                                'method': 'windows_apps'
                            })

            return matches

        except Exception as e:
            self.logger.warning(f"Windows Apps search failed: {e}")
            return []

    def _search_registry_all(self, app_name: str) -> List[Dict[str, Any]]:
        """Search in Windows Registry for installed applications and return ALL matches."""
        matches = []
        try:
            # Split app_name into words for better matching
            search_words = app_name.lower().split()

            registry_paths = [
                r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths',
                r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall',
                r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'
            ]

            for reg_path in registry_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)

                    # Enumerate subkeys
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey_lower = subkey_name.lower()

                            # Check if ANY search word is in the subkey name
                            # OR if the entire app_name is a substring
                            match = False
                            if app_name.lower() in subkey_lower:
                                match = True
                            else:
                                # Check if any word from search matches
                                for word in search_words:
                                    if len(word) > 2 and word in subkey_lower:
                                        match = True
                                        break

                            if match:
                                # Try to get the path
                                subkey = winreg.OpenKey(key, subkey_name)
                                try:
                                    path = winreg.QueryValue(subkey, None)
                                    path = path.strip('"').strip("'")
                                    winreg.CloseKey(subkey)
                                    if path and os.path.exists(path):
                                        # Extract clean name
                                        clean_name = subkey_name.replace('.exe', '')
                                        matches.append({
                                            'name': clean_name,
                                            'path': path,
                                            'method': 'registry'
                                        })
                                except:
                                    pass
                            i += 1
                        except OSError:
                            break

                    winreg.CloseKey(key)

                except WindowsError:
                    continue

            return matches

        except Exception as e:
            self.logger.warning(f"Registry search failed: {e}")
            return []
    
    def _handle_multiple_matches(self, app_name: str, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle case when multiple applications are found."""
        try:
            if not self.voice_processor:
                # No voice processor - return first match
                return {
                    'status': 'found',
                    'method': matches[0]['method'],
                    'app_name': app_name,
                    'path': matches[0]['path'],
                    'name': matches[0]['name'],
                    'message': f'Found {matches[0]["name"]}'
                }

            # Ask user which one to open
            app_names = [m['name'] for m in matches]

            if len(app_names) == 2:
                message = f"Lucky, I found {app_names[0]} and {app_names[1]}. Which one would you like me to open?"
            elif len(app_names) == 3:
                message = f"Lucky, I found {app_names[0]}, {app_names[1]}, and {app_names[2]}. Which one would you like me to open?"
            else:
                # More than 3 - list first 3 and say "and X more"
                first_three = ", ".join(app_names[:3])
                remaining = len(app_names) - 3
                message = f"Lucky, I found {first_three}, and {remaining} more. Which one would you like me to open?"

            self.logger.info(f"Asking user: {message}")
            self.voice_processor.speak(message)

            # Listen for response
            response = self.voice_processor.listen_once(timeout=20, phrase_time_limit=10)

            if response:
                response_lower = response.lower()
                self.logger.info(f"User response: {response}")

                # Try to match response to one of the apps
                for match in matches:
                    match_name_lower = match['name'].lower()
                    # Check if any word from the app name is in the response
                    name_words = match_name_lower.split()
                    if any(word in response_lower for word in name_words if len(word) > 2):
                        return {
                            'status': 'found',
                            'method': match['method'],
                            'app_name': app_name,
                            'path': match['path'],
                            'name': match['name'],
                            'message': f'Found {match["name"]}'
                        }

                # No match found - return first one
                self.voice_processor.speak(f"I didn't catch that. Opening {matches[0]['name']}.")
                return {
                    'status': 'found',
                    'method': matches[0]['method'],
                    'app_name': app_name,
                    'path': matches[0]['path'],
                    'name': matches[0]['name'],
                    'message': f'Found {matches[0]["name"]}'
                }
            else:
                # No response - return first match
                return {
                    'status': 'found',
                    'method': matches[0]['method'],
                    'app_name': app_name,
                    'path': matches[0]['path'],
                    'name': matches[0]['name'],
                    'message': f'Found {matches[0]["name"]}'
                }

        except Exception as e:
            self.logger.error(f"Error handling multiple matches: {e}")
            # Return first match on error
            return {
                'status': 'found',
                'method': matches[0]['method'],
                'app_name': app_name,
                'path': matches[0]['path'],
                'name': matches[0]['name'],
                'message': f'Found {matches[0]["name"]}'
            }

    def _handle_not_found(self, app_name: str) -> Dict[str, Any]:
        """Handle case when application is not found."""
        try:
            # Ask user if they want to download it
            if self.voice_processor:
                message = f"Lucky, I didn't find {app_name} in your system. Would you like me to open it in a browser so you can download it?"

                self.logger.info(f"Asking user: {message}")
                self.voice_processor.speak(message)
                
                # Listen for response
                response = self.voice_processor.listen_once(timeout=15, phrase_time_limit=10)
                
                if response:
                    response_lower = response.lower()
                    self.logger.info(f"User response: {response}")
                    
                    # Check if user wants to download
                    if any(word in response_lower for word in ['yes', 'yeah', 'sure', 'ok', 'okay', 'haan', 'download']):
                        # Get download URL
                        download_url = self._get_download_url(app_name)
                        
                        if download_url:
                            return {
                                'status': 'not_found',
                                'action': 'download',
                                'app_name': app_name,
                                'download_url': download_url,
                                'message': f'{app_name} not found. Opening download page.'
                            }
                        else:
                            # Search on Google
                            search_url = f"https://www.google.com/search?q=download+{app_name.replace(' ', '+')}"
                            return {
                                'status': 'not_found',
                                'action': 'search',
                                'app_name': app_name,
                                'search_url': search_url,
                                'message': f'{app_name} not found. Searching on Google.'
                            }
                    else:
                        return {
                            'status': 'not_found',
                            'action': 'cancelled',
                            'app_name': app_name,
                            'message': f'{app_name} not found. User declined download.'
                        }
            
            # No voice processor - just return not found
            return {
                'status': 'not_found',
                'action': 'none',
                'app_name': app_name,
                'message': f'{app_name} not found in system'
            }
        
        except Exception as e:
            self.logger.error(f"Error handling not found: {e}")
            return {
                'status': 'not_found',
                'action': 'error',
                'app_name': app_name,
                'message': f'Error: {str(e)}'
            }
    
    def _get_download_url(self, app_name: str) -> Optional[str]:
        """Get download URL for common applications."""
        app_name_lower = app_name.lower()
        
        # Check if we have a known download URL
        for key, url in self.download_urls.items():
            if key in app_name_lower or app_name_lower in key:
                return url
        
        return None
    
    def is_application_open(self, app_name: str) -> bool:
        """
        Check if an application is already open using Task View (Win+Tab).

        Args:
            app_name: Name of the application to check

        Returns:
            True if application is open, False otherwise
        """
        try:
            import pyautogui
            import time

            self.logger.info(f"Checking if {app_name} is already open using Task View")

            # Open Task View (Win+Tab)
            pyautogui.hotkey('win', 'tab')
            time.sleep(1.5)  # Wait for Task View to open

            # Take screenshot of Task View
            screenshot = pyautogui.screenshot()

            # Close Task View
            pyautogui.press('escape')
            time.sleep(0.5)

            # Use OCR to read text from screenshot
            try:
                import pytesseract

                # Get all text from screenshot
                text = pytesseract.image_to_string(screenshot)

                # Normalize app name for comparison
                app_name_lower = app_name.lower()
                text_lower = text.lower()

                # Check if app name is in the text
                if app_name_lower in text_lower:
                    self.logger.info(f"Found '{app_name}' in Task View")
                    return True

                # Also check for common variations
                # e.g., "word" -> "microsoft word", "chrome" -> "google chrome"
                app_variations = {
                    'word': ['microsoft word', 'word'],
                    'powerpoint': ['microsoft powerpoint', 'powerpoint'],
                    'excel': ['microsoft excel', 'excel'],
                    'chrome': ['google chrome', 'chrome'],
                    'edge': ['microsoft edge', 'edge'],
                    'dolby': ['dolby access', 'dolby atmos', 'dolby'],
                }

                if app_name_lower in app_variations:
                    for variation in app_variations[app_name_lower]:
                        if variation in text_lower:
                            self.logger.info(f"Found '{variation}' in Task View (variation of {app_name})")
                            return True

                self.logger.info(f"'{app_name}' not found in Task View")
                return False

            except Exception as ocr_error:
                self.logger.warning(f"OCR failed, falling back to pygetwindow: {ocr_error}")

                # Fallback to pygetwindow method
                import pygetwindow as gw

                # Get all window titles
                all_windows = gw.getAllTitles()

                # Normalize app name for comparison
                app_name_lower = app_name.lower()

                # Check if any window title contains the app name
                for window_title in all_windows:
                    if not window_title.strip():
                        continue

                    window_title_lower = window_title.lower()

                    # Check for match
                    if app_name_lower in window_title_lower or window_title_lower in app_name_lower:
                        self.logger.info(f"Found open window: {window_title}")
                        return True

                return False

        except Exception as e:
            self.logger.error(f"Error checking if application is open: {e}")
            return False

    def open_application(self, path: str, app_name: str = None) -> Dict[str, Any]:
        """
        Open an application by path.
        Checks if application is already open first.

        Args:
            path: Path to the application
            app_name: Name of the application (for checking if already open)

        Returns:
            Result dictionary
        """
        try:
            # Check if application is already open
            if app_name and self.is_application_open(app_name):
                self.logger.info(f"{app_name} is already open")

                if self.voice_processor:
                    self.voice_processor.speak(f"Lucky, {app_name} is already open.")

                return {
                    'status': 'already_open',
                    'message': f'{app_name} is already open'
                }

            self.logger.info(f"Opening application: {path}")

            # Check if it's a URI protocol (for built-in Windows apps)
            if path.startswith('ms-') or path.endswith(':'):
                self.logger.info(f"Opening URI protocol: {path}")
                os.startfile(path)
            elif path.endswith('.lnk'):
                # Open shortcut
                os.startfile(path)
            else:
                # Open executable
                subprocess.Popen([path])

            return {
                'status': 'completed',
                'message': f'Opened application'
            }

        except Exception as e:
            self.logger.error(f"Error opening application: {e}")
            return {
                'status': 'failed',
                'message': f'Failed to open application: {str(e)}'
            }



