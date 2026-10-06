"""
Regression tests for bugs fixed while stabilising the project.
None of these touch the network, microphone, speakers or the real screen.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from src.core.ai_command_converter import AICommandConverter
from src.core.nlp_processor import NLPProcessor, ActionType, ApplicationType, ParsedCommand
from src.automation.task_engine import TaskEngine, TaskStatus
from src.automation.handlers.smart_app_opener import SmartAppOpener
import jarvis


class TestAIProviderSelection(unittest.TestCase):
    """The converter used to send a GROQ key to Gemini when only GROQ_API_KEY was set."""

    def _make(self, env, provider=None):
        with patch.dict(os.environ, env, clear=True), \
             patch.object(AICommandConverter, '_initialize_client'):
            return AICommandConverter(provider=provider)

    def test_groq_key_selects_groq(self):
        conv = self._make({'GROQ_API_KEY': 'gsk_test'})
        self.assertEqual(conv.provider, 'groq')
        self.assertEqual(conv.api_key, 'gsk_test')

    def test_gemini_preferred_when_both_present(self):
        conv = self._make({'GROQ_API_KEY': 'gsk_test', 'GEMINI_API_KEY': 'gem_test'})
        self.assertEqual(conv.provider, 'gemini')
        self.assertEqual(conv.api_key, 'gem_test')

    def test_never_uses_other_providers_key(self):
        conv = self._make({'GROQ_API_KEY': 'gsk_test'}, provider='gemini')
        self.assertIsNone(conv.api_key)

    def test_placeholder_key_ignored(self):
        conv = self._make({'GEMINI_API_KEY': 'your_gemini_api_key_here'})
        self.assertIsNone(conv.api_key)

    def test_parses_json_wrapped_in_prose(self):
        conv = self._make({})
        cmd = conv._parse_ai_response(
            'Sure! ```json\n{"action": "press", "application": "unknown", "target": "enter", '
            '"parameters": null, "confidence": "0.9"}\n```', 'press enter')
        self.assertEqual(cmd.action, 'press')
        self.assertEqual(cmd.parameters, {})
        self.assertAlmostEqual(cmd.confidence, 0.9)


class TestNLPRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nlp = NLPProcessor(use_ai=False)

    def test_parameters_never_none(self):
        self.assertEqual(ParsedCommand(ActionType.PRESS, ApplicationType.UNKNOWN).parameters, {})

    def test_select_all_is_select_not_click(self):
        self.assertEqual(self.nlp.parse_command('select all').action, ActionType.SELECT)

    def test_press_extracts_key(self):
        self.assertEqual(self.nlp.parse_command('press enter').target, 'enter')
        self.assertEqual(self.nlp.parse_command('click windows key').target, 'win')

    def test_multi_step_keeps_case(self):
        cmd = self.nlp.parse_command('open notepad and type Hello World')
        self.assertEqual(cmd.action, ActionType.MULTI_STEP)
        self.assertEqual(cmd.parameters['steps'], ['open notepad', 'type Hello World'])

    def test_navigate_target(self):
        cmd = self.nlp.parse_command('go to youtube.com')
        self.assertEqual((cmd.action, cmd.target), (ActionType.NAVIGATE, 'youtube.com'))

    def test_search_query_and_engine(self):
        cmd = self.nlp.parse_command('search for python tutorials on youtube')
        self.assertEqual(cmd.target, 'python tutorials')
        self.assertEqual(cmd.parameters['engine'], 'youtube')

    def test_shutdown_requires_explicit_target(self):
        self.assertNotEqual(self.nlp.parse_command('shutdown chrome').action, ActionType.SHUTDOWN)
        self.assertEqual(self.nlp.parse_command('shut down the computer').action, ActionType.SHUTDOWN)


class TestTaskEngineRegressions(unittest.TestCase):
    def setUp(self):
        self.agent = MagicMock()
        for name in ('key_combination', 'press_key', 'type_text'):
            getattr(self.agent, name).return_value = True
        self.engine = TaskEngine(self.agent)

    def test_press_with_none_parameters(self):
        cmd = ParsedCommand(ActionType.PRESS, ApplicationType.UNKNOWN, target=None,
                            parameters=None, raw_text='press enter')
        self.assertEqual(self.engine.execute_command(cmd).status, TaskStatus.COMPLETED)
        self.agent.press_key.assert_called_with('enter')

    def test_multi_step_runs_steps_in_order(self):
        cmd = ParsedCommand(ActionType.MULTI_STEP, ApplicationType.UNKNOWN,
                            parameters={'steps': ['press win', 'type ChatGPT', 'press enter']})
        with patch('src.automation.task_engine.time.sleep'):
            result = self.engine.execute_command(cmd)
        self.assertEqual(result.status, TaskStatus.COMPLETED, result.message)
        self.agent.type_text.assert_called_once_with('ChatGPT')
        self.assertEqual([c.args[0] for c in self.agent.press_key.call_args_list], ['win', 'enter'])

    def test_erase_and_type(self):
        cmd = ParsedCommand(ActionType.ERASE_AND_TYPE, ApplicationType.UNKNOWN, target='hello')
        with patch('src.automation.task_engine.time.sleep'):
            result = self.engine.execute_command(cmd)
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.agent.key_combination.assert_called_with('ctrl', 'a')
        self.agent.type_text.assert_called_with('hello')

    @patch('webbrowser.open', return_value=True)
    def test_navigate_adds_scheme(self, mock_open):
        cmd = ParsedCommand(ActionType.NAVIGATE, ApplicationType.UNKNOWN, target='youtube')
        self.assertEqual(self.engine.execute_command(cmd).status, TaskStatus.COMPLETED)
        mock_open.assert_called_once_with('https://youtube.com')


class TestJarvisPhraseMatching(unittest.TestCase):
    """Substring matching used to treat 'notepad' as 'no' and 'restart' as 'sleep'."""

    def test_negative_needs_whole_word(self):
        self.assertFalse(jarvis.is_negative_response('open notepad'))
        self.assertFalse(jarvis.is_negative_response('i know'))
        self.assertTrue(jarvis.is_negative_response('no thanks'))

    def test_sleep_needs_whole_word(self):
        self.assertFalse(jarvis.is_sleep_command('restart chrome'))
        self.assertFalse(jarvis.is_sleep_command('interest rates'))
        self.assertTrue(jarvis.is_sleep_command('go to sleep'))

    def test_exit_only_for_whole_utterance(self):
        self.assertFalse(jarvis.is_exit_command('exit chrome'))
        self.assertTrue(jarvis.is_exit_command('goodbye'))

    def test_positive_whole_word(self):
        self.assertFalse(jarvis.is_positive_response('open facebook'))  # contains "ok"
        self.assertTrue(jarvis.is_positive_response('yes please'))


class TestSmartOpenerMatching(unittest.TestCase):
    def test_short_keys_need_whole_word(self):
        opener = SmartAppOpener()
        self.assertFalse(opener._name_matches('x', 'excel'))
        self.assertTrue(opener._name_matches('x', 'open x'))

    @patch('webbrowser.open', return_value=True)
    def test_excel_is_not_sent_to_x_dot_com(self, mock_open):
        result = SmartAppOpener().ask_open_in_browser('excel')
        self.assertEqual(result['status'], 'not_found')
        mock_open.assert_not_called()


if __name__ == '__main__':
    unittest.main()


class TestConversationAndClicks(unittest.TestCase):
    """Fixes from the 2026-10-06 JARVIS session log."""

    @classmethod
    def setUpClass(cls):
        cls.nlp = NLPProcessor(use_ai=False)

    def test_small_talk_is_answered_not_searched(self):
        for text in ("what are you doing", "how are you jarvis", "thank you"):
            with self.subTest(text=text):
                cmd = self.nlp.parse_command(text)
                self.assertEqual(cmd.action, ActionType.CHAT)
                self.assertTrue(cmd.target)
        self.assertNotEqual(self.nlp.parse_command("what is the weather in delhi").action, ActionType.CHAT)

    def test_click_is_one_action(self):
        cmd = self.nlp.parse_command("click type a message")
        self.assertEqual((cmd.action, cmd.target), (ActionType.CLICK, "type a message"))
        self.assertEqual(self.nlp.parse_command("click the text container").target, "text container")
        self.assertEqual(self.nlp.parse_command("click enter").action, ActionType.PRESS)

    def test_type_keeps_case(self):
        cmd = self.nlp.parse_command("type Hello World")
        self.assertEqual((cmd.action, cmd.target), (ActionType.TYPE, "Hello World"))


class TestUIAutomationMatching(unittest.TestCase):
    from src.core import ui_automation as ua

    CONTROLS = [
        {"name": "Chats", "type": 50000, "rect": (12, 48, 40, 40), "focused": False},
        {"name": "", "type": 50004, "rect": (133, 114, 239, 21), "focused": False},
        {"name": "Type a message to Mohith", "type": 50004, "rect": (548, 1030, 1309, 24), "focused": False},
        {"name": "WhatsApp", "type": 50030, "rect": (0, 0, 1920, 1080), "focused": False},
        {"name": "Send", "type": 50000, "rect": (1860, 1030, 30, 30), "focused": False},
    ]

    def match(self, query):
        m = self.ua.best_match(query, self.CONTROLS)
        return m and (m["name"], m["rect"])

    def test_named_controls(self):
        self.assertEqual(self.match("type a message")[0], "Type a message to Mohith")
        self.assertEqual(self.match("the send button")[0], "Send")
        self.assertEqual(self.match("chats")[0], "Chats")

    def test_generic_text_box_means_message_box(self):
        self.assertEqual(self.match("the text container")[0], "Type a message to Mohith")
        self.assertEqual(self.match("search box")[1], (133, 114, 239, 21))

    def test_no_match(self):
        self.assertIsNone(self.match("purple elephant"))
