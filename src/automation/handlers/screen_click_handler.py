"""
Screen Click Handler.
Handles clicking on screen elements using OCR and image recognition.
"""

import logging
import time
import pyautogui
from typing import Dict, Any, Optional, Tuple
from PIL import Image
import cv2
import numpy as np


class ScreenClickHandler:
    """Handler for clicking on screen elements."""

    def __init__(self, voice_processor=None):
        """
        Initialize screen click handler.

        Args:
            voice_processor: Voice processor for user interaction
        """
        self.voice_processor = voice_processor
        self.logger = logging.getLogger(__name__)

        # Configure Tesseract path
        try:
            import pytesseract
            import os

            # Check if tesseract is in PATH
            tesseract_cmd = None

            # Try common installation paths
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Tesseract-OCR\tesseract.exe',
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    tesseract_cmd = path
                    self.logger.info(f"Found Tesseract at: {path}")
                    break

            if tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
                self.logger.info(f"Configured Tesseract path: {tesseract_cmd}")
            else:
                self.logger.warning("Tesseract not found in common paths, will try system PATH")

        except ImportError:
            self.logger.warning("pytesseract not installed, screen click will not work")
    
    def find_text_on_screen(self, text: str, case_sensitive: bool = False) -> Optional[Tuple[int, int]]:
        """
        Find text on screen using OCR.
        
        Args:
            text: Text to find
            case_sensitive: Whether to match case
        
        Returns:
            (x, y) coordinates of text center, or None if not found
        """
        try:
            import pytesseract
            
            self.logger.info(f"Searching for text on screen: {text}")
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            
            # Convert to OpenCV format
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Get OCR data with bounding boxes
            data = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT)
            
            # Search for text
            search_text = text if case_sensitive else text.lower()
            
            for i, word in enumerate(data['text']):
                if not word.strip():
                    continue
                
                word_to_check = word if case_sensitive else word.lower()
                
                # Check if this word matches or contains the search text
                if search_text in word_to_check or word_to_check in search_text:
                    # Get bounding box
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    
                    # Calculate center
                    center_x = x + w // 2
                    center_y = y + h // 2
                    
                    self.logger.info(f"Found '{word}' at ({center_x}, {center_y})")
                    return (center_x, center_y)
            
            self.logger.warning(f"Text '{text}' not found on screen")
            return None
        
        except Exception as e:
            self.logger.error(f"Error finding text on screen: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def find_text_fuzzy(self, text: str) -> Optional[Tuple[int, int]]:
        """
        Find text on screen with fuzzy matching (handles partial matches).

        Args:
            text: Text to find (e.g., "custom 2", "custom2", "Custom 2")

        Returns:
            (x, y) coordinates of text center, or None if not found
        """
        try:
            try:
                import pytesseract
            except ImportError:
                self.logger.error("pytesseract not installed, cannot find text on screen")
                if self.voice_processor:
                    self.voice_processor.speak("Sorry, I need Tesseract OCR to find text on screen. Please install it first.")
                return None

            self.logger.info(f"Fuzzy searching for text: {text}")

            # Take screenshot
            screenshot = pyautogui.screenshot()

            try:
                # Get OCR data
                data = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT)
            except pytesseract.TesseractNotFoundError:
                self.logger.error("Tesseract executable not found")
                if self.voice_processor:
                    self.voice_processor.speak("Sorry, Tesseract OCR is not installed. I cannot read text from the screen.")
                return None

            # Normalize search text
            search_text = text.lower().replace(' ', '')

            # Search for text with fuzzy matching
            best_match = None
            best_score = 0

            for i in range(len(data['text'])):
                word = data['text'][i].strip()
                if not word:
                    continue

                # Normalize word
                word_normalized = word.lower().replace(' ', '')

                # Check for exact match
                if search_text == word_normalized:
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    center_x = x + w // 2
                    center_y = y + h // 2

                    self.logger.info(f"Exact match found: '{word}' at ({center_x}, {center_y})")
                    return (center_x, center_y)

                # Check for partial match
                if search_text in word_normalized or word_normalized in search_text:
                    score = len(word_normalized)
                    if score > best_score:
                        best_score = score
                        x = data['left'][i]
                        y = data['top'][i]
                        w = data['width'][i]
                        h = data['height'][i]
                        best_match = (x + w // 2, y + h // 2, word)

            if best_match:
                self.logger.info(f"Best match found: '{best_match[2]}' at ({best_match[0]}, {best_match[1]})")
                return (best_match[0], best_match[1])

            self.logger.warning(f"No match found for '{text}'")
            return None

        except Exception as e:
            self.logger.error(f"Error in fuzzy text search: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def click_text(self, text: str, fuzzy: bool = True) -> Dict[str, Any]:
        """
        Click on text found on screen.
        
        Args:
            text: Text to click on
            fuzzy: Use fuzzy matching
        
        Returns:
            Result dictionary with status and message
        """
        try:
            self.logger.info(f"Attempting to click on text: {text}")
            
            if self.voice_processor:
                self.voice_processor.speak(f"Looking for {text} on the screen.")
            
            # Find text
            if fuzzy:
                coords = self.find_text_fuzzy(text)
            else:
                coords = self.find_text_on_screen(text)
            
            if coords is None:
                self.logger.error(f"Could not find '{text}' on screen")
                return {
                    'status': 'failed',
                    'message': f"Could not find '{text}' on screen"
                }
            
            # Click on the text
            x, y = coords
            self.logger.info(f"Clicking at ({x}, {y})")
            
            if self.voice_processor:
                self.voice_processor.speak(f"Clicking on {text}.")
            
            pyautogui.click(x, y)
            time.sleep(0.5)
            
            self.logger.info(f"Successfully clicked on '{text}'")
            
            return {
                'status': 'completed',
                'message': f"Clicked on '{text}' at ({x}, {y})"
            }
        
        except Exception as e:
            self.logger.error(f"Error clicking on text: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'failed',
                'message': f"Failed to click on '{text}': {str(e)}"
            }
    
    def click_at_position(self, x: int, y: int) -> Dict[str, Any]:
        """
        Click at specific screen coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
        
        Returns:
            Result dictionary with status and message
        """
        try:
            self.logger.info(f"Clicking at position ({x}, {y})")
            
            pyautogui.click(x, y)
            time.sleep(0.5)
            
            return {
                'status': 'completed',
                'message': f"Clicked at ({x}, {y})"
            }
        
        except Exception as e:
            self.logger.error(f"Error clicking at position: {e}")
            return {
                'status': 'failed',
                'message': f"Failed to click: {str(e)}"
            }

