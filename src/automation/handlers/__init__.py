"""
Application-specific handlers for automated tasks.
"""

from .vscode_handler import VSCodeHandler
from .gmail_handler import GmailHandler
from .linkedin_handler import LinkedInHandler
from .browser_handler import BrowserHandler

__all__ = ['VSCodeHandler', 'GmailHandler', 'LinkedInHandler', 'BrowserHandler']
