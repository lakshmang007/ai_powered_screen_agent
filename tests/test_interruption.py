
import unittest
import threading
import time
from unittest.mock import MagicMock, patch
from src.automation.handlers.system_search_handler import SystemSearchHandler

class TestInterruption(unittest.TestCase):
    def setUp(self):
        self.interrupt_event = threading.Event()
        self.handler = SystemSearchHandler(interrupt_event=self.interrupt_event)

    @patch('pyautogui.hotkey')
    @patch('pyautogui.write')
    @patch('pyautogui.press')
    @patch('time.sleep')
    def test_windows_search_interruption_start(self, mock_sleep, mock_press, mock_write, mock_hotkey):
        # Set interrupt immediately
        self.interrupt_event.set()
        
        result = self.handler._windows_search_with_vision("test app")
        
        self.assertEqual(result['status'], 'cancelled')
        self.assertEqual(result['message'], 'Interrupted')
        # Should not have called hotkey
        mock_hotkey.assert_not_called()

    @patch('pyautogui.hotkey')
    @patch('pyautogui.write')
    @patch('pyautogui.press')
    @patch('time.sleep')
    def test_windows_search_interruption_during_wait(self, mock_sleep, mock_press, mock_write, mock_hotkey):
        # Simulate interruption during the first wait loop
        def side_effect_sleep(seconds):
            if mock_hotkey.called:
                self.interrupt_event.set()
        
        mock_sleep.side_effect = side_effect_sleep
        
        result = self.handler._windows_search_with_vision("test app")
        
        self.assertEqual(result['status'], 'cancelled')
        self.assertEqual(result['message'], 'Interrupted')
        # Should have called hotkey (Win+S)
        mock_hotkey.assert_called_with('win', 's')
        # Should NOT have typed
        mock_write.assert_not_called()

if __name__ == '__main__':
    unittest.main()
