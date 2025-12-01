"""
Intelligent Assistant with Follow-up Questions

This module adds intelligence to Byte by asking clarifying questions
when commands are ambiguous or need more information.
"""

import logging
from typing import Optional, Dict, List, Tuple
import os
import subprocess


class IntelligentAssistant:
    """
    Intelligent assistant that asks follow-up questions for ambiguous commands.
    """
    
    def __init__(self, voice_processor, nlp_processor):
        """
        Initialize intelligent assistant.
        
        Args:
            voice_processor: Voice processor for speaking and listening
            nlp_processor: NLP processor for understanding commands
        """
        self.voice = voice_processor
        self.nlp = nlp_processor
        self.logger = logging.getLogger(__name__)
        
        # Known applications and their paths
        self.known_apps = self._discover_applications()
    
    def _discover_applications(self) -> Dict[str, str]:
        """Discover installed applications on the system."""
        apps = {}
        
        # Common application paths
        common_paths = [
            r"C:\Program Files",
            r"C:\Program Files (x86)",
            os.path.expanduser("~\\AppData\\Local"),
            os.path.expanduser("~\\AppData\\Roaming"),
        ]
        
        # Common applications to look for
        app_patterns = {
            "dolby": ["Dolby", "DolbyAtmos", "Dolby Atmos"],
            "chrome": ["Google\\Chrome", "Chrome"],
            "firefox": ["Mozilla Firefox", "Firefox"],
            "edge": ["Microsoft\\Edge", "Edge"],
            "vscode": ["Microsoft VS Code", "VSCode", "Code"],
            "spotify": ["Spotify"],
            "discord": ["Discord"],
            "slack": ["Slack"],
            "zoom": ["Zoom"],
        }
        
        # Search for applications
        for base_path in common_paths:
            if not os.path.exists(base_path):
                continue
            
            try:
                for item in os.listdir(base_path):
                    item_lower = item.lower()
                    for app_name, patterns in app_patterns.items():
                        for pattern in patterns:
                            if pattern.lower() in item_lower:
                                full_path = os.path.join(base_path, item)
                                if os.path.isdir(full_path):
                                    # Look for .exe files
                                    for root, dirs, files in os.walk(full_path):
                                        for file in files:
                                            if file.endswith('.exe'):
                                                apps[app_name] = os.path.join(root, file)
                                                break
                                        if app_name in apps:
                                            break
            except (PermissionError, OSError):
                continue
        
        return apps
    
    def check_application_exists(self, app_name: str) -> Tuple[bool, Optional[str]]:
        """
        Check if an application exists on the system.
        
        Args:
            app_name: Name of the application
            
        Returns:
            Tuple of (exists, path)
        """
        app_lower = app_name.lower()
        
        # Check known apps
        for known_app, path in self.known_apps.items():
            if known_app in app_lower or app_lower in known_app:
                return True, path
        
        return False, None
    
    def ask_follow_up_question(self, question: str, options: List[str] = None) -> Optional[str]:
        """
        Ask a follow-up question and get response.
        
        Args:
            question: Question to ask
            options: Optional list of expected responses
            
        Returns:
            User's response or None
        """
        print(f"\n🤖 Byte: {question}")
        self.voice.speak(question)
        
        if options:
            print(f"   Options: {', '.join(options)}")
        
        print("🎤 Listening for your answer...")
        response = self.voice.listen_once(timeout=15, phrase_time_limit=20)
        
        if response:
            print(f"📝 You said: {response}")
            return response.lower().strip()
        
        return None
    
    def handle_ambiguous_open_command(self, app_name: str) -> Dict:
        """
        Handle ambiguous 'open' commands by asking follow-up questions.
        
        Args:
            app_name: Name of the application to open
            
        Returns:
            Dict with action details
        """
        # Check if app exists locally
        exists, app_path = self.check_application_exists(app_name)
        
        if exists:
            # App found locally
            question = f"I found {app_name} installed on your system. Should I open it?"
            response = self.ask_follow_up_question(question, ["yes", "no", "browser"])
            
            if response and ("yes" in response or "open" in response or "haan" in response):
                return {
                    "action": "open_local",
                    "app_name": app_name,
                    "app_path": app_path
                }
            elif response and ("browser" in response or "web" in response):
                # Ask which browser
                return self._ask_browser_choice(app_name)
        else:
            # App not found locally
            question = f"I couldn't find {app_name} installed. Should I open it in a browser?"
            response = self.ask_follow_up_question(question, ["yes", "no"])
            
            if response and ("yes" in response or "browser" in response or "haan" in response):
                return self._ask_browser_choice(app_name)
            else:
                return {"action": "cancel", "message": f"{app_name} not found and user declined browser"}
        
        return {"action": "cancel", "message": "User cancelled"}
    
    def _ask_browser_choice(self, app_name: str) -> Dict:
        """Ask which browser to use."""
        question = "Which browser should I use? Chrome, Firefox, or Edge?"
        response = self.ask_follow_up_question(question, ["chrome", "firefox", "edge"])
        
        browser = "chrome"  # Default
        if response:
            if "firefox" in response:
                browser = "firefox"
            elif "edge" in response:
                browser = "edge"
            elif "chrome" in response:
                browser = "chrome"
        
        return {
            "action": "open_browser",
            "app_name": app_name,
            "browser": browser,
            "url": self._get_web_url(app_name)
        }
    
    def _get_web_url(self, app_name: str) -> str:
        """Get web URL for an application."""
        urls = {
            "gmail": "https://mail.google.com",
            "github": "https://github.com",
            "linkedin": "https://linkedin.com",
            "twitter": "https://twitter.com",
            "facebook": "https://facebook.com",
            "youtube": "https://youtube.com",
            "netflix": "https://netflix.com",
            "spotify": "https://open.spotify.com",
            "dolby": "https://www.dolby.com",
            "dolby atmos": "https://www.dolby.com/technologies/dolby-atmos",
        }
        
        app_lower = app_name.lower()
        for key, url in urls.items():
            if key in app_lower or app_lower in key:
                return url
        
        # Default: search Google
        return f"https://www.google.com/search?q={app_name.replace(' ', '+')}"
    
    def handle_search_command(self, query: str) -> Dict:
        """
        Handle search commands with follow-up questions.
        
        Args:
            query: Search query
            
        Returns:
            Dict with action details
        """
        # Ask which search engine
        question = "Which search engine? Google, Bing, or DuckDuckGo?"
        response = self.ask_follow_up_question(question, ["google", "bing", "duckduckgo"])
        
        engine = "google"  # Default
        if response:
            if "bing" in response:
                engine = "bing"
            elif "duck" in response:
                engine = "duckduckgo"
        
        # Ask which browser
        question = "Which browser? Chrome, Firefox, or Edge?"
        response = self.ask_follow_up_question(question, ["chrome", "firefox", "edge"])
        
        browser = "chrome"  # Default
        if response:
            if "firefox" in response:
                browser = "firefox"
            elif "edge" in response:
                browser = "edge"
        
        return {
            "action": "search",
            "query": query,
            "engine": engine,
            "browser": browser
        }
    
    def handle_create_command(self, item_type: str, name: str = None) -> Dict:
        """
        Handle create commands with follow-up questions.
        
        Args:
            item_type: Type of item to create (file, folder, etc.)
            name: Optional name
            
        Returns:
            Dict with action details
        """
        # Ask for name if not provided
        if not name:
            question = f"What should I name the {item_type}?"
            response = self.ask_follow_up_question(question)
            if response:
                name = response
            else:
                return {"action": "cancel", "message": "No name provided"}
        
        # Ask for location
        question = "Where should I create it? Desktop, Documents, or current folder?"
        response = self.ask_follow_up_question(question, ["desktop", "documents", "current"])
        
        location = "current"  # Default
        if response:
            if "desktop" in response:
                location = os.path.expanduser("~/Desktop")
            elif "document" in response:
                location = os.path.expanduser("~/Documents")
            else:
                location = os.getcwd()
        
        return {
            "action": "create",
            "item_type": item_type,
            "name": name,
            "location": location
        }
    
    def confirm_action(self, action_description: str) -> bool:
        """
        Ask for confirmation before executing an action.
        
        Args:
            action_description: Description of the action
            
        Returns:
            True if confirmed, False otherwise
        """
        question = f"Should I {action_description}?"
        response = self.ask_follow_up_question(question, ["yes", "no"])
        
        if response and ("yes" in response or "yeah" in response or "haan" in response or "ok" in response):
            return True
        
        return False

