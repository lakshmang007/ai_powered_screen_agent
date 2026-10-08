"""
End-to-end JARVIS scenario run on the real desktop.

Uses the real NLP (incl. AI if a key is configured), the real task engine,
real clicks/keys and the real WhatsApp Desktop app. Only the microphone and
speaker are replaced by a scripted voice, and two things are made safe:
  * WhatsApp sends run in dry-run mode (typed, verified, then cleared - never sent)
  * Web searches / URLs are recorded instead of opening browser tabs

Usage:  python tests/scenarios/run_jarvis_scenarios.py [contact]
"""

import os
import sys
import time
import logging

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
os.chdir(ROOT)
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))
logging.basicConfig(level=logging.WARNING)

import jarvis
from main import register_default_handlers
from src.core.nlp_processor import NLPProcessor
from src.core.screen_agent import ScreenAgent
from src.automation.task_engine import TaskEngine
from src.automation.handlers.whatsapp_handler import WhatsAppHandler
from src.core import ui_automation

CONTACT = sys.argv[1] if len(sys.argv) > 1 else "mohith"


class ScriptedVoice:
    """Stands in for the microphone/speaker."""

    def __init__(self):
        self.answers, self.spoken = [], []

    def speak(self, text, async_speech=True):
        self.spoken.append(text)

    def listen_once(self, *args, **kwargs):
        return self.answers.pop(0) if self.answers else None

    def listen(self, *args, **kwargs):
        return self.listen_once()

    def stop_speaking(self):
        pass

    def wait_until_done(self, *args, **kwargs):
        pass


# --- safety patches ---------------------------------------------------------
opened_urls = []
jarvis.open_url = lambda url, browser=None: opened_urls.append(url) or True
_real_send = WhatsAppHandler.send_message
WhatsAppHandler.send_message = lambda self, contact, message, dry_run=False: _real_send(self, contact, message, dry_run=True)
real_click = ScreenAgent.click_element
clicks = []
def recording_click(self, x, y, *a, **k):
    clicks.append((x, y))
    return real_click(self, x, y, *a, **k)
ScreenAgent.click_element = recording_click


last_click_result = {}
_real_click_action = TaskEngine._handle_click_action
def recording_click_action(self, command):
    result = _real_click_action(self, command)
    last_click_result.update(message=result.message, control=(result.data or {}).get('control'))
    return result
TaskEngine._handle_click_action = recording_click_action


def focused_control_name():
    """Name of the WhatsApp message box if it has keyboard focus (WinUI reports
    the focused element as its outer content island, so ask the box itself)."""
    composer = WhatsAppHandler(ScreenAgent())._composer_element()
    if composer is not None and composer.CurrentHasKeyboardFocus:
        return composer.CurrentName
    return f"(message box not focused; clicked: {last_click_result.get('message')})"


def main():
    voice = ScriptedVoice()
    nlp = NLPProcessor(use_ai=True)
    agent = ScreenAgent()
    engine = TaskEngine(agent)
    register_default_handlers(engine, agent, whatsapp_confirm=jarvis.make_voice_confirm(voice))
    context = jarvis.ContextMemory()
    ai = nlp.ai_converter.provider if nlp.ai_converter else "none (regex only)"
    print(f"AI provider: {ai}\n")

    def whatsapp_window():
        return WhatsAppHandler(agent)._whatsapp_window()

    # (command, scripted answers, check(result, voice, urls, before_clicks) -> (ok, detail))
    scenarios = [
        ("open WhatsApp", [],
         lambda r: (r and whatsapp_window() is not None and jarvis.gw_active_title() == "WhatsApp",
                    f"foreground={jarvis.gw_active_title()!r}")),
        ("what are you doing", [],
         lambda r: (r and not opened_urls and len(voice.spoken[-1]) > 10,
                    f"reply={voice.spoken[-1]!r}, urls opened={opened_urls}")),
        (f"open whatsapp and go to {CONTACT} chat", [],
         lambda r: (r, f"spoken={voice.spoken[-1]!r}")),
        ("click the text container", [],
         lambda r: (r and "type a message" in (focused_control_name() or "").lower(),
                    f"focused={focused_control_name()!r}")),
        ("click type a message", [],
         lambda r: (r and "type a message" in (focused_control_name() or "").lower(),
                    f"focused={focused_control_name()!r}")),
        (f"open whatsapp , go to {CONTACT} chat and type and send yeah iam coming", ["yes"],
         lambda r: (r and "dry run" in voice.spoken[-1].lower(), f"spoken={voice.spoken[-1]!r}")),
        (f"send reply as coming to {CONTACT} in whatsapp jarvis", ["yes"],
         lambda r: (r and "dry run" in voice.spoken[-1].lower(), f"spoken={voice.spoken[-1]!r}")),
        (f"send hello to {CONTACT} on whatsapp", ["no"],
         lambda r: (r is False and "won't send" in voice.spoken[-1].lower(), f"spoken={voice.spoken[-1]!r}")),
        ("click windows button jarvis", [],
         lambda r: (r, "Start menu should have opened")),
        ("escape", [],
         lambda r: (r, "Start menu closed")),
        ("search for python tutorials", [],
         lambda r: (r and opened_urls and opened_urls[-1].endswith("q=python+tutorials"),
                    f"url={opened_urls[-1] if opened_urls else None}")),
        ("click the purple elephant", [],
         lambda r: (r is False and "could not find" in voice.spoken[-1].lower(),
                    f"spoken={voice.spoken[-1]!r}")),
        ("shut down the computer", ["no"],
         lambda r: (r is False and "cancelled" in voice.spoken[-1].lower(), f"spoken={voice.spoken[-1]!r}")),
    ]

    results = []
    for command, answers, check in scenarios:
        voice.answers = list(answers)
        start = time.time()
        try:
            returned = jarvis.execute_jarvis_command(command, nlp, engine, voice, None, context, None)
            time.sleep(0.8)
            ok, detail = check(returned)
        except Exception as e:
            ok, detail = False, f"EXCEPTION {type(e).__name__}: {e}"
        duration = time.time() - start
        results.append((command, bool(ok), duration, detail))
        print(f"{'PASS' if ok else 'FAIL'}  {duration:5.1f}s  {command}\n        {detail}")

    passed = sum(1 for r in results if r[1])
    print(f"\n{passed}/{len(results)} scenarios passed")
    return 0 if passed == len(results) else 1


# small helper used by the checks
def _active_title():
    import pygetwindow as gw
    w = gw.getActiveWindow()
    return w.title.strip() if w else None
jarvis.gw_active_title = _active_title

if __name__ == "__main__":
    sys.exit(main())
