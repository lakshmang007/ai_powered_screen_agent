"""
Core Screen Agent for automated screen interaction and computer vision.
"""

from __future__ import annotations
import time
import logging
from typing import Tuple, List, Optional, Dict, Any, TYPE_CHECKING
import os

if TYPE_CHECKING:
    import numpy as np

# Optional dependencies
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    cv2 = None

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    import pyautogui
    HAS_PYAUTOGUI = True
    # Configure pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.1
except ImportError:
    HAS_PYAUTOGUI = False
    pyautogui = None

try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False
    pytesseract = None

try:
    from PIL import Image, ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None
    ImageGrab = None

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False
    mss = None

class ScreenAgent:
    """Main class for screen interaction and automation."""

    def __init__(self, confidence_threshold: float = 0.8):
        """
        Initialize the Screen Agent.

        Args:
            confidence_threshold: Minimum confidence for template matching
        """
        self.confidence_threshold = confidence_threshold
        self.logger = logging.getLogger(__name__)

        # Initialize screen monitor if available
        # We don't initialize mss here to avoid threading issues
        # Instead we create a new instance for each capture
        if not HAS_MSS:
            self.logger.warning("mss not available - screen capture disabled")

        # Configure Tesseract path if needed (Windows). TESSERACT_CMD in .env wins;
        # otherwise use a default install location only if it exists, so a
        # tesseract.exe on PATH keeps working.
        if HAS_PYTESSERACT and os.name == 'nt':
            candidates = [
                os.getenv('TESSERACT_CMD'),
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            ]
            for candidate in candidates:
                if candidate and os.path.exists(candidate):
                    pytesseract.pytesseract.tesseract_cmd = candidate
                    break
    
    def capture_screen(self, region: Optional[Dict[str, int]] = None) -> np.ndarray:
        """
        Capture screenshot of the screen or a specific region.
        
        Args:
            region: Dictionary with 'top', 'left', 'width', 'height' keys
            
        Returns:
            Screenshot as numpy array
        """
        if not HAS_MSS:
            return None

        try:
            with mss.mss() as sct:
                if region:
                    screenshot = sct.grab(region)
                else:
                    # monitors[1] is the primary display. monitors[0] spans every
                    # monitor, whose origin doesn't match pyautogui's click coordinates.
                    screenshot = sct.grab(sct.monitors[1])
                
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
            
            if screenshot is None or not HAS_PYTESSERACT:
                return []
            
            # Convert to PIL Image for OCR
            pil_image = Image.fromarray(cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB))
            
            # Get OCR data
            ocr_data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)
            
            matches = []
            search_text = text.lower().strip()
            
            # 1. Check for exact word matches first (fast)
            for i, word in enumerate(ocr_data['text']):
                if not word.strip():
                    continue
                    
                if search_text in word.lower() and float(ocr_data['conf'][i]) > 30:
                    x = ocr_data['left'][i]
                    y = ocr_data['top'][i]
                    w = ocr_data['width'][i]
                    h = ocr_data['height'][i]
                    matches.append((x, y, w, h))
            
            # 2. If no single-word matches, try phrase matching
            if not matches and ' ' in search_text:
                words = search_text.split()
                n_words = len(words)
                
                # Filter out empty words but keep original indices
                valid_words = []
                for idx, text_val in enumerate(ocr_data['text']):
                    if text_val.strip():
                        valid_words.append({'text': text_val.lower(), 'index': idx})
                
                # Iterate through valid words to find the sequence
                for i in range(len(valid_words) - n_words + 1):
                    # Check if this sequence matches
                    match = True
                    for j in range(n_words):
                        if words[j] not in valid_words[i+j]['text']:
                            match = False
                            break
                    
                    if match:
                        # Found the phrase! Calculate bounding box covering all words
                        # Get original indices
                        start_idx = valid_words[i]['index']
                        end_idx = valid_words[i+n_words-1]['index']
                        
                        # Check confidence of all words in the sequence
                        # We need to check all valid words in the range
                        sequence_indices = [valid_words[k]['index'] for k in range(i, i+n_words)]
                        confidences = [float(ocr_data['conf'][idx]) for idx in sequence_indices]
                        
                        if all(c > 30 for c in confidences):
                            x1 = ocr_data['left'][start_idx]
                            y1 = ocr_data['top'][start_idx]
                            
                            x2 = ocr_data['left'][end_idx] + ocr_data['width'][end_idx]
                            y2 = ocr_data['top'][end_idx] + ocr_data['height'][end_idx]
                            
                            # Combined box
                            matches.append((x1, y1, x2 - x1, y2 - y1))
            
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
