#!/usr/bin/env python3
"""
Smart App Opener - Intelligently opens apps by checking taskbar first
"""

import logging
import re
import subprocess
import time
import webbrowser
from typing import Optional, Dict, Any, Tuple

try:
    import pygetwindow as gw
    HAS_PYGETWINDOW = True
except ImportError:
    HAS_PYGETWINDOW = False
    gw = None

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False
    pyautogui = None


class SmartAppOpener:
    """Smart application opener with taskbar checking."""

    SYSTEM_WINDOW_TITLES = {
        'Windows Input Experience', 'Program Manager', 'Microsoft Text Input Application',
        'Windows Shell Experience Host', 'Start', 'Search', 'Task Switching', 'Task View',
        'NVIDIA GeForce Overlay', 'Default IME', 'MSCTFIME UI',
    }

    def __init__(self, voice_processor=None, system_search_handler=None):
        """
        Initialize smart app opener.
        
        Args:
            voice_processor: Voice processor for speaking
            system_search_handler: System search handler for finding apps
        """
        self.logger = logging.getLogger(__name__)
        self.voice_processor = voice_processor
        self.system_search_handler = system_search_handler
        
        # Common web URLs for apps
        self.web_urls = {
            'chatgpt': 'https://chat.openai.com',
            'chat gpt': 'https://chat.openai.com',
            'openai': 'https://chat.openai.com',
            'claude': 'https://claude.ai',
            'gemini': 'https://gemini.google.com',
            'bard': 'https://gemini.google.com',
            'gmail': 'https://mail.google.com',
            'youtube': 'https://youtube.com',
            'twitter': 'https://twitter.com',
            'x': 'https://x.com',
            'facebook': 'https://facebook.com',
            'instagram': 'https://instagram.com',
            'linkedin': 'https://linkedin.com',
            'github': 'https://github.com',
            'stackoverflow': 'https://stackoverflow.com',
            'reddit': 'https://reddit.com',
            'netflix': 'https://netflix.com',
            'spotify': 'https://open.spotify.com',
            'discord': 'https://discord.com/app',
            'slack': 'https://slack.com',
            'notion': 'https://notion.so',
            'figma': 'https://figma.com',
            'canva': 'https://canva.com',
        }
    
    @staticmethod
    def _name_matches(key: str, name: str) -> bool:
        """Whole-word match, so 'x' doesn't match 'excel' and 'word' doesn't match 'wordpad'."""
        return re.search(rf'\b{re.escape(key)}\b', name) is not None

    def _listen(self, timeout: int = 10) -> Optional[str]:
        """Listen for a short answer with whichever API the voice processor offers."""
        vp = self.voice_processor
        if vp is None:
            return None
        try:
            if hasattr(vp, 'listen_once'):
                try:
                    return vp.listen_once(timeout=timeout, phrase_time_limit=10)
                except TypeError:
                    return vp.listen_once()
            if hasattr(vp, 'listen'):
                return vp.listen(timeout=timeout)
        except Exception as e:
            self.logger.error(f"Listening failed: {e}")
        return None

    def open_app_smart(self, app_name: str, force_windows_search: bool = False) -> Dict[str, Any]:
        """
        Smart app opening with taskbar checking.
        
        Steps:
        1. Check if app is already running (in taskbar)
        2. If running but minimized, bring to front
        3. If not running, check if installed
        4. If not installed, ask to open in browser
        
        Args:
            app_name: Name of the application
            force_windows_search: Whether to force using Windows Search
            
        Returns:
            Result dictionary
        """
        self.logger.info(f"Smart opening: {app_name} (Force Windows Search: {force_windows_search})")
        
        # Step 1: Check if already running
        running_result = self.check_if_running(app_name)
        
        if running_result['is_running']:
            # App is running, bring to front
            self.logger.info(f"{app_name} is already running, bringing to front")
            
            if self.voice_processor:
                self.voice_processor.speak(f"{app_name} is already open, bringing it to front")
            
            return self.bring_to_front(running_result['window'])
        
        # Step 2: Try protocol opening (Priority for UWP apps like Dolby Access)
        if 'dolby' in app_name.lower() and not force_windows_search:
            self.logger.info(f"Attempting to open {app_name} via protocol")
            try:
                subprocess.Popen('start dolbyaccess:', shell=True)
                if self.voice_processor:
                    self.voice_processor.speak(f"Opening {app_name}")
                return {'status': 'completed', 'message': f'Opened {app_name} via protocol'}
            except Exception as e:
                self.logger.error(f"Protocol open failed: {e}")

        # Step 3: App not running, check if installed
        self.logger.info(f"{app_name} not running, checking if installed")
        
        if self.system_search_handler:
            search_result = self.system_search_handler.search_application(app_name, force_windows_search=force_windows_search)
            
            if search_result.get('status') == 'found':
                # App is installed, open it
                # If it was found via Windows Search vision, it's already opened
                if search_result.get('method') == 'windows_search':
                    return {
                        'status': 'completed',
                        'message': search_result.get('message', f'Opened {app_name}')
                    }
                
                self.logger.info(f"{app_name} found installed, opening")
                
                if self.voice_processor:
                    self.voice_processor.speak(f"Opening {app_name}")
                
                return self.system_search_handler.open_application(
                    search_result['path'],
                    app_name
                )

            # The user already agreed to open a download / search page
            offered_url = search_result.get('download_url') or search_result.get('search_url')
            if offered_url:
                return self.open_in_browser(app_name, offered_url)
            if search_result.get('action') == 'cancelled':
                return {'status': 'cancelled', 'message': search_result.get('message', 'User cancelled')}

        # Step 4: App not installed, ask to open in browser
        self.logger.info(f"{app_name} not installed, asking to open in browser")
        
        return self.ask_open_in_browser(app_name)
    
    def check_if_running(self, app_name: str) -> Dict[str, Any]:
        """
        Check if application is running in taskbar.
        
        Args:
            app_name: Name of the application
            
        Returns:
            Dictionary with is_running and window info
        """
        if not HAS_PYGETWINDOW:
            return {'is_running': False, 'window': None}
        
        try:
            # Get all windows
            all_windows = gw.getAllTitles()
            app_name_lower = app_name.lower()

            # Phonetic corrections
            corrections = {
                "dolby axis": "dolby access",
                "dolby axes": "dolby access",
                "dolby excess": "dolby access"
            }
            for wrong, right in corrections.items():
                if wrong in app_name_lower:
                    app_name_lower = app_name_lower.replace(wrong, right)
            
            # Common aliases for better matching
            aliases = {
                'code': 'visual studio code',
                'vscode': 'visual studio code',
                'chrome': 'google chrome',
                'edge': 'microsoft edge',
                'word': 'word',
                'excel': 'excel',
                'powerpoint': 'powerpoint',
                'notepad': 'notepad',
                'terminal': 'cmd',
                'command prompt': 'cmd',
                'explorer': 'file explorer',
                'dolby access': 'dolby access',
                'dolby': 'dolby access'
            }
            
            search_terms = [app_name_lower]
            if app_name_lower in aliases:
                search_terms.append(aliases[app_name_lower])
            
            # Check each window
            for window_title in all_windows:
                # Skip blank titles and invisible shell/system windows that would
                # otherwise "match" (e.g. 'open windows' -> Windows Input Experience)
                if not window_title.strip() or window_title.strip() in self.SYSTEM_WINDOW_TITLES:
                    continue
                
                window_title_lower = window_title.lower()
                
                # Check for match with any search term (whole words only)
                for term in search_terms:
                    if self._name_matches(term, window_title_lower):
                        # Found matching window
                        windows = gw.getWindowsWithTitle(window_title)
                        if windows:
                            self.logger.info(f"Found running window: {window_title} (matched '{term}')")
                            return {
                                'is_running': True,
                                'window': windows[0],
                                'title': window_title
                            }
            
            return {'is_running': False, 'window': None}

        except Exception as e:
            self.logger.error(f"Error checking if running: {e}")
            return {'is_running': False, 'window': None}

    def bring_to_front(self, window) -> Dict[str, Any]:
        """
        Bring a window to front with robust handling.

        Args:
            window: pygetwindow Window object

        Returns:
            Result dictionary
        """
        try:
            self.logger.info(f"Attempting to bring {window.title} to front")
            
            # 1. Restore if minimized
            if window.isMinimized:
                window.restore()
                time.sleep(0.2)

            # 2. Try standard activation
            try:
                window.activate()
            except Exception as e:
                self.logger.warning(f"Standard activation failed: {e}. Trying force method.")
                
                # 3. Force method: Minimize then Restore (often bypasses focus lock)
                try:
                    window.minimize()
                    time.sleep(0.1)
                    window.restore()
                    time.sleep(0.2)
                    window.activate()
                except Exception as e2:
                    self.logger.error(f"Force activation failed: {e2}")

            # 4. Ensure visibility
            if window.isMaximized:
                window.maximize()

            self.logger.info(f"Brought window to front: {window.title}")

            return {
                'status': 'completed',
                'message': f'Brought {window.title} to front'
            }

        except Exception as e:
            self.logger.error(f"Error bringing window to front: {e}")
            return {
                'status': 'failed',
                'message': f'Failed to bring window to front: {str(e)}'
            }

    def ask_open_in_browser(self, app_name: str) -> Dict[str, Any]:
        """
        Ask user if they want to open app in browser.

        Args:
            app_name: Name of the application

        Returns:
            Result dictionary
        """
        try:
            # Check if we have a web URL for this app
            app_name_lower = app_name.lower()
            web_url = None

            for key, url in self.web_urls.items():
                if key == app_name_lower or self._name_matches(key, app_name_lower):
                    web_url = url
                    break

            if not web_url:
                # No known web URL
                self.logger.info(f"No web URL known for {app_name}")

                if self.voice_processor:
                    self.voice_processor.speak(f"I couldn't find {app_name} installed on your system.")

                return {
                    'status': 'not_found',
                    'message': f'{app_name} not found'
                }

            # Ask user if they want to open in browser
            if self.voice_processor:
                self.voice_processor.speak(
                    f"I couldn't find {app_name} installed. Should I open it in your browser?"
                )

                # Listen for response
                response = self._listen(timeout=10)

                if response:
                    response_lower = response.lower()

                    # Check for positive response
                    if any(self._name_matches(word, response_lower) for word in ['yes', 'yeah', 'sure', 'ok', 'okay', 'open', 'go ahead', 'haan']):
                        # Ask which browser
                        return self.open_in_browser(app_name, web_url)
                    else:
                        self.voice_processor.speak("Okay, no problem!")
                        return {
                            'status': 'cancelled',
                            'message': 'User cancelled'
                        }

            # No voice processor, just open in default browser
            return self.open_in_browser(app_name, web_url)

        except Exception as e:
            self.logger.error(f"Error asking to open in browser: {e}")
            return {
                'status': 'error',
                'message': f'Error: {str(e)}'
            }

    def open_in_browser(self, app_name: str, url: str) -> Dict[str, Any]:
        """
        Open app in browser.

        Args:
            app_name: Name of the application
            url: URL to open

        Returns:
            Result dictionary
        """
        try:
            # Ask which browser if voice processor available; None = system default
            browser = None

            if self.voice_processor:
                self.voice_processor.speak("Which browser? Chrome, Firefox, or Edge?")

                response = self._listen(timeout=10)

                if response:
                    response_lower = response.lower()

                    if 'firefox' in response_lower:
                        browser = 'firefox'
                    elif 'edge' in response_lower:
                        browser = 'msedge'
                    elif 'chrome' in response_lower:
                        browser = 'chrome'

            # Open in browser
            browser_label = browser or 'your default browser'
            self.logger.info(f"Opening {app_name} in {browser_label}: {url}")

            if browser:
                # Quote the URL so '&' in query strings isn't parsed by cmd
                subprocess.Popen(f'start "" {browser} "{url}"', shell=True)
            else:
                webbrowser.open(url)

            if self.voice_processor:
                self.voice_processor.speak(f"Opening {app_name} in {browser_label}")

            return {
                'status': 'completed',
                'message': f'Opened {app_name} in {browser_label}'
            }

        except Exception as e:
            self.logger.error(f"Error opening in browser: {e}")
            return {
                'status': 'failed',
                'message': f'Failed to open in browser: {str(e)}'
            }

