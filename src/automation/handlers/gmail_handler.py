"""
Gmail-specific automation handler using web browser.
"""

import time
import logging

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False
    webdriver = None
    By = None
    WebDriverWait = None
    EC = None
    Service = None
    ChromeDriverManager = None
    TimeoutException = Exception
    NoSuchElementException = Exception

from ...core.screen_agent import ScreenAgent
from ...core.nlp_processor import ParsedCommand, ActionType
from ..task_engine import TaskResult, TaskStatus

class GmailHandler:
    """Handler for Gmail automation using Selenium."""
    
    def __init__(self, screen_agent: ScreenAgent):
        """
        Initialize Gmail handler.
        
        Args:
            screen_agent: Screen agent for UI interactions
        """
        self.screen_agent = screen_agent
        self.logger = logging.getLogger(__name__)
        self.driver = None
        self.wait = None
        self.is_logged_in = False
    
    def handle_command(self, command: ParsedCommand) -> TaskResult:
        """
        Handle Gmail-specific commands.
        
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
                    message="Could not initialize browser for Gmail"
                )
            
            if command.action == ActionType.SEND:
                return self._handle_send_email(command)
            elif command.action == ActionType.OPEN:
                return self._handle_open_gmail(command)
            elif command.action == ActionType.SEARCH:
                return self._handle_search_emails(command)
            else:
                return TaskResult(
                    status=TaskStatus.FAILED,
                    message=f"Unsupported Gmail action: {command.action.value}"
                )
                
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Gmail handler error: {str(e)}"
            )
    
    def _ensure_browser_ready(self) -> bool:
        """Ensure browser is ready for Gmail operations."""
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
                
                # Navigate to Gmail
                self.driver.get("https://gmail.com")
                time.sleep(3)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up browser: {e}")
            return False
    
    def _handle_open_gmail(self, command: ParsedCommand) -> TaskResult:
        """Handle opening Gmail."""
        try:
            if not self.driver:
                return TaskResult(
                    status=TaskStatus.FAILED,
                    message="Browser not initialized"
                )
            
            # Navigate to Gmail if not already there
            if "gmail.com" not in self.driver.current_url:
                self.driver.get("https://gmail.com")
                time.sleep(3)
            
            # Check if we need to sign in
            if not self._is_logged_in():
                return TaskResult(
                    status=TaskStatus.COMPLETED,
                    message="Gmail opened. Please sign in manually to continue."
                )
            
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message="Gmail is ready"
            )
            
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error opening Gmail: {str(e)}"
            )
    
    def _handle_send_email(self, command: ParsedCommand) -> TaskResult:
        """Handle sending email or reply."""
        try:
            if not self._is_logged_in():
                return TaskResult(
                    status=TaskStatus.FAILED,
                    message="Please log in to Gmail first"
                )
            
            # Extract email address from command
            email_address = None
            if command.parameters and 'email' in command.parameters:
                email_address = command.parameters['email']
            elif command.target and '@' in command.target:
                email_address = command.target
            
            if not email_address:
                return TaskResult(
                    status=TaskStatus.FAILED,
                    message="No email address specified"
                )
            
            # Check if this is a reply or new email
            if 'reply' in command.raw_text.lower():
                return self._send_reply(email_address)
            else:
                return self._send_new_email(email_address)
                
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error sending email: {str(e)}"
            )
    
    def _send_reply(self, email_address: str) -> TaskResult:
        """Send a reply to an email from specific address."""
        try:
            # Search for emails from this address
            search_result = self._search_emails_from_address(email_address)
            if not search_result:
                return TaskResult(
                    status=TaskStatus.FAILED,
                    message=f"No emails found from {email_address}"
                )
            
            # Click on the first email
            first_email = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-thread-id]"))
            )
            first_email.click()
            time.sleep(2)
            
            # Click reply button
            try:
                reply_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-tooltip='Reply']"))
                )
                reply_button.click()
                time.sleep(2)
            except TimeoutException:
                # Try alternative selector
                reply_button = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Reply')]")
                reply_button.click()
                time.sleep(2)
            
            # Wait for compose window
            compose_area = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[contenteditable='true']"))
            )
            
            # Type reply message
            reply_message = "Thank you for your email. I'll get back to you soon."
            compose_area.send_keys(reply_message)
            
            # Send the email
            send_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-tooltip='Send']"))
            )
            send_button.click()
            
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message=f"Sent reply to {email_address}"
            )
            
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error sending reply: {str(e)}"
            )
    
    def _send_new_email(self, email_address: str) -> TaskResult:
        """Send a new email."""
        try:
            # Click compose button
            compose_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-tooltip='Compose']"))
            )
            compose_button.click()
            time.sleep(2)
            
            # Fill in recipient
            to_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[peoplekit-id='BbVjBd']"))
            )
            to_field.send_keys(email_address)
            
            # Fill in subject
            subject_field = self.driver.find_element(By.CSS_SELECTOR, "input[name='subjectbox']")
            subject_field.send_keys("Automated Message")
            
            # Fill in message body
            message_body = self.driver.find_element(By.CSS_SELECTOR, "[contenteditable='true']")
            message_body.send_keys("This is an automated message sent via AI assistant.")
            
            # Send the email
            send_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-tooltip='Send']"))
            )
            send_button.click()
            
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message=f"Sent new email to {email_address}"
            )
            
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error sending new email: {str(e)}"
            )
    
    def _handle_search_emails(self, command: ParsedCommand) -> TaskResult:
        """Handle searching emails."""
        if not command.target:
            return TaskResult(
                status=TaskStatus.FAILED,
                message="No search term specified"
            )
        
        try:
            search_box = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label='Search mail']"))
            )
            search_box.clear()
            search_box.send_keys(command.target)
            search_box.submit()
            
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message=f"Searched for '{command.target}' in Gmail"
            )
            
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error searching emails: {str(e)}"
            )
    
    def _search_emails_from_address(self, email_address: str) -> bool:
        """Search for emails from a specific address."""
        try:
            search_box = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label='Search mail']"))
            )
            search_box.clear()
            search_box.send_keys(f"from:{email_address}")
            search_box.submit()
            time.sleep(3)
            
            # Check if any results found
            try:
                self.driver.find_element(By.CSS_SELECTOR, "[data-thread-id]")
                return True
            except NoSuchElementException:
                return False
                
        except Exception as e:
            self.logger.error(f"Error searching emails from {email_address}: {e}")
            return False
    
    def _is_logged_in(self) -> bool:
        """Check if user is logged in to Gmail."""
        try:
            # Look for Gmail interface elements
            self.driver.find_element(By.CSS_SELECTOR, "[data-tooltip='Compose']")
            return True
        except NoSuchElementException:
            return False
    
    def close_browser(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            self.driver = None
