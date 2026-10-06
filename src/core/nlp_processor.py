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
    MULTI_STEP = "multi_step"
    ERASE_AND_TYPE = "erase_and_type"
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

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}

class NLPProcessor:
    """Natural Language Processing for command understanding."""

    # Application names the AI may return that map onto our enum
    AI_APP_ALIASES = {
        'vs code': 'vscode', 'visual studio code': 'vscode', 'code': 'vscode',
        'google chrome': 'chrome', 'browser': 'chrome',
        'file explorer': 'explorer', 'cmd': 'terminal', 'powershell': 'terminal',
        'command prompt': 'terminal', 'windows': 'unknown',
    }
    
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

        # Sentiment analysis pipeline is loaded lazily (see _get_sentiment_analyzer)
        self._sentiment_analyzer = None
        self._sentiment_loaded = False

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
                r'\bpower\s+off\b',
                r'^\s*(shutdown|shut\s+down)\s*$',  # Only the bare phrase
            ],
            # Specific editing actions must be checked before CLICK/TYPE,
            # otherwise "select all" became CLICK and "erase that and type x" became TYPE
            ActionType.ERASE: [
                r'\b(erase|remove|clear|delete)\s+(that|it|this|what|text)\b',
                r'\berase\b',
            ],
            ActionType.SELECT: [
                r'\bselect\s+(all|everything|text)\b',
                r'\bhighlight\s+all\b'
            ],
            ActionType.DELETE: [
                r'\bdelete\s+(all|everything)\b',
            ],
            ActionType.CLEAR: [
                r'\bclear\s+(all|everything|screen)\b',
                r'\bclear the\b'
            ],
            ActionType.MINIMIZE: [
                r'\b(minimize|minimise|hide)\b',
            ],
            ActionType.PLAY: [
                r'\b(play|run|execute)\s+(macro|recording)\b',
                r'\bplay\s+\w+',
            ],
            ActionType.NAVIGATE: [
                r'\b(go to|navigate to|navigate|visit|browse to)\b',
            ],
            ActionType.CLICK: [
                r'\b(click|tap|select)\b',
                r'\bpress the\b'
            ],
            ActionType.TYPE: [
                r'\b(type|write|input)\b',
            ],
            ActionType.OPEN: [
                r'\b(open|launch|start|run)\b',
            ],
            ActionType.CREATE: [
                r'\b(create|make|new|add)\b',
            ],
            ActionType.SEND: [
                r'\b(send|email|mail|reply)\b',
            ],
            ActionType.POST: [
                r'\b(post|share|upload|publish)\b',
            ],
            ActionType.SEARCH: [
                r'\b(search|find|look for|look up)\b',
            ],
            ActionType.CLOSE: [
                r'\b(close|exit|quit)\b',
            ],
            ActionType.SCROLL: [
                r'\b(scroll)\b',
            ],
            ActionType.WAIT: [
                r'\b(wait|pause)\b',
            ],
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
        # Handle "and then", "then", "and" as separators.
        # Case is preserved so typed text keeps its capitalisation.
        text = text.strip()

        # Handle "open it" or "launch it" after typing - convert to "press enter"
        if re.search(r'\btype\s+.+?\s+(?:and\s+)?(?:open|launch)\s+it\b', text, re.IGNORECASE):
            text = re.sub(r'(?:and\s+)?(?:open|launch)\s+it\b', 'and press enter', text, flags=re.IGNORECASE)

        # Replace "and then" with a marker
        text = re.sub(r'\s+and\s+then\s+', ' |STEP| ', text, flags=re.IGNORECASE)
        # Replace "then" with a marker
        text = re.sub(r'\s+then\s+', ' |STEP| ', text, flags=re.IGNORECASE)
        # Replace "and" with a marker (but be careful with "and" in search queries)
        # Only split on "and" if it's followed by an action word
        action_words = ['open', 'click', 'type', 'press', 'search', 'close', 'send', 'navigate', 'go to', 'scroll', 'wait', 'minimize']
        for action in action_words:
            text = re.sub(rf'\s+and\s+({action})\b', r' |STEP| \1', text, flags=re.IGNORECASE)

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

                    app_name = ai_result.application.lower()
                    app_name = self.AI_APP_ALIASES.get(app_name, app_name)
                    try:
                        app_type = ApplicationType(app_name)
                    except ValueError:
                        app_type = ApplicationType.UNKNOWN

                    parameters = dict(ai_result.parameters or {})
                    if action_type == ActionType.MULTI_STEP and not parameters.get('steps'):
                        parameters['steps'] = self.split_multi_step_command(original_text)

                    # Keep the regex-only flags the rest of the app relies on
                    if re.search(r'\b(using|in|with|via)\s+windows\b', text):
                        parameters['force_windows_search'] = True

                    if action_type != ActionType.UNKNOWN:
                        cmd = ParsedCommand(
                            action=action_type,
                            application=app_type,
                            target=ai_result.target or None,
                            parameters=parameters,
                            confidence=ai_result.confidence,
                            raw_text=original_text
                        )
                        if re.search(r'\b(macro|macros|recording)\b', text):
                            cmd.application = ApplicationType.MACRO
                        return cmd
            except Exception as e:
                self.logger.debug(f"AI conversion failed, falling back to regex: {e}")

        # Fallback to regex-based parsing
        # "open notepad and type hello" -> one MULTI_STEP command the engine runs in order
        steps = self.split_multi_step_command(original_text)
        if len(steps) > 1:
            return ParsedCommand(
                action=ActionType.MULTI_STEP,
                application=self._detect_application(text),
                target=None,
                parameters={'steps': steps},
                confidence=0.8,
                raw_text=original_text
            )

        # Detect action
        action = self._detect_action(text)

        # Detect application
        application = self._detect_application(text)

        # Extract target and parameters from the original text so the user's casing
        # survives (folder names, text to type, ...)
        target, parameters = self._extract_target_and_parameters(original_text.strip(), action, application)

        # Calculate confidence
        confidence = self._calculate_confidence(text, action, application, target)

        cmd = ParsedCommand(
            action=action,
            application=application,
            target=target,
            parameters=parameters,
            confidence=confidence,
            raw_text=original_text
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
        
        # Extract file/folder names: "create a folder named auto_work"
        if action == ActionType.CREATE and not target:
            name_match = re.search(r'\b(?:named|called)\s+(\S+)', text, re.IGNORECASE)
            if name_match:
                target = name_match.group(1).strip('"\'.,')
            item_match = re.search(r'\b(folder|directory|file)\b', text, re.IGNORECASE)
            if item_match:
                parameters['type'] = item_match.group(1).lower()

        # Posts that mention media
        if action == ActionType.POST and re.search(r'\b(image|photo|picture|pic|screenshot)\b', text, re.IGNORECASE):
            parameters['has_image'] = True

        # Extract text to type
        if action == ActionType.TYPE and not target:
            # Look for text after "type"
            type_match = re.search(r'\b(?:type|write|input)\s+(.+)', text, re.IGNORECASE)
            if type_match:
                target = type_match.group(1).strip()

        # Extract app for OPEN action
        if action == ActionType.OPEN and not target:
            # Look for text after "open", "launch", "start"
            open_match = re.search(r'\b(?:open|launch|start|run)\s+(.+)', text, re.IGNORECASE)
            if open_match:
                potential_target = open_match.group(1).strip()
                # Filter out "it", "that"
                if potential_target.lower() not in ['it', 'that', 'this']:
                    target = potential_target

        # Extract target for CLOSE action
        if action == ActionType.CLOSE and not target:
            # Look for text after "close", "exit", "quit"
            close_match = re.search(r'\b(?:close|exit|quit)\s+(.+)', text, re.IGNORECASE)
            if close_match:
                potential_target = close_match.group(1).strip()
                # Filter out "it", "that", "window"
                if potential_target.lower() not in ['it', 'that', 'this', 'window', 'application', 'the window', 'current window']:
                    target = potential_target

        # Extract key to press
        if action == ActionType.PRESS and not target:
            # Look for key name after "press", "hit", "click"
            if re.search(r'\b(windows|win)\s+key\b', text, re.IGNORECASE):
                target = 'win'
            else:
                press_match = re.search(r'\b(?:press|hit|click)\s+(?:the\s+)?(\w+)', text, re.IGNORECASE)
                if press_match:
                    target = press_match.group(1).lower()

        if action == ActionType.NAVIGATE and not target:
            nav_match = re.search(r'\b(?:go to|navigate to|navigate|visit|browse to)\s+(.+)', text, re.IGNORECASE)
            if nav_match:
                target = re.sub(r'\s+(?:website|site|page)$', '', nav_match.group(1).strip(), flags=re.IGNORECASE)

        if action == ActionType.SEARCH and not target:
            search_match = re.search(r'\b(?:search\s+for|search|look\s+for|look\s+up|find)\s+(.+)', text, re.IGNORECASE)
            if search_match:
                query = search_match.group(1).strip()
                # "search for cats on youtube" -> query "cats", engine hint "youtube"
                engine_match = re.search(r'\s+(?:on|in|using)\s+(google|youtube|bing|duckduckgo|chrome|browser)\s*$', query, re.IGNORECASE)
                if engine_match:
                    parameters['engine'] = engine_match.group(1).lower()
                    query = query[:engine_match.start()].strip()
                target = query
                parameters['query'] = query

        if action in (ActionType.ERASE, ActionType.CLEAR, ActionType.DELETE):
            # "erase that and type hello" -> also type afterwards
            type_after = re.search(r'\band\s+(?:then\s+)?(?:type|write)\s+(.+)', text, re.IGNORECASE)
            if type_after:
                parameters['type_after'] = type_after.group(1).strip()

        if action == ActionType.WAIT:
            wait_match = re.search(r'(\d+(?:\.\d+)?)', text)
            if wait_match:
                parameters['seconds'] = float(wait_match.group(1))

        if action == ActionType.SCROLL:
            if re.search(r'\bup\b', text, re.IGNORECASE):
                parameters['direction'] = 'up'
            elif re.search(r'\bdown\b', text, re.IGNORECASE):
                parameters['direction'] = 'down'

        # Check for forced Windows Search
        # e.g. "open dolby access using windows", "open spotify in windows"
        windows_search_match = re.search(r'\b(using|in|with|via)\s+windows\b', text, re.IGNORECASE)
        if windows_search_match:
            parameters['force_windows_search'] = True
            # Remove the phrase from text so subsequent extraction works on clean text
            text = re.sub(r'\b(using|in|with|via)\s+windows\b', '', text, flags=re.IGNORECASE).strip()
            # Also clean target if it was already extracted
            if target:
                target = re.sub(r'\b(using|in|with|via)\s+windows\b', '', target, flags=re.IGNORECASE).strip()

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
            if not target and action not in (ActionType.SCROLL, ActionType.WAIT, ActionType.SHUTDOWN,
                                              ActionType.ERASE, ActionType.SELECT, ActionType.CLEAR,
                                              ActionType.DELETE):
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
            sentiment_analyzer = self._get_sentiment_analyzer()
            if sentiment_analyzer:
                sentiment_result = sentiment_analyzer(text)[0]
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
    
    def _get_sentiment_analyzer(self):
        """Load the transformers sentiment pipeline on first use."""
        if not self._sentiment_loaded:
            self._sentiment_loaded = True
            if HAS_TRANSFORMERS:
                try:
                    self._sentiment_analyzer = pipeline("sentiment-analysis")
                except Exception as e:
                    self.logger.warning(f"Could not load sentiment analyzer: {e}")
        return self._sentiment_analyzer

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
