"""
Natural Language Processing module for understanding and parsing user commands.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False
    spacy = None

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
    PRESS = "press"
    ERASE = "erase"
    CLEAR = "clear"
    SELECT = "select"
    DELETE = "delete"
    MINIMIZE = "minimize"
    PLAY = "play"
    SHUTDOWN = "shutdown"
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
    MACRO = "macro"
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
    
    def __init__(self, use_ai: bool = True):
        """Initialize the NLP processor.

        Args:
            use_ai: Whether to use AI-powered command conversion (default: True)
        """
        self.logger = logging.getLogger(__name__)

        # Load spaCy model
        if HAS_SPACY:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                self.logger.warning("spaCy model not found. Using basic NLP only.")
                self.nlp = None
        else:
            self.logger.warning("spaCy not installed. Using basic NLP only.")
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

        # Initialize AI command converter
        self.ai_converter = None
        if use_ai:
            try:
                from src.core.ai_command_converter import AICommandConverter
                self.ai_converter = AICommandConverter()
                if self.ai_converter.is_available():
                    self.logger.info("🤖 AI-powered command conversion enabled!")
                else:
                    self.ai_converter = None
            except Exception as e:
                self.logger.debug(f"AI converter not available: {e}")
                self.ai_converter = None
        
        # Define action patterns (order matters - more specific first)
        self.action_patterns = {
            ActionType.PRESS: [
                r'\b(press|hit|click)\s+(enter|return|escape|esc|tab|space|backspace|delete|win|windows\s+key|win\s+key)\b',
                r'\bclick\s+enter\b',
                r'\bhit\s+enter\b',
                r'\bclick\s+windows\s+key\b',
                r'\bpress\s+windows\s+key\b',
                r'\bpress\s+win\s+key\b'
            ],
            ActionType.SHUTDOWN: [
                r'\b(shutdown|shut\s+down)\s+(the\s+)?(system|computer|pc|machine)\b',
                r'\b(shutdown|shut\s+down)\s+my\s+(system|computer|pc|machine)\b',
                r'\bshutdown\s+the\s+system\b',
                r'\bshut\s+down\s+computer\b',
                r'\bpower\s+off\b',
                r'\bshutdown\b',  # Just "shutdown" alone
                r'\bshut\s+down\b',  # Just "shut down" alone
            ],
            ActionType.CLICK: [
                r'\b(click|tap|select)\b',
                r'\bclick on\b',
                r'\bpress the\b'
            ],
            ActionType.TYPE: [
                r'\b(type|write|input)\b',
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
                r'\b(close|exit|quit)\b',
                r'\bclose the\b',
                r'\bclose\s+all\s+(apps|applications)\b'
            ],
            ActionType.SCROLL: [
                r'\b(scroll|move|slide)\b',
                r'\bscroll down\b',
                r'\bscroll up\b'
            ],
            ActionType.ERASE: [
                r'\b(erase|remove|clear|delete)\s+(that|it|this|what|text)\b',
                r'\berase\b',
                r'\bremove that\b',
                r'\bclear that\b'
            ],
            ActionType.CLEAR: [
                r'\bclear\s+(all|everything|screen)\b',
                r'\bclear the\b'
            ],
            ActionType.SELECT: [
                r'\bselect\s+(all|everything|text)\b',
                r'\bselect all\b',
                r'\bhighlight all\b'
            ],
            ActionType.DELETE: [
                r'\bdelete\s+(all|everything|text)\b',
                r'\bdelete all\b'
            ],
            ActionType.MINIMIZE: [
                r'\b(minimize|minimise|hide)\b',
                r'\bminimize all\b',
                r'\bminimise all\b',
                r'\bhide all\b'
            ],
            ActionType.PLAY: [
                r'\b(play|run|execute)\s+(macro|recording)\b',
                r'\bplay\s+\w+',
                r'\brun\s+\w+'
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
            ],
            ApplicationType.MACRO: [
                r'\b(macro|macros|recording|recordings)\b'
            ]
        }
    
    def split_multi_step_command(self, text: str) -> List[str]:
        """
        Split a multi-step command into individual steps.

        Args:
            text: Command text that may contain multiple steps

        Returns:
            List of individual command strings
        """
        # Split by common connectors
        # Handle "and then", "then", "and" as separators
        text = text.lower().strip()

        # Handle "open it" or "launch it" after typing - convert to "press enter"
        if re.search(r'type\s+.+?\s+(?:and\s+)?(?:open|launch)\s+it', text):
            text = re.sub(r'(?:and\s+)?(?:open|launch)\s+it', 'and press enter', text)

        # Replace "and then" with a marker
        text = re.sub(r'\s+and\s+then\s+', ' |STEP| ', text)
        # Replace "then" with a marker
        text = re.sub(r'\s+then\s+', ' |STEP| ', text)
        # Replace "and" with a marker (but be careful with "and" in search queries)
        # Only split on "and" if it's followed by an action word
        action_words = ['open', 'click', 'type', 'press', 'search', 'close', 'send', 'navigate']
        for action in action_words:
            text = re.sub(rf'\s+and\s+({action})', r' |STEP| \1', text)

        # Split by the marker
        steps = [step.strip() for step in text.split('|STEP|') if step.strip()]

        return steps if len(steps) > 1 else [text]

    def parse_command(self, text: str) -> ParsedCommand:
        """
        Parse a natural language command into structured data.

        Args:
            text: Raw command text

        Returns:
            ParsedCommand object with parsed information
        """
        original_text = text
        text = text.lower().strip()

        # Try AI-powered conversion first if available
        if self.ai_converter and self.ai_converter.is_available():
            try:
                ai_result = self.ai_converter.convert_command(original_text)
                if ai_result and ai_result.confidence > 0.7:
                    self.logger.info(f"🤖 AI parsed: {ai_result.action} on {ai_result.application}")

                    # Convert AI result to ParsedCommand
                    try:
                        action_type = ActionType(ai_result.action.lower())
                    except ValueError:
                        action_type = ActionType.UNKNOWN

                    try:
                        app_type = ApplicationType(ai_result.application.lower())
                    except ValueError:
                        app_type = ApplicationType.UNKNOWN

                    return ParsedCommand(
                        action=action_type,
                        application=app_type,
                        target=ai_result.target,
                        parameters=ai_result.parameters,
                        confidence=ai_result.confidence,
                        raw_text=original_text
                    )
            except Exception as e:
                self.logger.debug(f"AI conversion failed, falling back to regex: {e}")

        # Fallback to regex-based parsing
        # Detect action
        action = self._detect_action(text)

        # Detect application
        application = self._detect_application(text)

        # Extract target and parameters
        target, parameters = self._extract_target_and_parameters(text, action, application)

        # Calculate confidence
        confidence = self._calculate_confidence(text, action, application, target)

        cmd = ParsedCommand(
            action=action,
            application=application,
            target=target,
            parameters=parameters,
            confidence=confidence,
            raw_text=text
        )
        
        # Force MACRO application if keyword is present
        # This overrides any other detection to ensure macro commands are handled correctly
        if re.search(r'\b(macro|macros|recording)\b', text, re.IGNORECASE):
            cmd.application = ApplicationType.MACRO
            
        return cmd
    
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
        
        # Extract text to type
        if action == ActionType.TYPE and not target:
            # Look for text after "type"
            type_match = re.search(r'\b(?:type|write|input)\s+(.+)', text)
            if type_match:
                target = type_match.group(1).strip()

        # Extract app for OPEN action
        if action == ActionType.OPEN and not target:
            # Look for text after "open", "launch", "start"
            open_match = re.search(r'\b(?:open|launch|start|run)\s+(.+)', text)
            if open_match:
                potential_target = open_match.group(1).strip()
                # Filter out "it", "that"
                if potential_target.lower() not in ['it', 'that', 'this']:
                    target = potential_target

        # Extract target for CLOSE action
        if action == ActionType.CLOSE and not target:
            # Look for text after "close", "exit", "quit"
            close_match = re.search(r'\b(?:close|exit|quit)\s+(.+)', text)
            if close_match:
                potential_target = close_match.group(1).strip()
                # Filter out "it", "that", "window"
                if potential_target.lower() not in ['it', 'that', 'this', 'window', 'application', 'the window', 'current window']:
                    target = potential_target

        # Extract key to press
        if action == ActionType.PRESS and not target:
            # Look for key name after "press", "hit", "click"
            press_match = re.search(r'\b(?:press|hit|click)\s+(\w+)', text)
        if action == ActionType.SCROLL:
            if 'up' in text:
                parameters['direction'] = 'up'
            elif 'down' in text:
                parameters['direction'] = 'down'

        # Check for forced Windows Search
        # e.g. "open dolby access using windows", "open spotify in windows"
        windows_search_match = re.search(r'\b(using|in|with|via)\s+windows\b', text)
        if windows_search_match:
            parameters['force_windows_search'] = True
            # Remove the phrase from text so subsequent extraction works on clean text
            text = re.sub(r'\b(using|in|with|via)\s+windows\b', '', text).strip()
            # Also clean target if it was already extracted
            if target:
                target = re.sub(r'\b(using|in|with|via)\s+windows\b', '', target).strip()

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
                    
                    # Filter out generic terms for CLOSE action
                    if action == ActionType.CLOSE:
                        filtered_phrases = [phrase for phrase in filtered_phrases 
                                          if phrase.lower() not in ['window', 'application', 'app', 'program', 'browser', 'close window', 'the window', 'current window', 'close this', 'close it', 'close that']]

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
