"""
Tests for the NLP Processor module.
"""

import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.nlp_processor import NLPProcessor, ActionType, ApplicationType, ParsedCommand

class TestNLPProcessor(unittest.TestCase):
    """Test cases for NLP Processor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.nlp = NLPProcessor(use_ai=False)  # deterministic: no network calls in unit tests
    
    def test_parse_vscode_create_folder(self):
        """Test parsing VSCode folder creation command."""
        command = "create a new folder named auto_work in vscode"
        result = self.nlp.parse_command(command)
        
        self.assertEqual(result.action, ActionType.CREATE)
        self.assertEqual(result.application, ApplicationType.VSCODE)
        self.assertEqual(result.target, "auto_work")
        self.assertGreater(result.confidence, 0.5)
    
    def test_parse_gmail_send_email(self):
        """Test parsing Gmail send email command."""
        command = "send reply email to john@gmail.com"
        result = self.nlp.parse_command(command)
        
        self.assertEqual(result.action, ActionType.SEND)
        self.assertEqual(result.application, ApplicationType.GMAIL)
        self.assertIn('email', result.parameters)
        self.assertEqual(result.parameters['email'], 'john@gmail.com')
    
    def test_parse_linkedin_post(self):
        """Test parsing LinkedIn post command."""
        command = "post this image to my linkedin account"
        result = self.nlp.parse_command(command)
        
        self.assertEqual(result.action, ActionType.POST)
        self.assertEqual(result.application, ApplicationType.LINKEDIN)
        self.assertTrue(result.parameters.get('has_image', False))
    
    def test_parse_open_application(self):
        """Test parsing open application commands."""
        test_cases = [
            ("open vscode", ActionType.OPEN, ApplicationType.VSCODE),
            ("launch chrome", ActionType.OPEN, ApplicationType.CHROME),
            ("start notepad", ActionType.OPEN, ApplicationType.NOTEPAD),
        ]
        
        for command_text, expected_action, expected_app in test_cases:
            with self.subTest(command=command_text):
                result = self.nlp.parse_command(command_text)
                self.assertEqual(result.action, expected_action)
                self.assertEqual(result.application, expected_app)
    
    def test_parse_search_command(self):
        """Test parsing search commands."""
        command = "search for python tutorial"
        result = self.nlp.parse_command(command)
        
        self.assertEqual(result.action, ActionType.SEARCH)
        self.assertEqual(result.target, "python tutorial")
    
    def test_parse_type_command(self):
        """Test parsing type commands."""
        command = "type hello world"
        result = self.nlp.parse_command(command)
        
        self.assertEqual(result.action, ActionType.TYPE)
        self.assertEqual(result.target, "hello world")
    
    def test_parse_click_command(self):
        """Test parsing click commands."""
        command = "click on submit button"
        result = self.nlp.parse_command(command)
        
        self.assertEqual(result.action, ActionType.CLICK)
        self.assertIn("submit", result.target.lower())
    
    def test_parse_scroll_command(self):
        """Test parsing scroll commands."""
        test_cases = [
            ("scroll down", ActionType.SCROLL, "down"),
            ("scroll up", ActionType.SCROLL, "up"),
        ]
        
        for command_text, expected_action, expected_direction in test_cases:
            with self.subTest(command=command_text):
                result = self.nlp.parse_command(command_text)
                self.assertEqual(result.action, expected_action)
                if result.parameters:
                    self.assertEqual(result.parameters.get('direction'), expected_direction)
    
    def test_confidence_calculation(self):
        """Test confidence calculation."""
        # High confidence command
        high_conf_command = "create a new folder named test in vscode"
        high_result = self.nlp.parse_command(high_conf_command)
        
        # Low confidence command
        low_conf_command = "do something"
        low_result = self.nlp.parse_command(low_conf_command)
        
        self.assertGreater(high_result.confidence, low_result.confidence)
    
    def test_extract_email_addresses(self):
        """Test email address extraction."""
        command = "send email to user@example.com and admin@test.org"
        result = self.nlp.parse_command(command)
        
        self.assertIn('email', result.parameters)
        # Should extract the first email
        self.assertIn('@', result.parameters['email'])
    
    def test_extract_quoted_strings(self):
        """Test extraction of quoted strings."""
        command = 'create folder named "My Project Folder" in vscode'
        result = self.nlp.parse_command(command)
        
        self.assertEqual(result.target, "My Project Folder")
    
    def test_is_question(self):
        """Test question detection."""
        questions = [
            "What is the weather?",
            "How do I create a folder?",
            "Can you help me?",
            "Where is the file?"
        ]
        
        statements = [
            "Create a folder",
            "Open VSCode",
            "Send an email"
        ]
        
        for question in questions:
            with self.subTest(text=question):
                self.assertTrue(self.nlp.is_question(question))
        
        for statement in statements:
            with self.subTest(text=statement):
                self.assertFalse(self.nlp.is_question(statement))
    
    def test_extract_file_operations(self):
        """Test file operation extraction."""
        command = "create a new file named test.py"
        result = self.nlp.extract_file_operations(command)
        
        self.assertEqual(result['operation'], 'create')
        self.assertEqual(result['file_type'], 'file')
        self.assertEqual(result['file_name'], 'test.py')
    
    def test_unknown_action_and_application(self):
        """Test handling of unknown actions and applications."""
        command = "do something weird with unknown app"
        result = self.nlp.parse_command(command)
        
        # Should default to unknown when can't determine
        self.assertEqual(result.action, ActionType.UNKNOWN)
        self.assertEqual(result.application, ApplicationType.UNKNOWN)
        self.assertLess(result.confidence, 0.5)

class TestParsedCommand(unittest.TestCase):
    """Test cases for ParsedCommand dataclass."""
    
    def test_parsed_command_creation(self):
        """Test ParsedCommand creation."""
        command = ParsedCommand(
            action=ActionType.CREATE,
            application=ApplicationType.VSCODE,
            target="test_folder",
            parameters={'type': 'folder'},
            confidence=0.8,
            raw_text="create folder test_folder in vscode"
        )
        
        self.assertEqual(command.action, ActionType.CREATE)
        self.assertEqual(command.application, ApplicationType.VSCODE)
        self.assertEqual(command.target, "test_folder")
        self.assertEqual(command.parameters['type'], 'folder')
        self.assertEqual(command.confidence, 0.8)
        self.assertEqual(command.raw_text, "create folder test_folder in vscode")

if __name__ == '__main__':
    unittest.main()
