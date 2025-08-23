"""
Generic browser automation handler.
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys

from ...core.screen_agent import ScreenAgent
from ...core.nlp_processor import ParsedCommand, ActionType
from ..task_engine import TaskResult, TaskStatus

class BrowserHandler:
    """Handler for generic browser automation."""
    
    def __init__(self, screen_agent: ScreenAgent):
        """
        Initialize browser handler.
        
        Args:
            screen_agent: Screen agent for UI interactions
        """
        self.screen_agent = screen_agent
        self.logger = logging.getLogger(__name__)
        self.driver = None
        self.wait = None
    
    def handle_command(self, command: ParsedCommand) -> TaskResult:
        """
        Handle browser-specific commands.
        
        Args:
            command: Parsed command to execute
            
        Returns:
            TaskResult with execution status
        """
        try:
            # Initialize browser if not already done
            if not self._ensure_browser_ready():
                return TaskResult(
                    status=TaskStatus.FAILED,
                    message="Could not initialize browser"
                )
            
            if command.action == ActionType.NAVIGATE:
                return self._handle_navigate(command)
            elif command.action == ActionType.SEARCH:
                return self._handle_search(command)
            elif command.action == ActionType.CLICK:
                return self._handle_click(command)
            elif command.action == ActionType.TYPE:
                return self._handle_type(command)
            elif command.action == ActionType.OPEN:
                return self._handle_open_url(command)
            else:
                return TaskResult(
                    status=TaskStatus.FAILED,
                    message=f"Unsupported browser action: {command.action.value}"
                )
                
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Browser handler error: {str(e)}"
            )
    
    def _ensure_browser_ready(self) -> bool:
        """Ensure browser is ready for operations."""
        try:
            if self.driver is None:
                # Setup Chrome driver
                options = webdriver.ChromeOptions()
                options.add_argument("--start-maximized")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                self.wait = WebDriverWait(self.driver, 10)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up browser: {e}")
            return False
    
    def _handle_navigate(self, command: ParsedCommand) -> TaskResult:
        """Handle navigation to URLs."""
        url = command.target
        if not url:
            if command.parameters and 'url' in command.parameters:
                url = command.parameters['url']
            else:
                return TaskResult(
                    status=TaskStatus.FAILED,
                    message="No URL specified for navigation"
                )
        
        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            self.driver.get(url)
            time.sleep(3)
            
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message=f"Navigated to {url}"
            )
            
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error navigating to {url}: {str(e)}"
            )
    
    def _handle_search(self, command: ParsedCommand) -> TaskResult:
        """Handle search operations."""
        search_term = command.target
        if not search_term:
            return TaskResult(
                status=TaskStatus.FAILED,
                message="No search term specified"
            )
        
        try:
            # Try to find a search box on the current page
            search_selectors = [
                "input[type='search']",
                "input[name='q']",
                "input[name='search']",
                "input[placeholder*='search' i]",
                "input[placeholder*='Search' i]",
                "#search",
                ".search-input"
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not search_box:
                # If no search box found, navigate to Google and search
                self.driver.get("https://www.google.com")
                time.sleep(2)
                search_box = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='q']"))
                )
            
            # Perform search
            search_box.clear()
            search_box.send_keys(search_term)
            search_box.send_keys(Keys.RETURN)
            
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message=f"Searched for '{search_term}'"
            )
            
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error performing search: {str(e)}"
            )
    
    def _handle_click(self, command: ParsedCommand) -> TaskResult:
        """Handle clicking elements."""
        target = command.target
        if not target:
            return TaskResult(
                status=TaskStatus.FAILED,
                message="No target specified for click"
            )
        
        try:
            # Try different strategies to find the element
            element = None
            
            # Try by text content
            try:
                element = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{target}')]")
            except NoSuchElementException:
                pass
            
            # Try by link text
            if not element:
                try:
                    element = self.driver.find_element(By.LINK_TEXT, target)
                except NoSuchElementException:
                    pass
            
            # Try by partial link text
            if not element:
                try:
                    element = self.driver.find_element(By.PARTIAL_LINK_TEXT, target)
                except NoSuchElementException:
                    pass
            
            # Try by button text
            if not element:
                try:
                    element = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{target}')]")
                except NoSuchElementException:
                    pass
            
            if element:
                # Scroll to element and click
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)
                element.click()
                
                return TaskResult(
                    status=TaskStatus.COMPLETED,
                    message=f"Clicked on '{target}'"
                )
            else:
                return TaskResult(
                    status=TaskStatus.FAILED,
                    message=f"Could not find element '{target}' to click"
                )
                
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error clicking element: {str(e)}"
            )
    
    def _handle_type(self, command: ParsedCommand) -> TaskResult:
        """Handle typing text."""
        text = command.target
        if not text:
            return TaskResult(
                status=TaskStatus.FAILED,
                message="No text specified to type"
            )
        
        try:
            # Find the currently focused element or the first input field
            active_element = self.driver.switch_to.active_element
            
            if active_element.tag_name in ['input', 'textarea']:
                active_element.send_keys(text)
            else:
                # Try to find an input field
                input_fields = self.driver.find_elements(By.CSS_SELECTOR, "input, textarea")
                if input_fields:
                    input_fields[0].click()
                    input_fields[0].send_keys(text)
                else:
                    return TaskResult(
                        status=TaskStatus.FAILED,
                        message="No input field found to type in"
                    )
            
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message=f"Typed '{text}'"
            )
            
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error typing text: {str(e)}"
            )
    
    def _handle_open_url(self, command: ParsedCommand) -> TaskResult:
        """Handle opening URLs."""
        return self._handle_navigate(command)
    
    def scroll_page(self, direction: str = "down", amount: int = 3) -> TaskResult:
        """Scroll the page."""
        try:
            if direction.lower() == "down":
                self.driver.execute_script(f"window.scrollBy(0, {amount * 300});")
            else:
                self.driver.execute_script(f"window.scrollBy(0, {-amount * 300});")
            
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message=f"Scrolled {direction}"
            )
            
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error scrolling: {str(e)}"
            )
    
    def take_screenshot(self, filename: str = None) -> TaskResult:
        """Take a screenshot of the current page."""
        try:
            if not filename:
                filename = f"screenshot_{int(time.time())}.png"
            
            self.driver.save_screenshot(filename)
            
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message=f"Screenshot saved as {filename}"
            )
            
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error taking screenshot: {str(e)}"
            )
    
    def get_page_title(self) -> str:
        """Get the current page title."""
        try:
            return self.driver.title
        except Exception:
            return "Unknown"
    
    def get_current_url(self) -> str:
        """Get the current URL."""
        try:
            return self.driver.current_url
        except Exception:
            return "Unknown"
    
    def close_browser(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            self.driver = None
