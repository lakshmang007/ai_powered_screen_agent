"""
Core Screen Agent for automated screen interaction and computer vision.
"""

import cv2
import numpy as np
import pyautogui
import pytesseract
from PIL import Image, ImageGrab
import mss
import time
import logging
from typing import Tuple, List, Optional, Dict, Any
import os

# Configure pyautogui
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

class ScreenAgent:
    """Main class for screen interaction and automation."""
    
    def __init__(self, confidence_threshold: float = 0.8):
        """
        Initialize the Screen Agent.
        
        Args:
            confidence_threshold: Minimum confidence for template matching
        """
        self.confidence_threshold = confidence_threshold
        self.screen_monitor = mss.mss()
        self.logger = logging.getLogger(__name__)
        
        # Configure Tesseract path if needed (Windows)
        if os.name == 'nt':
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    def capture_screen(self, region: Optional[Dict[str, int]] = None) -> np.ndarray:
        """
        Capture screenshot of the screen or a specific region.
        
        Args:
            region: Dictionary with 'top', 'left', 'width', 'height' keys
            
        Returns:
            Screenshot as numpy array
        """
        try:
            if region:
                screenshot = self.screen_monitor.grab(region)
            else:
                screenshot = self.screen_monitor.grab(self.screen_monitor.monitors[0])
            
            # Convert to numpy array
            img = np.array(screenshot)
            # Convert BGRA to BGR
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img
        except Exception as e:
            self.logger.error(f"Error capturing screen: {e}")
            return None
    
    def find_element_by_image(self, template_path: str, screenshot: Optional[np.ndarray] = None) -> Optional[Tuple[int, int, int, int]]:
        """
        Find an element on screen using template matching.
        
        Args:
            template_path: Path to template image
            screenshot: Screenshot to search in (if None, captures new one)
            
        Returns:
            Tuple of (x, y, width, height) if found, None otherwise
        """
        try:
            if screenshot is None:
                screenshot = self.capture_screen()
            
            if screenshot is None:
                return None
            
            # Load template
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            if template is None:
                self.logger.error(f"Could not load template: {template_path}")
                return None
            
            # Perform template matching
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= self.confidence_threshold:
                h, w = template.shape[:2]
                x, y = max_loc
                return (x, y, w, h)
            
            return None
        except Exception as e:
            self.logger.error(f"Error in template matching: {e}")
            return None
    
    def find_text_on_screen(self, text: str, screenshot: Optional[np.ndarray] = None) -> List[Tuple[int, int, int, int]]:
        """
        Find text on screen using OCR.
        
        Args:
            text: Text to search for
            screenshot: Screenshot to search in (if None, captures new one)
            
        Returns:
            List of bounding boxes (x, y, width, height) where text was found
        """
        try:
            if screenshot is None:
                screenshot = self.capture_screen()
            
            if screenshot is None:
                return []
            
            # Convert to PIL Image for OCR
            pil_image = Image.fromarray(cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB))
            
            # Get OCR data
            ocr_data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)
            
            matches = []
            for i, word in enumerate(ocr_data['text']):
                if text.lower() in word.lower() and int(ocr_data['conf'][i]) > 30:
                    x = ocr_data['left'][i]
                    y = ocr_data['top'][i]
                    w = ocr_data['width'][i]
                    h = ocr_data['height'][i]
                    matches.append((x, y, w, h))
            
            return matches
        except Exception as e:
            self.logger.error(f"Error in OCR text search: {e}")
            return []
    
    def click_element(self, x: int, y: int, button: str = 'left', clicks: int = 1, interval: float = 0.1) -> bool:
        """
        Click on a specific coordinate.
        
        Args:
            x, y: Coordinates to click
            button: Mouse button ('left', 'right', 'middle')
            clicks: Number of clicks
            interval: Interval between clicks
            
        Returns:
            True if successful, False otherwise
        """
        try:
            pyautogui.click(x, y, clicks=clicks, interval=interval, button=button)
            return True
        except Exception as e:
            self.logger.error(f"Error clicking element: {e}")
            return False
    
    def type_text(self, text: str, interval: float = 0.01) -> bool:
        """
        Type text at current cursor position.
        
        Args:
            text: Text to type
            interval: Interval between keystrokes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            pyautogui.write(text, interval=interval)
            return True
        except Exception as e:
            self.logger.error(f"Error typing text: {e}")
            return False
    
    def press_key(self, key: str) -> bool:
        """
        Press a keyboard key.
        
        Args:
            key: Key to press (e.g., 'enter', 'ctrl', 'alt')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            pyautogui.press(key)
            return True
        except Exception as e:
            self.logger.error(f"Error pressing key: {e}")
            return False
    
    def key_combination(self, *keys) -> bool:
        """
        Press a combination of keys.
        
        Args:
            keys: Keys to press simultaneously
            
        Returns:
            True if successful, False otherwise
        """
        try:
            pyautogui.hotkey(*keys)
            return True
        except Exception as e:
            self.logger.error(f"Error pressing key combination: {e}")
            return False
    
    def scroll(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """
        Scroll at a specific position or current mouse position.
        
        Args:
            clicks: Number of scroll clicks (positive for up, negative for down)
            x, y: Position to scroll at (if None, uses current mouse position)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if x is not None and y is not None:
                pyautogui.scroll(clicks, x=x, y=y)
            else:
                pyautogui.scroll(clicks)
            return True
        except Exception as e:
            self.logger.error(f"Error scrolling: {e}")
            return False
    
    def wait_for_element(self, template_path: str, timeout: int = 10, check_interval: float = 0.5) -> Optional[Tuple[int, int, int, int]]:
        """
        Wait for an element to appear on screen.
        
        Args:
            template_path: Path to template image
            timeout: Maximum time to wait in seconds
            check_interval: Time between checks in seconds
            
        Returns:
            Element coordinates if found, None if timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            element = self.find_element_by_image(template_path)
            if element:
                return element
            time.sleep(check_interval)
        
        return None
    
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Get screen dimensions.
        
        Returns:
            Tuple of (width, height)
        """
        return pyautogui.size()
    
    def move_mouse(self, x: int, y: int, duration: float = 0.25) -> bool:
        """
        Move mouse to specific coordinates.
        
        Args:
            x, y: Target coordinates
            duration: Time to take for movement
            
        Returns:
            True if successful, False otherwise
        """
        try:
            pyautogui.moveTo(x, y, duration=duration)
            return True
        except Exception as e:
            self.logger.error(f"Error moving mouse: {e}")
            return False
