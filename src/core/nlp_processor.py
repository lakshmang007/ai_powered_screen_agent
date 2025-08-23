"""
Natural Language Processing module for understanding and parsing user commands.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import spacy
try:
    from transformers import pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    pipeline = None

class ActionType(Enum):
    """Enumeration of possible action types."""
    CLICK = "click"
    TYPE = "type"
    OPEN = "open"
    CREATE = "create"
    SEND = "send"
    POST = "post"
    NAVIGATE = "navigate"
    SEARCH = "search"
    CLOSE = "close"
    SCROLL = "scroll"
    WAIT = "wait"
    UNKNOWN = "unknown"

class ApplicationType(Enum):
    """Enumeration of supported applications."""
    VSCODE = "vscode"
    GMAIL = "gmail"
    LINKEDIN = "linkedin"
    CHROME = "chrome"
    FIREFOX = "firefox"
    NOTEPAD = "notepad"
    EXPLORER = "explorer"
    TERMINAL = "terminal"
    UNKNOWN = "unknown"

@dataclass
class ParsedCommand:
    """Represents a parsed user command."""
    action: ActionType
    application: ApplicationType
    target: Optional[str] = None
    parameters: Dict[str, Any] = None
    confidence: float = 0.0
    raw_text: str = ""

class NLPProcessor:
    """Natural Language Processing for command understanding."""
    
    def __init__(self):
        """Initialize the NLP processor."""
        self.logger = logging.getLogger(__name__)
        
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.logger.error("spaCy model not found. Please install: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Initialize sentiment analysis pipeline
        if HAS_TRANSFORMERS:
            try:
                self.sentiment_analyzer = pipeline("sentiment-analysis")
            except Exception as e:
                self.logger.warning(f"Could not load sentiment analyzer: {e}")
                self.sentiment_analyzer = None
        else:
            self.sentiment_analyzer = None
        
        # Define action patterns
        self.action_patterns = {
            ActionType.CLICK: [
                r'\b(click|press|tap|select)\b',
                r'\bclick on\b',
                r'\bpress the\b'
            ],
            ActionType.TYPE: [
                r'\b(type|write|enter|input)\b',
                r'\btype in\b',
                r'\bwrite down\b'
            ],
            ActionType.OPEN: [
                r'\b(open|launch|start|run)\b',
                r'\bopen up\b',
                r'\bstart up\b'
            ],
            ActionType.CREATE: [
                r'\b(create|make|new|add)\b',
                r'\bcreate a\b',
                r'\bmake a new\b'
            ],
            ActionType.SEND: [
                r'\b(send|email|mail|reply)\b',
                r'\bsend to\b',
                r'\breply to\b'
            ],
            ActionType.POST: [
                r'\b(post|share|upload|publish)\b',
                r'\bpost to\b',
                r'\bshare on\b'
            ],
            ActionType.NAVIGATE: [
                r'\b(go to|navigate|visit|browse)\b',
                r'\bgo to\b',
                r'\bnavigate to\b'
            ],
            ActionType.SEARCH: [
                r'\b(search|find|look for)\b',
                r'\bsearch for\b',
                r'\blook up\b'
            ],
            ActionType.CLOSE: [
                r'\b(close|exit|quit|shut)\b',
                r'\bclose the\b',
                r'\bshut down\b'
            ],
            ActionType.SCROLL: [
                r'\b(scroll|move|slide)\b',
                r'\bscroll down\b',
                r'\bscroll up\b'
            ]
        }
        
        # Define application patterns
        self.app_patterns = {
            ApplicationType.VSCODE: [
                r'\b(vscode|vs code|visual studio code|code editor)\b',
                r'\bvs\b'
            ],
            ApplicationType.GMAIL: [
                r'\b(gmail|google mail|email)\b',
                r'\bgmail\.com\b'
            ],
            ApplicationType.LINKEDIN: [
                r'\b(linkedin|linked in)\b',
                r'\blinkedin\.com\b'
            ],
            ApplicationType.CHROME: [
                r'\b(chrome|google chrome|browser)\b'
            ],
            ApplicationType.FIREFOX: [
                r'\b(firefox|mozilla)\b'
            ],
            ApplicationType.NOTEPAD: [
                r'\b(notepad|text editor)\b'
            ],
            ApplicationType.EXPLORER: [
                r'\b(explorer|file explorer|files)\b'
            ],
            ApplicationType.TERMINAL: [
                r'\b(terminal|command prompt|cmd|powershell)\b'
            ]
        }
    
    def parse_command(self, text: str) -> ParsedCommand:
        """
        Parse a natural language command into structured data.
        
        Args:
            text: Raw command text
            
        Returns:
            ParsedCommand object with parsed information
        """
        text = text.lower().strip()
        
        # Detect action
        action = self._detect_action(text)
        
        # Detect application
        application = self._detect_application(text)
        
        # Extract target and parameters
        target, parameters = self._extract_target_and_parameters(text, action, application)
        
        # Calculate confidence
        confidence = self._calculate_confidence(text, action, application, target)
        
        return ParsedCommand(
            action=action,
            application=application,
            target=target,
            parameters=parameters,
            confidence=confidence,
            raw_text=text
        )
    
    def _detect_action(self, text: str) -> ActionType:
        """Detect the action type from text."""
        for action_type, patterns in self.action_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return action_type
        return ActionType.UNKNOWN
    
    def _detect_application(self, text: str) -> ApplicationType:
        """Detect the application type from text."""
        for app_type, patterns in self.app_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return app_type
        return ApplicationType.UNKNOWN
    
    def _extract_target_and_parameters(self, text: str, action: ActionType, application: ApplicationType) -> Tuple[Optional[str], Dict[str, Any]]:
        """Extract target and parameters from text."""
        parameters = {}
        target = None
        
        # Extract quoted strings as potential targets
        quoted_matches = re.findall(r'["\']([^"\']+)["\']', text)
        if quoted_matches:
            target = quoted_matches[0]
        
        # Extract email addresses
        email_matches = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_matches:
            parameters['email'] = email_matches[0]
            if not target:
                target = email_matches[0]
        
        # Extract file/folder names
        if action == ActionType.CREATE:
            # Look for "named" or "called" patterns
            name_match = re.search(r'\b(?:named|called)\s+["\']?([^"\']+)["\']?', text)
            if name_match:
                target = name_match.group(1).strip()
            elif not target:
                # Look for words after "folder" or "file"
                folder_match = re.search(r'\b(?:folder|file|directory)\s+([^\s]+)', text)
                if folder_match:
                    target = folder_match.group(1).strip()
        
        # Extract URLs
        url_matches = re.findall(r'https?://[^\s]+', text)
        if url_matches:
            parameters['url'] = url_matches[0]
        
        # Extract image references
        if 'image' in text or 'photo' in text or 'picture' in text:
            parameters['has_image'] = True
        
        # Extract direction for scrolling
        if action == ActionType.SCROLL:
            if 'up' in text:
                parameters['direction'] = 'up'
            elif 'down' in text:
                parameters['direction'] = 'down'
        
        # Use NLP for more sophisticated extraction if available
        if self.nlp:
            doc = self.nlp(text)
            
            # Extract named entities
            entities = {}
            for ent in doc.ents:
                entities[ent.label_] = ent.text
            
            if entities:
                parameters['entities'] = entities
            
            # Extract noun phrases as potential targets if no target found
            if not target:
                noun_phrases = [chunk.text for chunk in doc.noun_chunks]
                if noun_phrases:
                    # Filter out common words
                    filtered_phrases = [phrase for phrase in noun_phrases 
                                      if phrase.lower() not in ['i', 'you', 'it', 'this', 'that']]
                    if filtered_phrases:
                        target = filtered_phrases[0]
        
        return target, parameters
    
    def _calculate_confidence(self, text: str, action: ActionType, application: ApplicationType, target: Optional[str]) -> float:
        """Calculate confidence score for the parsed command."""
        confidence = 0.0
        
        # Base confidence for recognized action
        if action != ActionType.UNKNOWN:
            confidence += 0.4
        
        # Additional confidence for recognized application
        if application != ApplicationType.UNKNOWN:
            confidence += 0.3
        
        # Additional confidence for extracted target
        if target:
            confidence += 0.2
        
        # Bonus for complete sentences
        if len(text.split()) >= 3:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def extract_intent(self, text: str) -> Dict[str, Any]:
        """
        Extract intent and entities from text using advanced NLP.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with intent and entities
        """
        result = {
            'intent': 'unknown',
            'entities': {},
            'sentiment': 'neutral',
            'confidence': 0.0
        }
        
        if not self.nlp:
            return result
        
        try:
            doc = self.nlp(text)
            
            # Extract entities
            for ent in doc.ents:
                result['entities'][ent.label_] = {
                    'text': ent.text,
                    'start': ent.start_char,
                    'end': ent.end_char
                }
            
            # Analyze sentiment if available
            if self.sentiment_analyzer:
                sentiment_result = self.sentiment_analyzer(text)[0]
                result['sentiment'] = sentiment_result['label'].lower()
                result['confidence'] = sentiment_result['score']
            
            # Simple intent classification based on verbs
            verbs = [token.lemma_ for token in doc if token.pos_ == 'VERB']
            if verbs:
                primary_verb = verbs[0]
                if primary_verb in ['open', 'start', 'launch']:
                    result['intent'] = 'open_application'
                elif primary_verb in ['create', 'make', 'add']:
                    result['intent'] = 'create_item'
                elif primary_verb in ['send', 'email', 'mail']:
                    result['intent'] = 'send_message'
                elif primary_verb in ['post', 'share', 'upload']:
                    result['intent'] = 'share_content'
                else:
                    result['intent'] = primary_verb
            
        except Exception as e:
            self.logger.error(f"Error in intent extraction: {e}")
        
        return result
    
    def is_question(self, text: str) -> bool:
        """Check if the text is a question."""
        question_words = ['what', 'how', 'when', 'where', 'why', 'who', 'which', 'can', 'could', 'would', 'should']
        text_lower = text.lower().strip()
        
        # Check for question mark
        if text_lower.endswith('?'):
            return True
        
        # Check for question words at the beginning
        first_word = text_lower.split()[0] if text_lower.split() else ""
        return first_word in question_words
    
    def extract_file_operations(self, text: str) -> Dict[str, Any]:
        """Extract file operation details from text."""
        operations = {
            'operation': None,
            'file_name': None,
            'file_type': None,
            'location': None
        }
        
        # File operations
        if re.search(r'\b(create|make|new)\b.*\b(file|folder|directory)\b', text, re.IGNORECASE):
            operations['operation'] = 'create'
        elif re.search(r'\b(delete|remove)\b.*\b(file|folder|directory)\b', text, re.IGNORECASE):
            operations['operation'] = 'delete'
        elif re.search(r'\b(open|edit)\b.*\b(file|folder|directory)\b', text, re.IGNORECASE):
            operations['operation'] = 'open'
        
        # Extract file name
        name_match = re.search(r'\b(?:named|called)\s+["\']?([^"\']+)["\']?', text)
        if name_match:
            operations['file_name'] = name_match.group(1).strip()
        
        # Extract file type
        type_match = re.search(r'\b(file|folder|directory)\b', text, re.IGNORECASE)
        if type_match:
            operations['file_type'] = type_match.group(1).lower()
        
        return operations
