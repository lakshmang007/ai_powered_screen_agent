"""
PowerPoint Handler.
Handles PowerPoint automation tasks like creating presentations, adding slides, etc.
"""

import logging
import time
import pyautogui
from typing import Dict, Any


class PowerPointHandler:
    """Handler for PowerPoint automation."""

    def __init__(self, voice_processor=None):
        """
        Initialize PowerPoint handler.

        Args:
            voice_processor: Voice processor for user interaction
        """
        self.voice_processor = voice_processor
        self.logger = logging.getLogger(__name__)
        self.ppt_app = None

    def _get_powerpoint_app(self):
        """Get or create PowerPoint application COM object."""
        try:
            import win32com.client

            if self.ppt_app is None:
                # Try to get existing PowerPoint instance
                try:
                    self.ppt_app = win32com.client.GetActiveObject("PowerPoint.Application")
                    self.logger.info("Connected to existing PowerPoint instance")
                except:
                    # Create new PowerPoint instance
                    self.ppt_app = win32com.client.Dispatch("PowerPoint.Application")
                    self.ppt_app.Visible = True
                    self.logger.info("Created new PowerPoint instance")

            return self.ppt_app

        except Exception as e:
            self.logger.error(f"Error getting PowerPoint application: {e}")
            return None

    def create_blank_presentation(self) -> Dict[str, Any]:
        """
        Create a blank presentation in PowerPoint.
        Uses COM automation for reliable control.

        Returns:
            Result dictionary with status and message
        """
        try:
            self.logger.info("Creating blank presentation in PowerPoint using COM automation")

            if self.voice_processor:
                self.voice_processor.speak("Creating a blank presentation.")

            # Get PowerPoint application
            ppt = self._get_powerpoint_app()

            if ppt is None:
                self.logger.error("Failed to get PowerPoint application")
                return {
                    'status': 'failed',
                    'message': 'Failed to connect to PowerPoint'
                }

            # Create a new presentation
            self.logger.info("Creating new presentation via COM")
            presentation = ppt.Presentations.Add()

            # Add a blank slide (layout 12 is blank in most PowerPoint versions)
            # Layout constants: ppLayoutBlank = 12
            self.logger.info("Adding blank slide")
            slide = presentation.Slides.Add(1, 12)  # 12 = ppLayoutBlank

            self.logger.info("Blank presentation created successfully")

            return {
                'status': 'completed',
                'message': 'Created blank presentation in PowerPoint'
            }

        except Exception as e:
            self.logger.error(f"Error creating blank presentation: {e}")
            import traceback
            traceback.print_exc()

            # Fallback to keyboard method
            self.logger.info("Falling back to keyboard method")
            return self._create_blank_presentation_keyboard()

    def _create_blank_presentation_keyboard(self) -> Dict[str, Any]:
        """
        Fallback method using keyboard shortcuts.

        Returns:
            Result dictionary with status and message
        """
        try:
            self.logger.info("Creating blank presentation using keyboard shortcuts")

            # Wait for PowerPoint to be ready
            time.sleep(1)

            # Press Ctrl+N to create new presentation
            self.logger.info("Pressing Ctrl+N")
            pyautogui.hotkey('ctrl', 'n')
            time.sleep(2)

            # In newer PowerPoint, Ctrl+N might open a start screen
            # Press Escape to close any dialogs, then try again
            pyautogui.press('escape')
            time.sleep(0.5)

            # Try Ctrl+N again
            pyautogui.hotkey('ctrl', 'n')
            time.sleep(1.5)

            # Press Tab and Enter to select blank presentation
            pyautogui.press('tab')
            time.sleep(0.3)
            pyautogui.press('enter')
            time.sleep(1)

            self.logger.info("Blank presentation created via keyboard")

            return {
                'status': 'completed',
                'message': 'Created blank presentation in PowerPoint'
            }

        except Exception as e:
            self.logger.error(f"Error in keyboard method: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'failed',
                'message': f'Failed to create blank presentation: {str(e)}'
            }
    
    def add_slide(self, layout: str = 'blank') -> Dict[str, Any]:
        """
        Add a new slide to the current presentation.

        Args:
            layout: Slide layout ('blank', 'title', 'title_content', etc.)

        Returns:
            Result dictionary with status and message
        """
        try:
            self.logger.info(f"Adding new slide with layout: {layout}")

            if self.voice_processor:
                self.voice_processor.speak(f"Adding a new slide.")

            # Try COM automation first
            try:
                ppt = self._get_powerpoint_app()
                if ppt and ppt.Presentations.Count > 0:
                    presentation = ppt.ActivePresentation
                    slide_count = presentation.Slides.Count

                    # Layout mapping
                    layout_map = {
                        'blank': 12,  # ppLayoutBlank
                        'title': 1,   # ppLayoutTitle
                        'title_content': 2,  # ppLayoutText
                    }

                    layout_id = layout_map.get(layout, 12)
                    presentation.Slides.Add(slide_count + 1, layout_id)

                    self.logger.info("New slide added via COM")
                    return {
                        'status': 'completed',
                        'message': f'Added new {layout} slide'
                    }
            except Exception as com_error:
                self.logger.warning(f"COM method failed, using keyboard: {com_error}")

            # Fallback to keyboard method
            # Ctrl+M adds a new slide
            pyautogui.hotkey('ctrl', 'm')
            time.sleep(1)

            self.logger.info("New slide added successfully via keyboard")

            return {
                'status': 'completed',
                'message': f'Added new {layout} slide'
            }

        except Exception as e:
            self.logger.error(f"Error adding slide: {e}")
            return {
                'status': 'failed',
                'message': f'Failed to add slide: {str(e)}'
            }
    
    def add_text(self, text: str) -> Dict[str, Any]:
        """
        Add text to the current slide.
        
        Args:
            text: Text to add
        
        Returns:
            Result dictionary with status and message
        """
        try:
            self.logger.info(f"Adding text to slide: {text}")
            
            if self.voice_processor:
                self.voice_processor.speak("Adding text to the slide.")
            
            # Click on the slide to focus
            pyautogui.click()
            time.sleep(0.5)
            
            # Type the text
            pyautogui.write(text, interval=0.05)
            time.sleep(0.5)
            
            self.logger.info("Text added successfully")
            
            return {
                'status': 'completed',
                'message': f'Added text: {text}'
            }
        
        except Exception as e:
            self.logger.error(f"Error adding text: {e}")
            return {
                'status': 'failed',
                'message': f'Failed to add text: {str(e)}'
            }
    
    def save_presentation(self, filename: str = None) -> Dict[str, Any]:
        """
        Save the current presentation.
        
        Args:
            filename: Optional filename to save as
        
        Returns:
            Result dictionary with status and message
        """
        try:
            self.logger.info(f"Saving presentation: {filename}")
            
            if self.voice_processor:
                self.voice_processor.speak("Saving the presentation.")
            
            # Ctrl+S to save
            pyautogui.hotkey('ctrl', 's')
            time.sleep(1)
            
            if filename:
                # Type filename
                pyautogui.write(filename, interval=0.05)
                time.sleep(0.5)
                pyautogui.press('enter')
                time.sleep(1)
            
            self.logger.info("Presentation saved successfully")
            
            return {
                'status': 'completed',
                'message': f'Saved presentation{" as " + filename if filename else ""}'
            }
        
        except Exception as e:
            self.logger.error(f"Error saving presentation: {e}")
            return {
                'status': 'failed',
                'message': f'Failed to save presentation: {str(e)}'
            }

