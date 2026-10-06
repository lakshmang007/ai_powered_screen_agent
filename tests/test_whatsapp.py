"""
Tests for WhatsApp request parsing and the send flow (WhatsApp/screen fully mocked).
"""

import unittest
from unittest.mock import MagicMock, patch

from src.automation.handlers.whatsapp_handler import WhatsAppHandler, parse_whatsapp_request
from src.automation.task_engine import TaskStatus
from src.core.nlp_processor import NLPProcessor, ActionType, ApplicationType


class TestParseWhatsAppRequest(unittest.TestCase):
    CASES = {
        "send reply as coming to mohith in whatsapp": ("mohith", "coming"),
        "open whatsapp , go to mohith chat and type and send yeah iam coming": ("mohith", "yeah iam coming"),
        "send yeah I'm coming to Mohith on WhatsApp": ("Mohith", "yeah I'm coming"),
        "whatsapp mohith saying I'll be late": ("mohith", "I'll be late"),
        "message mohith on whatsapp that I am on the way": ("mohith", "I am on the way"),
        "on whatsapp send hi to mohith": ("mohith", "hi"),
        "send mohith a message saying hi on whatsapp": ("mohith", "hi"),
        "jarvis send ok to rahul kumar on whatsapp": ("rahul kumar", "ok"),
        "open whatsapp and go to mohith chat": ("mohith", None),
    }

    def test_phrasings(self):
        for text, (contact, message) in self.CASES.items():
            with self.subTest(text=text):
                self.assertEqual(parse_whatsapp_request(text), {"contact": contact, "message": message})

    def test_not_whatsapp(self):
        self.assertIsNone(parse_whatsapp_request("send hi to mohith"))
        self.assertIsNone(parse_whatsapp_request("open whatsapp"))


class TestNLPRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nlp = NLPProcessor(use_ai=False)

    def test_whatsapp_send_not_split_into_steps(self):
        cmd = self.nlp.parse_command("jarvis open whatsapp , go to mohith chat and type and send Yeah I'm coming")
        self.assertEqual((cmd.action, cmd.application), (ActionType.SEND, ApplicationType.WHATSAPP))
        self.assertEqual(cmd.parameters["message"], "Yeah I'm coming")  # case preserved

    def test_windows_button_is_win_key(self):
        for text in ("click windows button jarvis", "open windows", "press the windows key"):
            with self.subTest(text=text):
                cmd = self.nlp.parse_command(text)
                self.assertEqual((cmd.action, cmd.target), (ActionType.PRESS, "win"))


class TestSendFlow(unittest.TestCase):
    def _handler(self, confirm=None, header_ok=True):
        agent = MagicMock()
        agent.key_combination.return_value = True
        agent.press_key.return_value = True
        handler = WhatsAppHandler(agent, confirm_callback=confirm)
        handler.contacts = {}
        handler._focus_whatsapp = MagicMock(return_value=MagicMock())
        handler._whatsapp_window = MagicMock(return_value=MagicMock())
        handler._is_foreground = MagicMock(return_value=True)
        handler._find_in_results = MagicMock(return_value=(100, 200, 50, 20))
        handler._chat_is_open_for = MagicMock(return_value=header_ok)
        handler._focus_composer = MagicMock(return_value=True)
        handler._paste_text = MagicMock(return_value=True)
        return handler, agent

    @patch("src.automation.handlers.whatsapp_handler.time.sleep")
    def test_sends_after_verified_header(self, _sleep):
        handler, agent = self._handler()
        result = handler.send_message("mohith", "yeah iam coming")
        self.assertEqual(result.status, TaskStatus.COMPLETED, result.message)
        handler._paste_text.assert_any_call("yeah iam coming")
        agent.press_key.assert_called_with("enter")

    @patch("src.automation.handlers.whatsapp_handler.time.sleep")
    def test_never_types_if_wrong_chat(self, _sleep):
        handler, agent = self._handler(header_ok=False)
        result = handler.send_message("mohith", "secret")
        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertNotIn(unittest.mock.call("secret"), handler._paste_text.call_args_list)

    @patch("src.automation.handlers.whatsapp_handler.time.sleep")
    def test_declined_confirmation_does_nothing(self, _sleep):
        handler, agent = self._handler(confirm=lambda c, m: False)
        result = handler.send_message("mohith", "hi")
        self.assertEqual(result.status, TaskStatus.CANCELLED)
        handler._focus_whatsapp.assert_not_called()

    def test_open_whatsapp_target_is_not_a_contact(self):
        handler, _ = self._handler()
        handler.open_whatsapp = MagicMock()
        cmd = NLPProcessor(use_ai=False).parse_command("open whatsapp")
        handler.handle_command(cmd)
        handler.open_whatsapp.assert_called_once()


if __name__ == "__main__":
    unittest.main()
