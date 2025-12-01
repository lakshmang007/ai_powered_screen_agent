
import unittest
from unittest.mock import MagicMock
from src.core.nlp_processor import NLPProcessor, ActionType, ParsedCommand
from src.automation.handlers.smart_app_opener import SmartAppOpener
from src.automation.handlers.system_search_handler import SystemSearchHandler

class TestWindowsSearchIntent(unittest.TestCase):
    def setUp(self):
        self.nlp = NLPProcessor()
        self.search_handler = SystemSearchHandler()
        self.search_handler._windows_search_with_vision = MagicMock(return_value={
            'status': 'found',
            'method': 'windows_search',
            'path': 'windows_search_opened',
            'name': 'Test App'
        })
        self.opener = SmartAppOpener(system_search_handler=self.search_handler)

    def test_nlp_detects_using_windows(self):
        text = "open dolby access using windows"
        command = self.nlp.parse_command(text)
        
        self.assertEqual(command.action, ActionType.OPEN)
        self.assertTrue(command.parameters.get('force_windows_search'))
        self.assertEqual(command.target, "dolby access")

    def test_nlp_detects_in_windows(self):
        text = "open spotify in windows"
        command = self.nlp.parse_command(text)
        
        self.assertEqual(command.action, ActionType.OPEN)
        self.assertTrue(command.parameters.get('force_windows_search'))
        self.assertEqual(command.target, "spotify")

    def test_opener_passes_force_flag(self):
        # Mock check_if_running to return False so it proceeds to search
        self.opener.check_if_running = MagicMock(return_value={'is_running': False})
        # Mock search_application to verify call
        self.search_handler.search_application = MagicMock(return_value={'status': 'found', 'method': 'windows_search'})
        
        self.opener.open_app_smart("dolby access", force_windows_search=True)
        
        self.search_handler.search_application.assert_called_with("dolby access", force_windows_search=True)

    def test_search_handler_calls_windows_search_when_forced(self):
        self.search_handler.search_application("dolby access", force_windows_search=True)
        self.search_handler._windows_search_with_vision.assert_called_with("dolby access")

if __name__ == '__main__':
    unittest.main()
