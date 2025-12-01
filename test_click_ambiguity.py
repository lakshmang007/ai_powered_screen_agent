import unittest
from unittest.mock import MagicMock
from src.automation.task_engine import TaskEngine, TaskStatus
from src.core.nlp_processor import ParsedCommand, ActionType, ApplicationType
from src.core.screen_agent import ScreenAgent

class TestClickAmbiguity(unittest.TestCase):
    def setUp(self):
        self.screen_agent = MagicMock(spec=ScreenAgent)
        self.engine = TaskEngine(self.screen_agent)

    def test_click_single_match(self):
        # Setup: 1 match found
        self.screen_agent.find_text_on_screen.return_value = [(100, 100, 50, 20)]
        self.screen_agent.click_element.return_value = True
        
        cmd = ParsedCommand(ActionType.CLICK, ApplicationType.UNKNOWN, target="Submit")
        result = self.engine.execute_command(cmd)
        
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.screen_agent.click_element.assert_called_once()

    def test_click_ambiguous_no_context(self):
        # Setup: 2 matches found
        self.screen_agent.find_text_on_screen.return_value = [
            (100, 100, 50, 20),
            (500, 500, 50, 20)
        ]
        
        cmd = ParsedCommand(ActionType.CLICK, ApplicationType.UNKNOWN, target="Submit", raw_text="click on Submit")
        result = self.engine.execute_command(cmd)
        
        self.assertEqual(result.status, TaskStatus.AMBIGUOUS)
        self.assertIn("Found 2 instances", result.message)

    def test_click_ambiguous_with_context(self):
        # Setup: 2 matches for "Submit", 1 match for "Cancel" (reference)
        # Match 1 is at (100, 100) - near (120, 100)
        # Match 2 is at (500, 500) - far
        # Reference "Cancel" is at (160, 100)
        
        def find_text_side_effect(text):
            if text.lower() == "submit":
                return [(100, 100, 50, 20), (500, 500, 50, 20)]
            elif text.lower() == "cancel":
                return [(160, 100, 50, 20)]
            return []
            
        self.screen_agent.find_text_on_screen.side_effect = find_text_side_effect
        self.screen_agent.click_element.return_value = True
        
        # Command: "click on Submit near Cancel"
        cmd = ParsedCommand(
            ActionType.CLICK, 
            ApplicationType.UNKNOWN, 
            target="Submit", 
            raw_text="click on Submit near Cancel"
        )
        
        result = self.engine.execute_command(cmd)
        
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        # Should click the first match (100, 100) because it's closer to (160, 100)
        # Center of match 1: 125, 110
        # Center of match 2: 525, 510
        # Center of ref: 185, 110
        # Dist 1: 60
        # Dist 2: ~500
        
        # Verify it clicked the correct coordinates (approx center of match 1)
        self.screen_agent.click_element.assert_called_with(125, 110)

if __name__ == '__main__':
    unittest.main()
