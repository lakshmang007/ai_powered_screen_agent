"""
Browser Detection and Selection Handler.
Detects installed browsers and asks user which one to use.
"""

import logging
import os
import winreg
from typing import List, Dict, Any, Optional


class BrowserDetector:
    """Detects installed browsers on Windows."""
    
    def __init__(self, voice_processor=None):
        """
        Initialize browser detector.
        
        Args:
            voice_processor: Voice processor for asking user
        """
        self.voice_processor = voice_processor
        self.logger = logging.getLogger(__name__)
        
        # Common browser paths and registry keys
        self.browser_info = {
            'chrome': {
                'name': 'Google Chrome',
                'executable': 'chrome.exe',
                'paths': [
                    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                    os.path.expanduser(r'~\AppData\Local\Google\Chrome\Application\chrome.exe')
                ],
                'registry_key': r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe',
                'command': 'chrome'
            },
            'firefox': {
                'name': 'Mozilla Firefox',
                'executable': 'firefox.exe',
                'paths': [
                    r'C:\Program Files\Mozilla Firefox\firefox.exe',
                    r'C:\Program Files (x86)\Mozilla Firefox\firefox.exe'
                ],
                'registry_key': r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe',
                'command': 'firefox'
            },
            'edge': {
                'name': 'Microsoft Edge',
                'executable': 'msedge.exe',
                'paths': [
                    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe'
                ],
                'registry_key': r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe',
                'command': 'msedge'
            },
            'opera': {
                'name': 'Opera',
                'executable': 'opera.exe',
                'paths': [
                    r'C:\Program Files\Opera\launcher.exe',
                    r'C:\Program Files (x86)\Opera\launcher.exe',
                    os.path.expanduser(r'~\AppData\Local\Programs\Opera\launcher.exe'),
                    os.path.expanduser(r'~\AppData\Local\Programs\Opera GX\opera.exe')
                ],
                'registry_key': r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\opera.exe',
                'command': 'opera'
            },
            'brave': {
                'name': 'Brave',
                'executable': 'brave.exe',
                'paths': [
                    r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
                    r'C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe',
                    os.path.expanduser(r'~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe')
                ],
                'registry_key': r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\brave.exe',
                'command': 'brave'
            }
        }
    
    def detect_installed_browsers(self) -> List[Dict[str, Any]]:
        """
        Detect all installed browsers.
        
        Returns:
            List of installed browser dictionaries
        """
        installed = []
        
        for browser_id, info in self.browser_info.items():
            if self._is_browser_installed(browser_id):
                installed.append({
                    'id': browser_id,
                    'name': info['name'],
                    'command': info['command'],
                    'path': self._get_browser_path(browser_id)
                })
                self.logger.info(f"Detected browser: {info['name']}")
        
        return installed
    
    def _is_browser_installed(self, browser_id: str) -> bool:
        """
        Check if a specific browser is installed.
        
        Args:
            browser_id: Browser identifier (chrome, firefox, etc.)
            
        Returns:
            True if browser is installed
        """
        info = self.browser_info.get(browser_id)
        if not info:
            return False
        
        # Check common paths
        for path in info['paths']:
            if os.path.exists(path):
                return True
        
        # Check registry
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, info['registry_key'])
            winreg.CloseKey(key)
            return True
        except WindowsError:
            pass
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, info['registry_key'])
            winreg.CloseKey(key)
            return True
        except WindowsError:
            pass
        
        return False
    
    def _get_browser_path(self, browser_id: str) -> Optional[str]:
        """
        Get the installation path of a browser.

        Args:
            browser_id: Browser identifier

        Returns:
            Path to browser executable or None
        """
        info = self.browser_info.get(browser_id)
        if not info:
            return None

        # Check common paths
        for path in info['paths']:
            if os.path.exists(path):
                return path

        # Check registry - HKEY_LOCAL_MACHINE
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, info['registry_key'])
            path = winreg.QueryValue(key, None)
            winreg.CloseKey(key)
            if path:
                # Remove quotes if present
                path = path.strip('"').strip("'")
                if os.path.exists(path):
                    return path
        except (WindowsError, OSError):
            pass

        # Check registry - HKEY_CURRENT_USER
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, info['registry_key'])
            path = winreg.QueryValue(key, None)
            winreg.CloseKey(key)
            if path:
                # Remove quotes if present
                path = path.strip('"').strip("'")
                if os.path.exists(path):
                    return path
        except (WindowsError, OSError):
            pass

        return None
    
    def ask_browser_choice(self, installed_browsers: List[Dict[str, Any]]) -> Optional[str]:
        """
        Ask user which browser to use via voice.
        
        Args:
            installed_browsers: List of installed browsers
            
        Returns:
            Selected browser ID or None
        """
        if not installed_browsers:
            self.logger.warning("No browsers detected")
            return None
        
        # If only one browser, use it
        if len(installed_browsers) == 1:
            browser = installed_browsers[0]
            self.logger.info(f"Only one browser found: {browser['name']}")
            return browser['id']
        
        # Ask user which browser to use
        if self.voice_processor:
            try:
                # Build message
                browser_names = [b['name'] for b in installed_browsers]
                
                if len(browser_names) == 2:
                    message = f"I can see {browser_names[0]} and {browser_names[1]}. Which one would you like me to use?"
                else:
                    names_str = ", ".join(browser_names[:-1]) + f", and {browser_names[-1]}"
                    message = f"I can see {len(browser_names)} browsers: {names_str}. Which one would you like me to use?"
                
                self.logger.info(f"Asking user: {message}")
                self.voice_processor.speak(message)
                
                # Listen for response
                response = self.voice_processor.listen_once(timeout=15, phrase_time_limit=10)
                
                if response:
                    response_lower = response.lower()
                    self.logger.info(f"User response: {response}")
                    
                    # Match response to browser
                    for browser in installed_browsers:
                        browser_id = browser['id']
                        browser_name = browser['name'].lower()
                        
                        if browser_id in response_lower or browser_name in response_lower:
                            self.logger.info(f"Selected browser: {browser['name']}")
                            return browser_id
                    
                    # If no match, try partial matches
                    if 'chrome' in response_lower and any(b['id'] == 'chrome' for b in installed_browsers):
                        return 'chrome'
                    elif 'firefox' in response_lower and any(b['id'] == 'firefox' for b in installed_browsers):
                        return 'firefox'
                    elif 'edge' in response_lower and any(b['id'] == 'edge' for b in installed_browsers):
                        return 'edge'
                    elif 'opera' in response_lower and any(b['id'] == 'opera' for b in installed_browsers):
                        return 'opera'
                    elif 'brave' in response_lower and any(b['id'] == 'brave' for b in installed_browsers):
                        return 'brave'
                
            except Exception as e:
                self.logger.error(f"Error asking for browser choice: {e}")
        
        # Default to first browser if no voice processor or error
        default_browser = installed_browsers[0]
        self.logger.info(f"Using default browser: {default_browser['name']}")
        return default_browser['id']
    
    def get_browser_command(self, browser_id: str) -> str:
        """
        Get the command to launch a browser.
        
        Args:
            browser_id: Browser identifier
            
        Returns:
            Command string
        """
        info = self.browser_info.get(browser_id)
        if info:
            return info['command']
        return 'chrome'  # Default

