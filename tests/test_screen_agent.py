"""
Tests for the Screen Agent module.
"""

import unittest
import sys
import os
import numpy as np
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.screen_agent import ScreenAgent

class TestScreenAgent(unittest.TestCase):
    """Test cases for Screen Agent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.screen_agent = ScreenAgent()
    
    def test_initialization(self):
        """Test ScreenAgent initialization."""
        # mss is opened per capture (thread safety), so there is no long-lived monitor
        self.assertEqual(self.screen_agent.confidence_threshold, 0.8)

    @patch('src.core.screen_agent.mss.mss')
    def test_capture_screen(self, mock_mss):
        """Test screen capture functionality."""
        # mss.mss() is used as a context manager; grab() returns a BGRA image
        sct = MagicMock()
        sct.monitors = [{'top': 0, 'left': 0, 'width': 200, 'height': 100},
                        {'top': 0, 'left': 0, 'width': 100, 'height': 100}]
        sct.grab.return_value = np.zeros((100, 100, 4), dtype=np.uint8)
        mock_mss.return_value.__enter__.return_value = sct

        result = self.screen_agent.capture_screen()

        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.shape, (100, 100, 3))  # BGRA -> BGR
        # Primary monitor, so OCR coordinates line up with pyautogui clicks
        sct.grab.assert_called_once_with(sct.monitors[1])
    
    @patch('src.core.screen_agent.pyautogui.click')
    def test_click_element(self, mock_click):
        """Test clicking elements."""
        result = self.screen_agent.click_element(100, 200)
        
        self.assertTrue(result)
        mock_click.assert_called_once_with(100, 200, clicks=1, interval=0.1, button='left')
    
    @patch('src.core.screen_agent.pyautogui.write')
    def test_type_text(self, mock_write):
        """Test typing text."""
        test_text = "Hello, World!"
        result = self.screen_agent.type_text(test_text)
        
        self.assertTrue(result)
        mock_write.assert_called_once_with(test_text, interval=0.01)
    
    @patch('src.core.screen_agent.pyautogui.press')
    def test_press_key(self, mock_press):
        """Test pressing keys."""
        result = self.screen_agent.press_key('enter')
        
        self.assertTrue(result)
        mock_press.assert_called_once_with('enter')
    
    @patch('src.core.screen_agent.pyautogui.hotkey')
    def test_key_combination(self, mock_hotkey):
        """Test key combinations."""
        result = self.screen_agent.key_combination('ctrl', 'c')
        
        self.assertTrue(result)
        mock_hotkey.assert_called_once_with('ctrl', 'c')
    
    @patch('src.core.screen_agent.pyautogui.scroll')
    def test_scroll(self, mock_scroll):
        """Test scrolling."""
        result = self.screen_agent.scroll(3)
        
        self.assertTrue(result)
        mock_scroll.assert_called_once_with(3)
    
    @patch('src.core.screen_agent.pyautogui.moveTo')
    def test_move_mouse(self, mock_move):
        """Test mouse movement."""
        result = self.screen_agent.move_mouse(100, 200)
        
        self.assertTrue(result)
        mock_move.assert_called_once_with(100, 200, duration=0.25)
    
    @patch('src.core.screen_agent.pyautogui.size')
    def test_get_screen_size(self, mock_size):
        """Test getting screen size."""
        mock_size.return_value = (1920, 1080)
        
        width, height = self.screen_agent.get_screen_size()
        
        self.assertEqual(width, 1920)
        self.assertEqual(height, 1080)
    
    @patch('src.core.screen_agent.cv2.imread')
    @patch('src.core.screen_agent.cv2.matchTemplate')
    @patch('src.core.screen_agent.cv2.minMaxLoc')
    def test_find_element_by_image(self, mock_minmaxloc, mock_match, mock_imread):
        """Test finding elements by image template."""
        # Mock template loading
        mock_template = np.zeros((50, 50, 3), dtype=np.uint8)
        mock_imread.return_value = mock_template
        
        # Mock template matching
        mock_match.return_value = np.array([[0.9]])
        mock_minmaxloc.return_value = (0.1, 0.9, (10, 20), (100, 150))
        
        # Mock screenshot
        screenshot = np.zeros((200, 200, 3), dtype=np.uint8)
        
        result = self.screen_agent.find_element_by_image('test_template.png', screenshot)
        
        self.assertIsNotNone(result)
        self.assertEqual(result, (100, 150, 50, 50))  # x, y, w, h
    
    @patch('src.core.screen_agent.pytesseract.image_to_data')
    def test_find_text_on_screen(self, mock_ocr):
        """Test finding text on screen using OCR."""
        # Mock OCR data
        mock_ocr.return_value = {
            'text': ['Hello', 'World', 'Test'],
            'left': [10, 60, 110],
            'top': [20, 20, 20],
            'width': [40, 45, 35],
            'height': [15, 15, 15],
            'conf': [85, 90, 80]
        }
        
        screenshot = np.zeros((200, 200, 3), dtype=np.uint8)
        
        results = self.screen_agent.find_text_on_screen('Hello', screenshot)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], (10, 20, 40, 15))  # x, y, w, h
    
    def test_confidence_threshold(self):
        """Test confidence threshold setting."""
        agent = ScreenAgent(confidence_threshold=0.9)
        self.assertEqual(agent.confidence_threshold, 0.9)
    
    @patch('src.core.screen_agent.time.sleep')
    @patch('src.core.screen_agent.time.time')
    def test_wait_for_element_timeout(self, mock_time, mock_sleep):
        """Test waiting for element with timeout."""
        # Mock time progression
        mock_time.side_effect = [0, 5, 11]  # Start, check, timeout
        
        with patch.object(self.screen_agent, 'find_element_by_image', return_value=None):
            result = self.screen_agent.wait_for_element('test.png', timeout=10)
            
            self.assertIsNone(result)
    
    @patch('src.core.screen_agent.time.sleep')
    @patch('src.core.screen_agent.time.time')
    def test_wait_for_element_found(self, mock_time, mock_sleep):
        """Test waiting for element when found."""
        # Mock time progression
        mock_time.side_effect = [0, 2]  # Start, found
        
        with patch.object(self.screen_agent, 'find_element_by_image', return_value=(100, 100, 50, 50)):
            result = self.screen_agent.wait_for_element('test.png', timeout=10)
            
            self.assertEqual(result, (100, 100, 50, 50))

class TestScreenAgentErrorHandling(unittest.TestCase):
    """Test error handling in Screen Agent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.screen_agent = ScreenAgent()
    
    @patch('src.core.screen_agent.pyautogui.click')
    def test_click_element_error_handling(self, mock_click):
        """Test error handling in click_element."""
        mock_click.side_effect = Exception("Click failed")
        
        result = self.screen_agent.click_element(100, 200)
        
        self.assertFalse(result)
    
    @patch('src.core.screen_agent.pyautogui.write')
    def test_type_text_error_handling(self, mock_write):
        """Test error handling in type_text."""
        mock_write.side_effect = Exception("Type failed")
        
        result = self.screen_agent.type_text("test")
        
        self.assertFalse(result)
    
    @patch('src.core.screen_agent.cv2.imread')
    def test_find_element_by_image_template_not_found(self, mock_imread):
        """Test handling when template image is not found."""
        mock_imread.return_value = None
        
        result = self.screen_agent.find_element_by_image('nonexistent.png')
        
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
