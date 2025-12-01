"""
PyWhatKit-based automation handler.
Handles WhatsApp, YouTube, Google searches, and more using PyWhatKit.
"""

import time
import logging
from typing import Dict, Any
from datetime import datetime, timedelta

try:
    import pywhatkit as pwk
    HAS_PYWHATKIT = True
except ImportError:
    HAS_PYWHATKIT = False
    pwk = None

from ...core.nlp_processor import ParsedCommand, ActionType


class PyWhatKitHandler:
    """Handler for PyWhatKit-based automation."""
    
    def __init__(self, screen_agent=None):
        """
        Initialize PyWhatKit handler.
        
        Args:
            screen_agent: Screen agent (optional, for compatibility)
        """
        self.screen_agent = screen_agent
        self.logger = logging.getLogger(__name__)
        
        if not HAS_PYWHATKIT:
            self.logger.warning("PyWhatKit not installed. Install with: pip install pywhatkit")
    
    def handle_command(self, command: ParsedCommand) -> Dict[str, Any]:
        """
        Handle a PyWhatKit automation command.
        
        Args:
            command: Parsed command
            
        Returns:
            Result dictionary with status and message
        """
        if not HAS_PYWHATKIT:
            return {
                'status': 'failed',
                'message': 'PyWhatKit not installed. Install with: pip install pywhatkit'
            }
        
        try:
            action = command.action.value.lower()
            params = command.parameters
            
            if action == "send" or action == "whatsapp":
                return self.send_whatsapp_message(params)
            elif action == "search":
                return self.search_google(params)
            elif action == "play" or action == "youtube":
                return self.play_youtube(params)
            elif action == "info":
                return self.get_info(params)
            elif action == "convert":
                return self.convert_text_to_handwriting(params)
            else:
                return {
                    'status': 'error',
                    'message': f'Unsupported PyWhatKit action: {action}'
                }
        
        except Exception as e:
            self.logger.error(f"PyWhatKit handler error: {e}")
            return {
                'status': 'error',
                'message': f'PyWhatKit error: {str(e)}'
            }
    
    def send_whatsapp_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send WhatsApp message.
        
        Args:
            params: Parameters with 'phone', 'message', and optional 'time'
            
        Returns:
            Result dictionary
        """
        try:
            phone = params.get('phone', params.get('number', ''))
            message = params.get('message', params.get('text', ''))
            
            if not phone:
                return {
                    'status': 'failed',
                    'message': 'Phone number required'
                }
            
            if not message:
                return {
                    'status': 'failed',
                    'message': 'Message text required'
                }
            
            # Ensure phone number has country code
            if not phone.startswith('+'):
                phone = '+91' + phone  # Default to India
            
            # Get time (default: 1 minute from now)
            now = datetime.now()
            send_time = params.get('time')
            
            if send_time:
                # Parse time if provided
                hour, minute = map(int, send_time.split(':'))
            else:
                # Send in 1 minute
                future = now + timedelta(minutes=1)
                hour = future.hour
                minute = future.minute
            
            # Send message
            pwk.sendwhatmsg(phone, message, hour, minute)
            
            return {
                'status': 'completed',
                'message': f'WhatsApp message scheduled to {phone} at {hour}:{minute}',
                'data': {
                    'phone': phone,
                    'message': message,
                    'time': f'{hour}:{minute}'
                }
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'WhatsApp send failed: {str(e)}'
            }
    
    def send_whatsapp_instant(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send WhatsApp message instantly (requires WhatsApp Web to be open).
        
        Args:
            params: Parameters with 'phone' and 'message'
            
        Returns:
            Result dictionary
        """
        try:
            phone = params.get('phone', params.get('number', ''))
            message = params.get('message', params.get('text', ''))
            
            if not phone or not message:
                return {
                    'status': 'failed',
                    'message': 'Phone number and message required'
                }
            
            # Ensure phone number has country code
            if not phone.startswith('+'):
                phone = '+91' + phone
            
            # Send instantly
            pwk.sendwhatmsg_instantly(phone, message, wait_time=15, tab_close=True)
            
            return {
                'status': 'completed',
                'message': f'WhatsApp message sent to {phone}',
                'data': {'phone': phone, 'message': message}
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'WhatsApp instant send failed: {str(e)}'
            }
    
    def search_google(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search on Google.
        
        Args:
            params: Parameters with 'query'
            
        Returns:
            Result dictionary
        """
        try:
            query = params.get('query', params.get('text', ''))
            
            if not query:
                return {
                    'status': 'failed',
                    'message': 'Search query required'
                }
            
            # Search on Google
            pwk.search(query)
            
            return {
                'status': 'completed',
                'message': f'Searched Google for: {query}',
                'data': {'query': query}
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Google search failed: {str(e)}'
            }
    
    def play_youtube(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Play video on YouTube.
        
        Args:
            params: Parameters with 'query' (video search term)
            
        Returns:
            Result dictionary
        """
        try:
            query = params.get('query', params.get('video', params.get('text', '')))
            
            if not query:
                return {
                    'status': 'failed',
                    'message': 'Video search query required'
                }
            
            # Play on YouTube
            pwk.playonyt(query)
            
            return {
                'status': 'completed',
                'message': f'Playing on YouTube: {query}',
                'data': {'query': query}
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'YouTube play failed: {str(e)}'
            }
    
    def get_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get information from Wikipedia.
        
        Args:
            params: Parameters with 'topic'
            
        Returns:
            Result dictionary
        """
        try:
            topic = params.get('topic', params.get('query', ''))
            lines = params.get('lines', 2)
            
            if not topic:
                return {
                    'status': 'failed',
                    'message': 'Topic required'
                }
            
            # Get info from Wikipedia
            info = pwk.info(topic, lines=lines)
            
            return {
                'status': 'completed',
                'message': f'Information about {topic}',
                'data': {
                    'topic': topic,
                    'info': info
                }
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Info retrieval failed: {str(e)}'
            }
    
    def convert_text_to_handwriting(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert text to handwriting image.
        
        Args:
            params: Parameters with 'text' and optional 'filename'
            
        Returns:
            Result dictionary
        """
        try:
            text = params.get('text', params.get('message', ''))
            filename = params.get('filename', 'handwriting.png')
            
            if not text:
                return {
                    'status': 'failed',
                    'message': 'Text required'
                }
            
            # Convert to handwriting
            pwk.text_to_handwriting(text, save_to=filename)
            
            return {
                'status': 'completed',
                'message': f'Handwriting saved to {filename}',
                'data': {
                    'text': text,
                    'filename': filename
                }
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Handwriting conversion failed: {str(e)}'
            }
    
    def send_whatsapp_group(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send message to WhatsApp group.
        
        Args:
            params: Parameters with 'group_id', 'message', and 'time'
            
        Returns:
            Result dictionary
        """
        try:
            group_id = params.get('group_id', '')
            message = params.get('message', params.get('text', ''))
            
            if not group_id or not message:
                return {
                    'status': 'failed',
                    'message': 'Group ID and message required'
                }
            
            # Get time (default: 1 minute from now)
            now = datetime.now()
            send_time = params.get('time')
            
            if send_time:
                hour, minute = map(int, send_time.split(':'))
            else:
                future = now + timedelta(minutes=1)
                hour = future.hour
                minute = future.minute
            
            # Send to group
            pwk.sendwhatmsg_to_group(group_id, message, hour, minute)
            
            return {
                'status': 'completed',
                'message': f'WhatsApp group message scheduled at {hour}:{minute}',
                'data': {
                    'group_id': group_id,
                    'message': message,
                    'time': f'{hour}:{minute}'
                }
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'WhatsApp group send failed: {str(e)}'
            }

