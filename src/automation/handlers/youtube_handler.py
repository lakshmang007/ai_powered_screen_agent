"""
YouTube automation handler.
Handles YouTube video playback using multiple methods.
"""

import logging
import time
import webbrowser
import subprocess
from typing import Dict, Any, Optional
from urllib.parse import quote_plus

from ...core.nlp_processor import ParsedCommand, ActionType
from .browser_detector import BrowserDetector


class YouTubeHandler:
    """Handler for YouTube automation."""

    def __init__(self, screen_agent=None, voice_processor=None):
        """
        Initialize YouTube handler.

        Args:
            screen_agent: Screen agent (optional)
            voice_processor: Voice processor for asking user
        """
        self.screen_agent = screen_agent
        self.voice_processor = voice_processor
        self.logger = logging.getLogger(__name__)
        self.browser_detector = BrowserDetector(voice_processor)
    
    def handle_command(self, command: ParsedCommand) -> Dict[str, Any]:
        """
        Handle a YouTube automation command.
        
        Args:
            command: Parsed command
            
        Returns:
            Result dictionary with status and message
        """
        try:
            action = command.action.value.lower()
            params = command.parameters
            
            if action == "play" or action == "open":
                return self.play_video(params)
            elif action == "search":
                return self.search_youtube(params)
            else:
                return {
                    'status': 'error',
                    'message': f'Unsupported YouTube action: {action}'
                }
        
        except Exception as e:
            self.logger.error(f"YouTube handler error: {e}")
            return {
                'status': 'error',
                'message': f'YouTube error: {str(e)}'
            }
    
    def play_video(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Play video on YouTube.

        Args:
            params: Parameters with 'query' (video search term)

        Returns:
            Result dictionary
        """
        try:
            query = params.get('query', params.get('video', params.get('text', '')))

            if not query:
                return {
                    'status': 'failed',
                    'message': 'Video search query required'
                }

            # Build YouTube URL
            encoded_query = quote_plus(query)
            youtube_url = f"https://www.youtube.com/results?search_query={encoded_query}"

            # Detect installed browsers and ask user
            browser_id = self._select_browser()

            if browser_id:
                # Open in selected browser
                result = self._open_url_in_browser(youtube_url, browser_id)
                if result:
                    return {
                        'status': 'completed',
                        'message': f'Opened YouTube search for: {query}',
                        'data': {'query': query, 'url': youtube_url, 'browser': browser_id}
                    }

            # Fallback to default browser
            self.logger.info(f"Opening YouTube search in default browser: {youtube_url}")
            webbrowser.open(youtube_url)
            time.sleep(2)

            return {
                'status': 'completed',
                'message': f'Opened YouTube search for: {query}',
                'data': {'query': query, 'url': youtube_url, 'method': 'webbrowser'}
            }

        except Exception as e:
            return {
                'status': 'failed',
                'message': f'YouTube play failed: {str(e)}'
            }
    
    def search_youtube(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search on YouTube.

        Args:
            params: Parameters with 'query'

        Returns:
            Result dictionary
        """
        try:
            query = params.get('query', params.get('text', ''))

            if not query:
                return {
                    'status': 'failed',
                    'message': 'Search query required'
                }

            # Build YouTube URL
            encoded_query = quote_plus(query)
            youtube_url = f"https://www.youtube.com/results?search_query={encoded_query}"

            # Detect installed browsers and ask user
            browser_id = self._select_browser()

            if browser_id:
                # Open in selected browser
                result = self._open_url_in_browser(youtube_url, browser_id)
                if result:
                    return {
                        'status': 'completed',
                        'message': f'Searching YouTube for: {query}',
                        'data': {'query': query, 'url': youtube_url, 'browser': browser_id}
                    }

            # Fallback to default browser
            self.logger.info(f"Searching YouTube: {youtube_url}")
            webbrowser.open(youtube_url)

            return {
                'status': 'completed',
                'message': f'Searching YouTube for: {query}',
                'data': {'query': query, 'url': youtube_url}
            }

        except Exception as e:
            return {
                'status': 'failed',
                'message': f'YouTube search failed: {str(e)}'
            }
    
    def open_youtube(self) -> Dict[str, Any]:
        """
        Open YouTube homepage.

        Returns:
            Result dictionary
        """
        try:
            youtube_url = "https://www.youtube.com"

            # Detect installed browsers and ask user
            browser_id = self._select_browser()

            if browser_id:
                # Open in selected browser
                result = self._open_url_in_browser(youtube_url, browser_id)
                if result:
                    return {
                        'status': 'completed',
                        'message': 'Opened YouTube',
                        'data': {'url': youtube_url, 'browser': browser_id}
                    }

            # Fallback to default browser
            self.logger.info(f"Opening YouTube: {youtube_url}")
            webbrowser.open(youtube_url)

            return {
                'status': 'completed',
                'message': 'Opened YouTube',
                'data': {'url': youtube_url}
            }

        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Failed to open YouTube: {str(e)}'
            }
    
    def play_video_by_url(self, url: str) -> Dict[str, Any]:
        """
        Play specific YouTube video by URL.

        Args:
            url: YouTube video URL

        Returns:
            Result dictionary
        """
        try:
            # Detect installed browsers and ask user
            browser_id = self._select_browser()

            if browser_id:
                # Open in selected browser
                result = self._open_url_in_browser(url, browser_id)
                if result:
                    return {
                        'status': 'completed',
                        'message': f'Opened YouTube video',
                        'data': {'url': url, 'browser': browser_id}
                    }

            # Fallback to default browser
            self.logger.info(f"Opening YouTube video: {url}")
            webbrowser.open(url)

            return {
                'status': 'completed',
                'message': f'Opened YouTube video',
                'data': {'url': url}
            }

        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Failed to open video: {str(e)}'
            }

    def _select_browser(self) -> Optional[str]:
        """
        Detect installed browsers and ask user which to use.

        Returns:
            Selected browser ID or None
        """
        try:
            # Detect installed browsers
            installed_browsers = self.browser_detector.detect_installed_browsers()

            if not installed_browsers:
                self.logger.warning("No browsers detected")
                return None

            # Ask user which browser to use
            browser_id = self.browser_detector.ask_browser_choice(installed_browsers)
            return browser_id

        except Exception as e:
            self.logger.error(f"Error selecting browser: {e}")
            return None

    def _open_url_in_browser(self, url: str, browser_id: str) -> bool:
        """
        Open URL in specific browser.

        Args:
            url: URL to open
            browser_id: Browser identifier (chrome, firefox, etc.)

        Returns:
            True if successful
        """
        try:
            command = self.browser_detector.get_browser_command(browser_id)

            self.logger.info(f"Opening {url} in {browser_id}")

            # Use subprocess to open in specific browser
            subprocess.Popen(["start", command, url], shell=True)
            time.sleep(2)

            return True

        except Exception as e:
            self.logger.error(f"Error opening URL in {browser_id}: {e}")
            return False

