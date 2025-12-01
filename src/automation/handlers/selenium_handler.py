"""
Selenium-based web automation handler.
Handles all web automation tasks using Selenium WebDriver.
"""

import time
import logging
from typing import Dict, Any, Optional, List

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False
    webdriver = None
    By = None
    Keys = None
    WebDriverWait = None
    EC = None
    Options = None
    Service = None
    ChromeDriverManager = None

from ...core.nlp_processor import ParsedCommand, ActionType


class SeleniumHandler:
    """Handler for Selenium-based web automation."""

    def __init__(self, screen_agent=None, voice_processor=None):
        """
        Initialize Selenium handler.

        Args:
            screen_agent: Screen agent (optional, for compatibility)
            voice_processor: Voice processor for speaking to user
        """
        self.screen_agent = screen_agent
        self.voice_processor = voice_processor
        self.logger = logging.getLogger(__name__)
        self.driver = None
        self.wait_timeout = 10

        # Common URLs
        self.url_mappings = {
            'google': 'https://www.google.com',
            'youtube': 'https://www.youtube.com',
            'github': 'https://github.com',
            'gmail': 'https://mail.google.com',
            'linkedin': 'https://www.linkedin.com',
            'facebook': 'https://www.facebook.com',
            'twitter': 'https://twitter.com',
            'instagram': 'https://www.instagram.com',
            'reddit': 'https://www.reddit.com',
            'stackoverflow': 'https://stackoverflow.com',
            'amazon': 'https://www.amazon.com',
            'netflix': 'https://www.netflix.com',
            'spotify': 'https://open.spotify.com',
            'whatsapp': 'https://web.whatsapp.com',
        }
    
    def handle_command(self, command: ParsedCommand) -> Dict[str, Any]:
        """
        Handle a Selenium automation command.
        
        Args:
            command: Parsed command
            
        Returns:
            Result dictionary with status and message
        """
        try:
            action = command.action.value.lower()
            params = command.parameters
            
            if action == "open":
                return self.open_website(params)
            elif action == "search":
                return self.search_web(params)
            elif action == "navigate":
                return self.navigate_to(params)
            elif action == "click":
                return self.click_element(params)
            elif action == "type":
                return self.type_text(params)
            elif action == "scroll":
                return self.scroll_page(params)
            elif action == "extract":
                return self.extract_data(params)
            elif action == "screenshot":
                return self.take_screenshot(params)
            elif action == "analyze":
                return self.analyze_page()
            elif action == "identify":
                return self.identify_elements()
            elif action == "close":
                return self.close_browser()
            else:
                return {
                    'status': 'error',
                    'message': f'Unsupported Selenium action: {action}'
                }
        
        except Exception as e:
            self.logger.error(f"Selenium handler error: {e}")
            return {
                'status': 'error',
                'message': f'Selenium error: {str(e)}'
            }
    
    def _init_driver(self, headless: bool = False):
        """Initialize Chrome WebDriver."""
        if self.driver:
            return
        
        try:
            options = Options()
            if headless:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--start-maximized")
            
            # Initialize driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.logger.info("Chrome WebDriver initialized")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def open_website(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Open a website.
        
        Args:
            params: Parameters with 'url' or 'site' name
            
        Returns:
            Result dictionary
        """
        try:
            self._init_driver()
            
            # Get URL
            url = params.get('url')
            if not url:
                site = params.get('site', params.get('query', '')).lower()
                url = self.url_mappings.get(site, f'https://www.{site}.com')
            
            # Ensure URL has protocol
            if not url.startswith('http'):
                url = 'https://' + url
            
            self.driver.get(url)
            time.sleep(2)  # Wait for page load
            
            return {
                'status': 'completed',
                'message': f'Opened {url}',
                'data': {'url': url}
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Failed to open website: {str(e)}'
            }
    
    def search_web(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search on Google.
        
        Args:
            params: Parameters with 'query'
            
        Returns:
            Result dictionary
        """
        try:
            self._init_driver()
            
            query = params.get('query', '')
            if not query:
                return {
                    'status': 'failed',
                    'message': 'No search query provided'
                }
            
            # Go to Google
            self.driver.get('https://www.google.com')
            time.sleep(1)
            
            # Find search box and search
            search_box = WebDriverWait(self.driver, self.wait_timeout).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            
            time.sleep(2)  # Wait for results
            
            return {
                'status': 'completed',
                'message': f'Searched for: {query}',
                'data': {'query': query}
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Search failed: {str(e)}'
            }
    
    def navigate_to(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a URL."""
        return self.open_website(params)
    
    def click_element(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Click an element on the page.
        
        Args:
            params: Parameters with 'selector' (CSS selector or text)
            
        Returns:
            Result dictionary
        """
        try:
            if not self.driver:
                return {'status': 'failed', 'message': 'No browser open'}
            
            selector = params.get('selector', params.get('target', ''))
            
            # Try different methods to find element
            element = None
            try:
                # Try CSS selector
                element = WebDriverWait(self.driver, self.wait_timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
            except:
                try:
                    # Try by link text
                    element = self.driver.find_element(By.LINK_TEXT, selector)
                except:
                    # Try by partial link text
                    element = self.driver.find_element(By.PARTIAL_LINK_TEXT, selector)
            
            if element:
                element.click()
                return {
                    'status': 'completed',
                    'message': f'Clicked element: {selector}'
                }
            else:
                return {
                    'status': 'failed',
                    'message': f'Element not found: {selector}'
                }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Click failed: {str(e)}'
            }
    
    def type_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Type text into an element.
        
        Args:
            params: Parameters with 'selector' and 'text'
            
        Returns:
            Result dictionary
        """
        try:
            if not self.driver:
                return {'status': 'failed', 'message': 'No browser open'}
            
            selector = params.get('selector', '')
            text = params.get('text', params.get('query', ''))
            
            element = WebDriverWait(self.driver, self.wait_timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            element.clear()
            element.send_keys(text)
            
            return {
                'status': 'completed',
                'message': f'Typed text into {selector}'
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Type failed: {str(e)}'
            }
    
    def scroll_page(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Scroll the page."""
        try:
            if not self.driver:
                return {'status': 'failed', 'message': 'No browser open'}
            
            direction = params.get('direction', 'down')
            amount = params.get('amount', 500)
            
            if direction == 'down':
                self.driver.execute_script(f"window.scrollBy(0, {amount});")
            elif direction == 'up':
                self.driver.execute_script(f"window.scrollBy(0, -{amount});")
            elif direction == 'bottom':
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            elif direction == 'top':
                self.driver.execute_script("window.scrollTo(0, 0);")
            
            return {
                'status': 'completed',
                'message': f'Scrolled {direction}'
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Scroll failed: {str(e)}'
            }
    
    def extract_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from page."""
        try:
            if not self.driver:
                return {'status': 'failed', 'message': 'No browser open'}
            
            selector = params.get('selector', 'body')
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            
            data = [elem.text for elem in elements if elem.text]
            
            return {
                'status': 'completed',
                'message': f'Extracted {len(data)} items',
                'data': {'items': data}
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Extract failed: {str(e)}'
            }
    
    def take_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Take a screenshot."""
        try:
            if not self.driver:
                return {'status': 'failed', 'message': 'No browser open'}
            
            filename = params.get('filename', 'screenshot.png')
            self.driver.save_screenshot(filename)
            
            return {
                'status': 'completed',
                'message': f'Screenshot saved: {filename}',
                'data': {'filename': filename}
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Screenshot failed: {str(e)}'
            }
    
    def analyze_page(self) -> Dict[str, Any]:
        """
        Analyze the current page and identify all clickable elements.

        Returns:
            Result dictionary with identified elements
        """
        try:
            if not self.driver:
                return {'status': 'failed', 'message': 'No browser open'}

            self.logger.info("Analyzing page...")

            # Get all clickable elements
            elements = []

            # Find links
            links = self.driver.find_elements(By.TAG_NAME, 'a')
            for link in links[:20]:  # Limit to first 20
                text = link.text.strip()
                href = link.get_attribute('href')
                if text and href:
                    elements.append({
                        'type': 'link',
                        'text': text,
                        'href': href,
                        'clickable': True
                    })

            # Find buttons
            buttons = self.driver.find_elements(By.TAG_NAME, 'button')
            for button in buttons[:10]:  # Limit to first 10
                text = button.text.strip()
                if text:
                    elements.append({
                        'type': 'button',
                        'text': text,
                        'clickable': True
                    })

            # Find input fields
            inputs = self.driver.find_elements(By.TAG_NAME, 'input')
            for inp in inputs[:10]:  # Limit to first 10
                input_type = inp.get_attribute('type')
                placeholder = inp.get_attribute('placeholder')
                name = inp.get_attribute('name')
                if input_type not in ['hidden', 'submit']:
                    elements.append({
                        'type': 'input',
                        'input_type': input_type,
                        'placeholder': placeholder,
                        'name': name,
                        'clickable': True
                    })

            self.logger.info(f"Found {len(elements)} elements")

            # Ask user which one to interact with
            if self.voice_processor and elements:
                self._ask_user_to_select(elements)

            return {
                'status': 'completed',
                'message': f'Found {len(elements)} elements on page',
                'data': {
                    'elements': elements,
                    'url': self.driver.current_url,
                    'title': self.driver.title
                }
            }

        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Page analysis failed: {str(e)}'
            }

    def identify_elements(self) -> Dict[str, Any]:
        """
        Identify all interactive elements on the current page.

        Returns:
            Result dictionary with elements
        """
        return self.analyze_page()

    def _ask_user_to_select(self, elements: List[Dict[str, Any]]):
        """
        Ask user which element to interact with.

        Args:
            elements: List of detected elements
        """
        try:
            if not self.voice_processor:
                return

            # Group elements by type
            links = [e for e in elements if e['type'] == 'link']
            buttons = [e for e in elements if e['type'] == 'button']
            inputs = [e for e in elements if e['type'] == 'input']

            # Build message
            message = "I can see several elements on this page: "

            if links:
                message += f"{len(links)} links including "
                for i, link in enumerate(links[:3], 1):
                    text = link['text']
                    if len(text) > 30:
                        text = text[:27] + "..."
                    message += f"{text}, "

            if buttons:
                message += f"{len(buttons)} buttons including "
                for i, button in enumerate(buttons[:3], 1):
                    text = button['text']
                    if len(text) > 30:
                        text = text[:27] + "..."
                    message += f"{text}, "

            if inputs:
                message += f"and {len(inputs)} input fields. "

            message += "What would you like me to do?"

            self.voice_processor.speak(message)

        except Exception as e:
            self.logger.error(f"Error asking user: {e}")

    def close_browser(self) -> Dict[str, Any]:
        """Close the browser."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                return {
                    'status': 'completed',
                    'message': 'Browser closed'
                }
            else:
                return {
                    'status': 'completed',
                    'message': 'No browser to close'
                }

        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Close failed: {str(e)}'
            }

    def cleanup(self):
        """Cleanup resources."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

