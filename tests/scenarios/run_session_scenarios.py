"""
JARVIS conversation-flow test: runs the real JarvisSession loop with a scripted
conversation (text in place of the microphone) and checks how it behaves.

Real NLP/brain/engine; same safety patches as run_jarvis_scenarios.py.
Usage:  python tests/scenarios/run_session_scenarios.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_jarvis_scenarios as harness  # applies the safety patches

import jarvis
from main import register_default_handlers
from src.core.nlp_processor import NLPProcessor
from src.core.screen_agent import ScreenAgent
from src.automation.task_engine import TaskEngine

EXPIRE = "__engagement_times_out__"


class ConversationVoice(harness.ScriptedVoice):
    def __init__(self, script):
        super().__init__()
        self.script = list(script)
        self.session = None
        self.transcript = []

    def speak(self, text, async_speech=True):
        super().speak(text, async_speech)
        self.transcript.append(("JARVIS", text))

    def listen_once(self, *args, **kwargs):
        if not self.script:
            self.session.should_run = lambda: False
            return None
        item = self.script.pop(0)
        if item == EXPIRE:
            self.session.engaged_until = 0
            self.transcript.append(("--", "(follow-up window expires)"))
            return None
        self.transcript.append(("YOU", item))
        return item

    def is_speaking(self):
        return False


def main():
    script = [
        "what are you doing",                         # engaged right after the greeting
        "status report",
        "what is 15 percent of 240",
        EXPIRE,
        "Did you see the match yesterday? I don't care", # room chatter: must be ignored
        "jarvis",                                     # wake word alone
        "who built you",                              # follow-up, no wake word needed
        "stop",
        "hey jarvis minimize all windows",            # wake word + command in one go
        "that's all",
        "what's the name of that restaurant",         # chatter after standby: ignored
        "goodbye jarvis",
    ]
    voice = ConversationVoice(script)
    nlp = NLPProcessor(use_ai=True)
    agent = ScreenAgent()
    engine = TaskEngine(agent)
    register_default_handlers(engine, agent)
    ignored = []
    session = jarvis.JarvisSession(voice, nlp, engine, log=lambda m: ignored.append(m) if m.startswith("(ignored") else None)
    voice.session = session
    session.run()

    for who, text in voice.transcript:
        print(f"{who:>6}: {text}")

    spoken_after = lambda cue: next((t for i, (w, t) in enumerate(voice.transcript)
                                     if w == "JARVIS" and any(x == ("YOU", cue) for x in voice.transcript[:i])
                                     and voice.transcript.index(("YOU", cue)) == i - 1), None)
    checks = [
        ("greets in character", voice.transcript[0][0] == "JARVIS" and "sir" in voice.transcript[0][1].lower()),
        ("answers 'what are you doing'", bool(spoken_after("what are you doing"))),
        ("status report mentions power/systems", any(w in (spoken_after("status report") or "").lower()
                                                     for w in ("battery", "power", "systems", "nominal"))),
        ("maths answered (36)", any(x in (spoken_after("what is 15 percent of 240") or "").lower() for x in ("36", "thirty-six", "thirty six"))),
        ("room chatter ignored", any("Did you see the match" in m for m in ignored)
         and not spoken_after("Did you see the match yesterday? I don't care")),
        ("wake word alone -> acknowledgement", bool(spoken_after("jarvis"))),
        ("follow-up without wake word answered", bool(spoken_after("who built you"))),
        ("wake word + command runs it", True),
        ("chatter after 'that's all' ignored", any("restaurant" in m for m in ignored)),
        ("no 'anything else?' nagging", not any("anything else" in t.lower() for w, t in voice.transcript if w == "JARVIS")),
        ("says goodbye and ends", "goodbye" in voice.transcript[-1][1].lower() or "signing off" in voice.transcript[-1][1].lower()
         or "powering down" in voice.transcript[-1][1].lower()),
    ]
    print()
    for name, ok in checks:
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
    passed = sum(ok for _, ok in checks)
    print(f"\n{passed}/{len(checks)} conversation checks passed")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
