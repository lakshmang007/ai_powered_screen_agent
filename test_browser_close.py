
import sys
import os
import logging
from unittest.mock import MagicMock

# Add src to path
sys.path.insert(0, os.getcwd())

from src.automation.handlers.browser_handler import BrowserHandler
from src.core.nlp_processor import ParsedCommand, ActionType, ApplicationType
from src.core.screen_agent import ScreenAgent

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_close_browser():
    print("Testing BrowserHandler close action...")
    
    # Mock ScreenAgent
    screen_agent = MagicMock(spec=ScreenAgent)
    
    # Initialize handler
    handler = BrowserHandler(screen_agent)
    
    # Create CLOSE command
    command = ParsedCommand(
        action=ActionType.CLOSE,
        application=ApplicationType.CHROME,
        target="chrome",
        raw_text="close chrome"
    )
    
    # Execute command
    # This should try to close system chrome since no driver is active
    # We expect it to succeed (or at least try taskkill)
    
    print("Executing close command...")
    result = handler.handle_command(command)
    
    print(f"Result Status: {result.status}")
    print(f"Result Message: {result.message}")
    
    if result.status.value == 'completed':
        print("✅ Test Passed: Close action handled successfully")
    else:
        print("❌ Test Failed: Close action failed")

if __name__ == "__main__":
    test_close_browser()
