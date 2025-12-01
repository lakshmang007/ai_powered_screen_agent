"""
Visual Screen Analysis Handler.
Uses Selenium and OCR to identify screen components and interact with them.
"""

from __future__ import annotations
import logging
import time
from typing import Dict, Any, List, Tuple, TYPE_CHECKING
import io

if TYPE_CHECKING:
    from PIL import Image as PILImage

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False
    pyautogui = None

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

from ...core.nlp_processor import ParsedCommand, ActionType


class VisualScreenHandler:
    """Handler for visual screen analysis and interaction."""
    
    def __init__(self, screen_agent=None, voice_processor=None):
        """
        Initialize visual screen handler.
        
        Args:
            screen_agent: Screen agent for screen capture
            voice_processor: Voice processor for speaking to user
        """
        self.screen_agent = screen_agent
        self.voice_processor = voice_processor
        self.logger = logging.getLogger(__name__)
        self.driver = None
        
        if not HAS_SELENIUM:
            self.logger.warning("Selenium not installed. Install with: pip install selenium webdriver-manager")
        
        if not HAS_OCR:
            self.logger.warning("Tesseract OCR not installed. Install with: pip install pytesseract")
    
    def handle_command(self, command: ParsedCommand) -> Dict[str, Any]:
        """
        Handle a visual screen analysis command.
        
        Args:
            command: Parsed command
            
        Returns:
            Result dictionary with status and message
        """
        try:
            action = command.action.value.lower()
            params = command.parameters
            
            if action == "analyze" or action == "scan":
                return self.analyze_screen()
            elif action == "identify":
                return self.identify_components()
            elif action == "click":
                target = params.get('target', command.target)
                return self.click_component(target)
            else:
                return {
                    'status': 'error',
                    'message': f'Unsupported visual screen action: {action}'
                }
        
        except Exception as e:
            self.logger.error(f"Visual screen handler error: {e}")
            return {
                'status': 'error',
                'message': f'Visual screen error: {str(e)}'
            }
    
    def analyze_screen(self) -> Dict[str, Any]:
        """
        Analyze the current screen and identify all components.
        
        Returns:
            Result dictionary with identified components
        """
        try:
            self.logger.info("Analyzing screen...")
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            
            # Get screen size
            screen_width, screen_height = pyautogui.size()
            
            # Identify components using multiple methods
            components = []
            
            # Method 1: Detect windows and applications
            windows = self._detect_windows()
            components.extend(windows)
            
            # Method 2: OCR text detection
            if HAS_OCR:
                text_elements = self._detect_text_elements(screenshot)
                components.extend(text_elements)
            
            # Method 3: Icon detection (basic color-based)
            icons = self._detect_icons(screenshot)
            components.extend(icons)
            
            self.logger.info(f"Found {len(components)} components")
            
            # Ask user which one to open
            if self.voice_processor and components:
                self._ask_user_to_select(components)
            
            return {
                'status': 'completed',
                'message': f'Found {len(components)} components on screen',
                'data': {
                    'components': components,
                    'screen_size': (screen_width, screen_height)
                }
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Screen analysis failed: {str(e)}'
            }
    
    def identify_components(self) -> Dict[str, Any]:
        """
        Identify clickable components on screen.
        
        Returns:
            Result dictionary with components
        """
        try:
            # Get all windows
            import pygetwindow as gw
            
            windows = gw.getAllWindows()
            components = []
            
            for window in windows:
                if window.title and window.visible:
                    components.append({
                        'type': 'window',
                        'title': window.title,
                        'position': (window.left, window.top),
                        'size': (window.width, window.height),
                        'clickable': True
                    })
            
            return {
                'status': 'completed',
                'message': f'Found {len(components)} windows',
                'data': {'components': components}
            }
        
        except ImportError:
            self.logger.warning("pygetwindow not installed. Install with: pip install pygetwindow")
            return {
                'status': 'failed',
                'message': 'pygetwindow not installed'
            }
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Component identification failed: {str(e)}'
            }
    
    def click_component(self, target: str) -> Dict[str, Any]:
        """
        Click on a specific component.
        
        Args:
            target: Name or description of component to click
            
        Returns:
            Result dictionary
        """
        try:
            # Analyze screen to find component
            result = self.analyze_screen()
            
            if result['status'] != 'completed':
                return result
            
            components = result['data']['components']
            
            # Find matching component
            target_lower = target.lower()
            matching = None
            
            for comp in components:
                title = comp.get('title', '').lower()
                text = comp.get('text', '').lower()
                
                if target_lower in title or target_lower in text:
                    matching = comp
                    break
            
            if not matching:
                return {
                    'status': 'failed',
                    'message': f'Component "{target}" not found on screen'
                }
            
            # Click on component
            x, y = matching['position']
            width, height = matching.get('size', (0, 0))
            
            # Click center of component
            click_x = x + width // 2
            click_y = y + height // 2
            
            pyautogui.click(click_x, click_y)
            
            return {
                'status': 'completed',
                'message': f'Clicked on {matching.get("title", target)}',
                'data': {'component': matching}
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Click failed: {str(e)}'
            }
    
    def _detect_windows(self) -> List[Dict[str, Any]]:
        """Detect all visible windows."""
        try:
            import pygetwindow as gw
            
            windows = gw.getAllWindows()
            components = []
            
            for window in windows:
                if window.title and window.visible and window.width > 0 and window.height > 0:
                    components.append({
                        'type': 'window',
                        'title': window.title,
                        'position': (window.left, window.top),
                        'size': (window.width, window.height),
                        'clickable': True
                    })
            
            return components
        
        except Exception as e:
            self.logger.warning(f"Window detection failed: {e}")
            return []
    
    def _detect_text_elements(self, screenshot: "PILImage.Image") -> List[Dict[str, Any]]:
        """Detect text elements using OCR."""
        try:
            if not HAS_OCR:
                return []
            
            # Convert to grayscale for better OCR
            gray = screenshot.convert('L')
            
            # Run OCR
            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            
            components = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                if text and len(text) > 2:  # Ignore very short text
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    confidence = data['conf'][i]
                    
                    if confidence > 50:  # Only high confidence text
                        components.append({
                            'type': 'text',
                            'text': text,
                            'position': (x, y),
                            'size': (w, h),
                            'confidence': confidence,
                            'clickable': True
                        })
            
            return components
        
        except Exception as e:
            self.logger.warning(f"Text detection failed: {e}")
            return []
    
    def _detect_icons(self, screenshot: "PILImage.Image") -> List[Dict[str, Any]]:
        """Detect icons on screen (basic implementation)."""
        # This is a placeholder - would need more sophisticated image processing
        # For now, we'll skip this and rely on window/text detection
        return []
    
    def _ask_user_to_select(self, components: List[Dict[str, Any]]):
        """
        Ask user which component to open.
        
        Args:
            components: List of detected components
        """
        try:
            if not self.voice_processor:
                return
            
            # Group components by type
            windows = [c for c in components if c['type'] == 'window']
            
            if not windows:
                self.voice_processor.speak("I don't see any windows to open.")
                return
            
            # Limit to top 5 most relevant windows
            windows = windows[:5]
            
            # Build message
            message = f"I can see {len(windows)} windows on your screen: "
            
            for i, window in enumerate(windows, 1):
                title = window['title']
                # Clean up title
                if len(title) > 50:
                    title = title[:47] + "..."
                message += f"{i}. {title}, "
            
            message += "Which one would you like me to open?"
            
            self.voice_processor.speak(message)
            
        except Exception as e:
            self.logger.error(f"Error asking user: {e}")

