"""
JARVIS's voice lines: short, polite, dry, British, in the style of the Iron Man films.

How JARVIS addresses you is set with JARVIS_ADDRESS in .env (default "sir").
"""

import os
import random
import datetime
from typing import Dict, Optional


def address() -> str:
    return os.getenv("JARVIS_ADDRESS", "sir").strip() or "sir"


def _pick(options):
    # Plain replace (not str.format): names spoken by the user may contain braces
    line = random.choice(options).replace("{{sir}}", "{sir}")
    return line.replace("{Sir}", address().capitalize()).replace("{sir}", address())


def part_of_day(now: Optional[datetime.datetime] = None) -> str:
    hour = (now or datetime.datetime.now()).hour
    if hour < 5:
        return "night"
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    return "evening"


def greeting() -> str:
    pod = part_of_day()
    if pod == "night":
        return _pick(["Working late again, {sir}? All systems are online.",
                      "Burning the midnight oil, {sir}. I'm at your disposal."])
    return _pick([f"Good {pod}, {{sir}}. All systems are online.",
                  f"Good {pod}, {{sir}}. How may I assist?",
                  f"Good {pod}, {{sir}}. I'm at your service."])


def wake() -> str:
    return _pick(["Yes, {sir}?", "At your service, {sir}.", "{Sir}?", "I'm listening, {sir}.", "For you, {sir}, always."])


def standby() -> str:
    return _pick(["Very well, {sir}. I'll be here.", "Standing by, {sir}.", "As you wish. Call if you need me."])


def goodbye() -> str:
    return _pick(["Goodbye, {sir}. Shutting down.", "Powering down, {sir}. Do try to get some rest.",
                  "Very good, {sir}. Signing off."])


def didnt_catch() -> str:
    return _pick(["I'm sorry, {sir}, I didn't catch that.", "Could you repeat that, {sir}?"])


def stopped() -> str:
    return _pick(["Of course.", "Stopping.", "As you wish, {sir}."])


def ack(action: str, target: Optional[str] = None, app: Optional[str] = None) -> Optional[str]:
    """What JARVIS says while starting a task (None = just do it quietly)."""
    name = (target or app or "").strip()
    if action == "open" and name and name != "unknown":
        return _pick([f"Opening {name}, {{sir}}.", f"Bringing up {name}.", f"{name.capitalize()}, coming right up."])
    if action == "search" and name:
        return _pick([f"Searching for {name}.", f"Looking that up now, {{sir}}."])
    if action == "navigate" and name:
        return _pick([f"Pulling up {name}.", f"Navigating to {name}, {{sir}}."])
    if action == "multi_step":
        return _pick(["Right away, {sir}.", "On it.", "Consider it done."])
    if action in ("close", "minimize"):
        return None  # instant; the confirmation is enough
    return None


def done(action: str, target: Optional[str] = None, app: Optional[str] = None,
         result: Optional[str] = None, data: Optional[Dict] = None) -> Optional[str]:
    """Short confirmation after a task succeeded (None = the ack already said enough)."""
    data = data or {}
    if app == "whatsapp" and data.get("message"):
        return _pick([f"Message sent to {data.get('contact')}, {{sir}}.", f"Done. {data.get('contact')} has your message."])
    if action == "open":
        return None
    if action == "close" and target:
        return _pick([f"{target.capitalize()} closed.", f"I've closed {target}, {{sir}}."])
    if action == "minimize":
        return _pick(["Done.", "Cleared the decks, {sir}."])
    if action in ("type", "erase_and_type"):
        return _pick(["Typed.", "Done, {sir}."])
    if action in ("click", "press", "scroll", "select"):
        return None  # visible on screen; talking would just slow things down
    if action == "multi_step":
        return _pick(["All done, {sir}.", "That's everything, {sir}."])
    return _pick(["Done, {sir}.", "Taken care of."])


def failed(reason: str) -> str:
    reason = (reason or "something went wrong").rstrip(".")
    return _pick([f"I'm afraid I couldn't do that, {{sir}}. {reason}.",
                  f"That didn't go as planned, {{sir}}. {reason}."])
