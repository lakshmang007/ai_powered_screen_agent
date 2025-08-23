"""
LinkedIn-specific automation handler using web browser.
"""

import time
import logging
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ...core.screen_agent import ScreenAgent
from ...core.nlp_processor import ParsedCommand, ActionType
from ..task_engine import TaskResult, TaskStatus

class LinkedInHandler:
    """Handler for LinkedIn automation using Selenium."""
    
    def __init__(self, screen_agent: ScreenAgent):
        """
        Initialize LinkedIn handler.
        
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
        Handle LinkedIn-specific commands.
        
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
                    message="Could not initialize browser for LinkedIn"
                )
            
            if command.action == ActionType.POST:
                return self._handle_post_content(command)
            elif command.action == ActionType.OPEN:
                return self._handle_open_linkedin(command)
            elif command.action == ActionType.SEARCH:
                return self._handle_search_linkedin(command)
            else:
                return TaskResult(
                    status=TaskStatus.FAILED,
                    message=f"Unsupported LinkedIn action: {command.action.value}"
                )
                
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"LinkedIn handler error: {str(e)}"
            )
    
    def _ensure_browser_ready(self) -> bool:
        """Ensure browser is ready for LinkedIn operations."""
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
                
                # Navigate to LinkedIn
                self.driver.get("https://linkedin.com")
                time.sleep(3)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up browser: {e}")
            return False
    
    def _handle_open_linkedin(self, command: ParsedCommand) -> TaskResult:
        """Handle opening LinkedIn."""
        try:
            if not self.driver:
                return TaskResult(
                    status=TaskStatus.FAILED,
                    message="Browser not initialized"
                )
            
            # Navigate to LinkedIn if not already there
            if "linkedin.com" not in self.driver.current_url:
                self.driver.get("https://linkedin.com")
                time.sleep(3)
            
            # Check if we need to sign in
            if not self._is_logged_in():
                return TaskResult(
                    status=TaskStatus.COMPLETED,
                    message="LinkedIn opened. Please sign in manually to continue."
                )
            
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message="LinkedIn is ready"
            )
            
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error opening LinkedIn: {str(e)}"
            )
    
    def _handle_post_content(self, command: ParsedCommand) -> TaskResult:
        """Handle posting content to LinkedIn."""
        try:
            if not self._is_logged_in():
                return TaskResult(
                    status=TaskStatus.FAILED,
                    message="Please log in to LinkedIn first"
                )
            
            # Navigate to home feed
            self.driver.get("https://www.linkedin.com/feed/")
            time.sleep(3)
            
            # Click on "Start a post" button
            try:
                start_post_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-control-name='share_to_feed']"))
                )
                start_post_button.click()
                time.sleep(2)
            except TimeoutException:
                # Try alternative selector
                start_post_button = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Start a post')]")
                start_post_button.click()
                time.sleep(2)
            
            # Check if we need to upload an image
            has_image = command.parameters and command.parameters.get('has_image', False)
            if has_image:
                return self._post_with_image(command)
            else:
                return self._post_text_only(command)
                
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error posting to LinkedIn: {str(e)}"
            )
    
    def _post_text_only(self, command: ParsedCommand) -> TaskResult:
        """Post text-only content to LinkedIn."""
        try:
            # Wait for the text area to be available
            text_area = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-placeholder='What do you want to talk about?']"))
            )
            
            # Generate interesting content based on the command
            post_content = self._generate_post_content(command)
            
            # Type the content
            text_area.send_keys(post_content)
            time.sleep(1)
            
            # Click the Post button
            post_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-control-name='share.post']"))
            )
            post_button.click()
            
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message="Posted content to LinkedIn successfully"
            )
            
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error posting text content: {str(e)}"
            )
    
    def _post_with_image(self, command: ParsedCommand) -> TaskResult:
        """Post content with image to LinkedIn."""
        try:
            # Click on the image/media button
            try:
                media_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-control-name='media']"))
                )
                media_button.click()
                time.sleep(2)
            except TimeoutException:
                # Try alternative approach
                media_button = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Add media')]")
                media_button.click()
                time.sleep(2)
            
            # Note: File upload would require the user to manually select the image
            # as we cannot programmatically access local files without user permission
            
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message="LinkedIn post dialog opened. Please manually select your image and complete the post."
            )
            
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error posting with image: {str(e)}"
            )
    
    def _generate_post_content(self, command: ParsedCommand) -> str:
        """Generate interesting post content based on the command."""
        # This is a simple content generator
        # In a real implementation, you might use AI to generate more sophisticated content
        
        base_content = command.target if command.target else "Sharing some thoughts today!"
        
        interesting_additions = [
            "\n\n💡 What are your thoughts on this?",
            "\n\n🚀 Excited to share this with my network!",
            "\n\n📈 Always learning and growing in this space.",
            "\n\n🌟 Grateful for the opportunities to connect and learn.",
            "\n\n💪 Continuous improvement is the key to success!"
        ]
        
        import random
        addition = random.choice(interesting_additions)
        
        return base_content + addition
    
    def _handle_search_linkedin(self, command: ParsedCommand) -> TaskResult:
        """Handle searching on LinkedIn."""
        if not command.target:
            return TaskResult(
                status=TaskStatus.FAILED,
                message="No search term specified"
            )
        
        try:
            # Find the search box
            search_box = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Search']"))
            )
            search_box.clear()
            search_box.send_keys(command.target)
            search_box.submit()
            
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message=f"Searched for '{command.target}' on LinkedIn"
            )
            
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error searching LinkedIn: {str(e)}"
            )
    
    def _is_logged_in(self) -> bool:
        """Check if user is logged in to LinkedIn."""
        try:
            # Look for LinkedIn interface elements that appear when logged in
            self.driver.find_element(By.CSS_SELECTOR, "[data-control-name='share_to_feed']")
            return True
        except NoSuchElementException:
            try:
                # Alternative check - look for profile menu
                self.driver.find_element(By.CSS_SELECTOR, "[data-control-name='identity_welcome_message']")
                return True
            except NoSuchElementException:
                return False
    
    def connect_with_user(self, user_profile_url: str) -> TaskResult:
        """Send connection request to a user."""
        try:
            # Navigate to user profile
            self.driver.get(user_profile_url)
            time.sleep(3)
            
            # Click Connect button
            connect_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Connect')]"))
            )
            connect_button.click()
            time.sleep(1)
            
            # Click Send without note (or add note if needed)
            send_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Send')]"))
            )
            send_button.click()
            
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message=f"Sent connection request to user"
            )
            
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error sending connection request: {str(e)}"
            )
    
    def like_post(self, post_element) -> TaskResult:
        """Like a LinkedIn post."""
        try:
            like_button = post_element.find_element(By.CSS_SELECTOR, "[data-control-name='like']")
            like_button.click()
            
            return TaskResult(
                status=TaskStatus.COMPLETED,
                message="Liked the post"
            )
            
        except Exception as e:
            return TaskResult(
                status=TaskStatus.FAILED,
                message=f"Error liking post: {str(e)}"
            )
    
    def close_browser(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            self.driver = None
