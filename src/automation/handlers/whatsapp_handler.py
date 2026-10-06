"""
WhatsApp Desktop automation: open a chat by contact name and send a message.

Flow (no phone numbers needed):
1. Bring WhatsApp Desktop to the front (launch it via the whatsapp: protocol if needed)
2. Search the contact in the chat list and open the matching chat
3. Verify with OCR that the chat header shows the contact's name
4. Paste the message (clipboard, so emoji / non-ASCII work) and press Enter

Step 3 is a hard gate: if the open chat can't be confirmed, nothing is typed or sent.

Optional data/whatsapp_contacts.json maps spoken names to what to search for, and
optionally a phone number (then the official whatsapp://send link is used):
    {"mohit": {"search": "Mohith"}, "mom": {"search": "Amma", "phone": "+91XXXXXXXXXX"}}
"""

import os
import re
import json
import time
import logging
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple, Any
from urllib.parse import quote

try:
    import pygetwindow as gw
    HAS_PYGETWINDOW = True
except ImportError:
    gw = None
    HAS_PYGETWINDOW = False

from ..task_engine import TaskResult, TaskStatus
from ...core.nlp_processor import ParsedCommand, ActionType

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONTACTS_FILE = PROJECT_ROOT / "data" / "whatsapp_contacts.json"

_WA = r"whats\s?app"
_FILLER_PREFIX = r"^(?:(?:hey\s+)?jarvis[,\s]+|please\s+|can you\s+|could you\s+)+"


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" ,.!?\"'")


def _clean_name(name: str) -> str:
    name = _clean(name)
    name = re.sub(r"^(?:the\s+|my\s+)", "", name, flags=re.IGNORECASE)
    name = re.sub(r"(?:'s)?\s+(?:chat|conversation|contact)$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"'s$", "", name)
    return _clean(name)


def parse_whatsapp_request(text: str) -> Optional[Dict[str, Optional[str]]]:
    """
    Extract {'contact', 'message'} from a WhatsApp request, or None if the text
    isn't a WhatsApp request. 'message' is None for "open X's chat" requests.

    Handles e.g.
      "send reply as coming to mohith in whatsapp"
      "send yeah I'm coming to Mohith on WhatsApp"
      "open whatsapp, go to mohith chat and type and send yeah iam coming"
      "whatsapp mohith saying I'll be late"
      "message mohith on whatsapp that I'm on the way"
      "on whatsapp send hi to mohith"
      "open whatsapp and go to mohith chat"
    """
    if not text or not re.search(rf"\b{_WA}\b", text, re.IGNORECASE):
        return None

    t = re.sub(r"\s+", " ", text).strip()
    t = re.sub(_FILLER_PREFIX, "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+jarvis[.!?]*$", "", t, flags=re.IGNORECASE)
    I = re.IGNORECASE

    msg_word = r"(?:a\s+)?(?:message|msg|reply|text)"
    lead = r"(?:saying|as|that|like|:)"

    patterns = [
        # open whatsapp, go to mohith chat and type and send yeah iam coming
        rf"{_WA}\b.*?\b(?:go to|open|search(?: for)?|find)\s+(?P<name>.+?)(?:'s)?\s+(?:chat|conversation)\b"
        rf"(?:\s*(?:,|and|then)\s*)+(?:type|write|send|say)(?:\s+(?:and|then)\s+(?:send|enter|hit enter))?\s*{lead}?\s+(?P<msg>.+)$",
        # on whatsapp send hi to mohith
        rf"^(?:on|in|using|via)\s+{_WA}[,\s]+send\s+(?:{msg_word}\s+)?{lead}?\s*(?P<msg>.+?)\s+to\s+(?P<name>.+)$",
        # send reply as coming to mohith in whatsapp / send hi to mohith on whatsapp
        rf"^send\s+(?:{msg_word}\s+)?{lead}?\s*(?P<msg>.+?)\s+to\s+(?P<name>.+?)\s+(?:on|in|via|through|using|over)\s+{_WA}$",
        # send mohith a message saying hi on whatsapp
        rf"^send\s+(?P<name>.+?)\s+{msg_word}\s+{lead}\s+(?P<msg>.+?)(?:\s+(?:on|in|via)\s+{_WA})?$",
        # message mohith on whatsapp that I'm on the way
        rf"^(?:message|text|whatsapp|ping)\s+(?P<name>.+?)\s+(?:on|in|via)\s+{_WA}\s+{lead}\s+(?P<msg>.+)$",
        # whatsapp mohith saying I'll be late / message mohith saying hi on whatsapp
        rf"^(?:{_WA}|message|text|ping)\s+(?:to\s+)?(?P<name>.+?)\s+{lead}\s+(?P<msg>.+?)(?:\s+(?:on|in|via)\s+{_WA})?$",
        # tell mohith on whatsapp that ...
        rf"^tell\s+(?P<name>.+?)\s+(?:on|in|via)\s+{_WA}\s+(?:that\s+)?(?P<msg>.+)$",
    ]
    for pattern in patterns:
        m = re.search(pattern, t, I)
        if m:
            name, msg = _clean_name(m.group("name")), _clean(m.group("msg"))
            if name and msg and not re.fullmatch(_WA, name, I):
                return {"contact": name, "message": msg}

    # Open a chat without sending: "open whatsapp and go to mohith chat"
    m = re.search(rf"{_WA}\b.*?\b(?:go to|open|search(?: for)?|find)\s+(?P<name>.+?)(?:'s)?\s+(?:chat|conversation)\s*$", t, I) or \
        re.search(rf"^open\s+(?P<name>.+?)(?:'s)?\s+(?:chat|conversation)\s+(?:on|in)\s+{_WA}$", t, I)
    if m:
        name = _clean_name(m.group("name"))
        if name:
            return {"contact": name, "message": None}
    return None


class WhatsAppHandler:
    """Automates WhatsApp Desktop on Windows."""

    WINDOW_TITLE = "WhatsApp"

    def __init__(self, screen_agent, confirm_callback: Optional[Callable[[str, str], bool]] = None):
        """
        Args:
            screen_agent: ScreenAgent used for keys, typing and OCR
            confirm_callback: optional fn(contact, message) -> bool asked before sending
        """
        self.screen_agent = screen_agent
        self.confirm_callback = confirm_callback
        self.logger = logging.getLogger(__name__)
        self.contacts = self._load_contacts()

    # ------------------------------------------------------------------ public API
    def handle_command(self, command: ParsedCommand) -> TaskResult:
        params = command.parameters or {}
        contact = params.get("contact") or command.target
        message = params.get("message")
        if contact and re.fullmatch(_WA, contact.strip(), re.IGNORECASE):
            contact = None  # "open whatsapp" -> target is the app, not a person

        if not contact and command.raw_text:
            parsed = parse_whatsapp_request(command.raw_text)
            if parsed:
                contact, message = parsed["contact"], parsed["message"]

        if command.action == ActionType.OPEN and not contact:
            return self.open_whatsapp()
        if not contact:
            return TaskResult(TaskStatus.FAILED, "Tell me who to message, e.g. 'send hi to Mohith on WhatsApp'")
        if message:
            return self.send_message(contact, message)
        return self.open_chat(contact)

    def open_whatsapp(self) -> TaskResult:
        window = self._focus_whatsapp()
        if not window:
            return TaskResult(TaskStatus.FAILED, "Couldn't open WhatsApp Desktop")
        return TaskResult(TaskStatus.COMPLETED, "Opened WhatsApp")

    def open_chat(self, contact: str, dry_run: bool = False) -> TaskResult:
        """Open the chat for `contact`. dry_run only searches (opens nothing)."""
        entry = self._lookup(contact)
        window = self._focus_whatsapp()
        if not window:
            return TaskResult(TaskStatus.FAILED, "Couldn't open WhatsApp Desktop")

        search_name = entry["search"]
        if not self._search(search_name):
            return TaskResult(TaskStatus.FAILED, f"Couldn't search for {search_name} in WhatsApp")

        hit = self._find_in_results(window, search_name)
        if dry_run:
            self.screen_agent.press_key("escape")
            if hit:
                return TaskResult(TaskStatus.COMPLETED, f"Dry run: found '{search_name}' in WhatsApp search",
                                  data={"result_box": hit})
            return TaskResult(TaskStatus.FAILED, f"Dry run: '{search_name}' not visible in search results")

        if hit:
            x, y, w, h = hit
            self.screen_agent.click_element(x + w // 2, y + h // 2)
        else:
            # No OCR match: fall back to opening the top search result from the keyboard
            self.screen_agent.press_key("down")
            time.sleep(0.2)
            self.screen_agent.press_key("enter")
        time.sleep(1.2)

        if not self._chat_is_open_for(window, search_name):
            self.screen_agent.press_key("escape")
            return TaskResult(TaskStatus.FAILED,
                              f"Couldn't confirm that {search_name}'s chat is open, so I stopped.")
        return TaskResult(TaskStatus.COMPLETED, f"Opened {search_name}'s chat")

    def _chat_is_open_for(self, window, name: str) -> bool:
        """Verify the open chat belongs to `name`.

        Primary: the message box's accessible name, "Type a message to <Contact>".
        Fallback (UI Automation unavailable): OCR of the chat header.
        """
        composer = self._composer_element()
        if composer is not None:
            label = composer.CurrentName.lower()
            return any(word.lower() in label for word in self._name_words(name))
        return self._chat_header_matches(window, name)

    def _composer_element(self):
        """The WhatsApp message box via Windows UI Automation, or None."""
        window = self._whatsapp_window()
        if window is None or not isinstance(getattr(window, "_hWnd", None), int):
            return None
        try:
            import comtypes.client
            comtypes.client.GetModule('UIAutomationCore.dll')
            from comtypes.gen.UIAutomationClient import CUIAutomation, IUIAutomation, TreeScope_Descendants
            if not hasattr(self, "_uia"):
                self._uia = comtypes.client.CreateObject(CUIAutomation, interface=IUIAutomation)
            root = self._uia.ElementFromHandle(window._hWnd)
            edits = root.FindAll(TreeScope_Descendants,
                                 self._uia.CreatePropertyCondition(30003, 50004))  # ControlType == Edit
            for i in range(edits.Length):
                element = edits.GetElement(i)
                if element.CurrentName.lower().startswith("type a message"):
                    return element
        except Exception as e:
            self.logger.debug(f"UI Automation unavailable: {e}")
        return None

    def send_message(self, contact: str, message: str, dry_run: bool = False) -> TaskResult:
        """Send `message` to `contact`. dry_run does everything except pressing Enter,
        then clears the draft again (used for testing without messaging anyone)."""
        entry = self._lookup(contact)
        display = entry["search"]

        if self.confirm_callback and not self.confirm_callback(display, message):
            return TaskResult(TaskStatus.CANCELLED, "Message not sent (cancelled)")

        if entry.get("phone"):
            opened = self._open_chat_by_phone(entry["phone"])
        else:
            opened = self.open_chat(contact)
        if opened.status != TaskStatus.COMPLETED:
            return opened

        if not self._focus_composer():
            return TaskResult(TaskStatus.FAILED, "Opened the chat but couldn't focus the message box")
        if not self._paste_text(message):
            return TaskResult(TaskStatus.FAILED, "Couldn't type the message")
        time.sleep(0.3)

        # Make sure the text is in this chat's message box before pressing Enter
        draft = self._composer_text()
        if draft is not None and message.strip() not in draft:
            self.screen_agent.key_combination("ctrl", "a")
            self.screen_agent.press_key("delete")
            return TaskResult(TaskStatus.FAILED, "The message didn't land in the message box, so I didn't send it")

        if dry_run:
            self.screen_agent.key_combination("ctrl", "a")
            self.screen_agent.press_key("delete")
            return TaskResult(TaskStatus.COMPLETED, f"Dry run: '{message}' was ready to send to {display} (cleared, not sent)",
                              data={"contact": display, "message": message, "draft_verified": draft is not None})

        self.screen_agent.press_key("enter")
        return TaskResult(TaskStatus.COMPLETED, f"Sent '{message}' to {display} on WhatsApp",
                          data={"contact": display, "message": message})

    def _composer_text(self) -> Optional[str]:
        """Current text in the message box (UI Automation Value), or None if unreadable."""
        composer = self._composer_element()
        if composer is None:
            return None
        try:
            value = composer.GetCurrentPropertyValue(30045)  # UIA_ValueValuePropertyId
            return value if isinstance(value, str) else None
        except Exception:
            return None

    # ------------------------------------------------------------------ helpers
    def _load_contacts(self) -> Dict[str, Dict[str, str]]:
        try:
            with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {k.lower(): (v if isinstance(v, dict) else {"search": str(v)}) for k, v in data.items()}
        except FileNotFoundError:
            return {}
        except Exception as e:
            self.logger.warning(f"Couldn't read {CONTACTS_FILE}: {e}")
            return {}

    def _lookup(self, contact: str) -> Dict[str, str]:
        entry = dict(self.contacts.get(contact.lower(), {}))
        entry.setdefault("search", contact)
        return entry

    def _whatsapp_window(self):
        if not HAS_PYGETWINDOW:
            return None
        for w in gw.getWindowsWithTitle(self.WINDOW_TITLE):
            if w.title.strip() == self.WINDOW_TITLE and w.width > 200:
                return w
        return None

    def _is_foreground(self) -> bool:
        try:
            active = gw.getActiveWindow()
            return bool(active and active.title.strip() == self.WINDOW_TITLE)
        except Exception:
            return False

    def _focus_whatsapp(self, timeout: float = 15.0):
        """Bring WhatsApp to the front; the whatsapp: protocol launches or focuses it."""
        if self._is_foreground():
            return self._whatsapp_window()
        try:
            os.startfile("whatsapp:")
        except OSError as e:
            self.logger.error(f"Couldn't launch WhatsApp: {e}")
            return None

        deadline = time.time() + timeout
        while time.time() < deadline:
            window = self._whatsapp_window()
            if window:
                if window.isMinimized:
                    window.restore()
                if not self._is_foreground():
                    try:
                        window.activate()
                    except Exception:
                        pass
                if self._is_foreground():
                    time.sleep(0.8)  # let the UI settle
                    return window
            time.sleep(0.4)
        return None

    def _search(self, name: str) -> bool:
        # Ctrl+F focuses "Search or start a new chat"; Ctrl+A clears earlier text
        if not self.screen_agent.key_combination("ctrl", "f"):
            return False
        time.sleep(0.5)
        self.screen_agent.key_combination("ctrl", "a")
        if not self._paste_text(name):
            return False
        time.sleep(1.5)  # results load asynchronously
        return True

    def _window_region(self, window) -> Dict[str, int]:
        return {"left": max(window.left, 0), "top": max(window.top, 0),
                "width": window.width, "height": window.height}

    def _ocr_in_window(self, window, text: str, area: Tuple[float, float, float, float]):
        """OCR-search `text` inside a fractional area (x0, y0, x1, y1) of the window.
        Returns boxes in screen coordinates."""
        region = self._window_region(window)
        x0, y0, x1, y1 = area
        sub = {
            "left": region["left"] + int(region["width"] * x0),
            "top": region["top"] + int(region["height"] * y0),
            "width": int(region["width"] * (x1 - x0)),
            "height": int(region["height"] * (y1 - y0)),
        }
        shot = self.screen_agent.capture_screen(sub)
        if shot is None:
            return []
        matches = []
        for word in self._name_words(text):
            for (x, y, w, h) in self.screen_agent.find_text_on_screen(word, shot):
                matches.append((sub["left"] + x, sub["top"] + y, w, h))
            if matches:
                break
        return matches

    @staticmethod
    def _name_words(name: str):
        # Try the full name first, then the longest word (OCR splits on spaces;
        # speech gives "mohit" for "Mohith", which still matches as a prefix)
        words = sorted(name.split(), key=len, reverse=True)
        return [name] + [w for w in words if len(w) >= 3 and w != name]

    def _find_in_results(self, window, name: str):
        # Chat list: left part of the window, below the search box
        matches = self._ocr_in_window(window, name, (0.0, 0.12, 0.5, 0.95))
        if not matches:
            return None
        return min(matches, key=lambda b: b[1])  # top-most result

    def _chat_header_matches(self, window, name: str) -> bool:
        # Header of the open chat: top strip of the right-hand pane
        return bool(self._ocr_in_window(window, name, (0.25, 0.0, 1.0, 0.12)))

    def _focus_composer(self) -> bool:
        window = self._whatsapp_window()
        if not window or not self._is_foreground():
            return False
        composer = self._composer_element()
        if composer is not None:
            if composer.CurrentHasKeyboardFocus:
                return True
            rect = composer.CurrentBoundingRectangle
            self.screen_agent.click_element((rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2)
            time.sleep(0.3)
            return bool(self._composer_element() and self._composer_element().CurrentHasKeyboardFocus)
        boxes = self._ocr_in_window(window, "Type a message", (0.25, 0.8, 1.0, 1.0))
        if boxes:
            x, y, w, h = boxes[0]
            self.screen_agent.click_element(x + w // 2, y + h // 2)
            time.sleep(0.3)
        # Opening a chat already focuses the composer, so no match is fine
        return True

    def _paste_text(self, text: str) -> bool:
        """Type via the clipboard (handles emoji/Unicode), restoring the old clipboard."""
        try:
            import win32clipboard
            win32clipboard.OpenClipboard()
            try:
                previous = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            except Exception:
                previous = None
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()

            ok = self.screen_agent.key_combination("ctrl", "v")
            time.sleep(0.3)

            if previous is not None:
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(previous, win32clipboard.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
            return ok
        except Exception as e:
            self.logger.warning(f"Clipboard paste failed ({e}); typing instead")
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass
            return self.screen_agent.type_text(text)

    def _open_chat_by_phone(self, phone: str) -> TaskResult:
        digits = re.sub(r"\D", "", phone)
        try:
            os.startfile(f"whatsapp://send?phone={digits}")
        except OSError as e:
            return TaskResult(TaskStatus.FAILED, f"Couldn't open WhatsApp chat: {e}")
        time.sleep(2.5)
        if not self._focus_whatsapp():
            return TaskResult(TaskStatus.FAILED, "WhatsApp didn't come to the front")
        return TaskResult(TaskStatus.COMPLETED, "Opened chat")


def format_confirmation(contact: str, message: str) -> str:
    return f"Send '{message}' to {contact} on WhatsApp?"
