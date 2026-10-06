"""
Find on-screen controls by name with Windows UI Automation (UIA).

UIA reads the accessibility tree that apps expose (button labels, text boxes,
list items), so "click type a message" or "click the text box" can be resolved
to a real control instead of guessing from OCR'd pixels.
"""

import re
import logging
import threading
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# UIA control type ids
BUTTON, CHECKBOX, COMBOBOX, EDIT, HYPERLINK, LISTITEM, MENUITEM = 50000, 50002, 50003, 50004, 50005, 50007, 50011
TABITEM, TEXT, DOCUMENT = 50019, 50020, 50030
INTERACTIVE_TYPES = [BUTTON, CHECKBOX, COMBOBOX, EDIT, HYPERLINK, LISTITEM, MENUITEM, TABITEM, DOCUMENT, TEXT]
TYPE_PRIORITY = {EDIT: 0, BUTTON: 0, LISTITEM: 1, HYPERLINK: 1, MENUITEM: 1, TABITEM: 1,
                 CHECKBOX: 1, COMBOBOX: 1, DOCUMENT: 2, TEXT: 3}

# UIA property ids
NAME, RECT, CONTROL_TYPE, OFFSCREEN, HAS_FOCUS = 30005, 30001, 30003, 30022, 30008

# "click the text box" etc. mean "the text input", whatever its label is
TEXT_INPUT_WORDS = re.compile(
    r"\b(text\s*(box|field|area|container|input)|textbox|input(\s*(box|field))?|message\s*box|chat\s*box|"
    r"compose(\s*box)?|typing\s*(area|box)|search\s*(box|bar|field))\b", re.IGNORECASE)
FILLER_WORDS = {"the", "a", "an", "on", "button", "icon", "link", "tab", "option", "item", "menu", "field", "box"}

_local = threading.local()


def _uia():
    """One UIA client per thread (COM objects are bound to their thread's apartment)."""
    client = getattr(_local, "client", None)
    if client is None:
        import comtypes
        import comtypes.client
        try:
            comtypes.CoInitialize()
        except OSError:
            pass  # already initialised on this thread
        comtypes.client.GetModule("UIAutomationCore.dll")
        from comtypes.gen.UIAutomationClient import CUIAutomation, IUIAutomation
        client = comtypes.client.CreateObject(CUIAutomation, interface=IUIAutomation)
        _local.client = client
    return client


def list_controls(hwnd: int) -> List[Dict]:
    """All visible, named interactive controls in a window (deduplicated)."""
    from comtypes.gen.UIAutomationClient import TreeScope_Descendants
    uia = _uia()
    root = uia.ElementFromHandle(hwnd)

    type_cond = uia.CreatePropertyCondition(CONTROL_TYPE, INTERACTIVE_TYPES[0])
    for control_type in INTERACTIVE_TYPES[1:]:
        type_cond = uia.CreateOrCondition(type_cond, uia.CreatePropertyCondition(CONTROL_TYPE, control_type))
    cond = uia.CreateAndCondition(type_cond, uia.CreatePropertyCondition(OFFSCREEN, False))

    cache = uia.CreateCacheRequest()
    for prop in (NAME, RECT, CONTROL_TYPE, HAS_FOCUS):
        cache.AddProperty(prop)

    elements = root.FindAllBuildCache(TreeScope_Descendants, cond, cache)
    seen, controls = set(), []
    for i in range(elements.Length):
        element = elements.GetElement(i)
        r = element.CachedBoundingRectangle
        name = (element.CachedName or "").strip()
        if r.right <= r.left or r.bottom <= r.top:
            continue
        key = (name, r.left, r.top, element.CachedControlType)
        if key in seen:
            continue
        seen.add(key)
        controls.append({
            "name": name,
            "type": element.CachedControlType,
            "rect": (r.left, r.top, r.right - r.left, r.bottom - r.top),
            "focused": bool(element.CachedHasKeyboardFocus),
        })
    return controls


def _words(text: str) -> List[str]:
    return [w for w in re.findall(r"[a-z0-9+#']+", text.lower()) if w not in FILLER_WORDS]


def best_match(query: str, controls: List[Dict]) -> Optional[Dict]:
    """Pick the control the user most likely means by `query`."""
    query = query.strip().lower()
    wanted = _words(query)

    if TEXT_INPUT_WORDS.search(query):
        edits = [c for c in controls if c["type"] == EDIT]
        if not edits:
            # Some apps expose inputs as documents; skip the one wrapping the whole window
            biggest = max((c["rect"][2] * c["rect"][3] for c in controls), default=0)
            edits = [c for c in controls if c["type"] == DOCUMENT and c["rect"][2] * c["rect"][3] < 0.8 * biggest]
        if edits:
            if "search" in query:
                named = [c for c in edits if "search" in c["name"].lower()]
                return named[0] if named else min(edits, key=lambda c: c["rect"][1])  # top-most
            named = [c for c in edits if "message" in c["name"].lower()]
            if named:
                return named[0]
            focused = [c for c in edits if c["focused"]]
            # Message/compose boxes sit at the bottom of chat-style apps
            return focused[0] if focused else max(edits, key=lambda c: c["rect"][1])

    if not wanted:
        return None
    phrase = " ".join(wanted)
    scored = []
    for c in controls:
        name = c["name"].lower()
        if not name:
            continue
        name_words = _words(name)
        if name == query or " ".join(name_words) == phrase:
            score = 0
        elif name.startswith(phrase):
            score = 1
        elif re.search(rf"\b{re.escape(phrase)}\b", name):
            score = 2
        elif all(any(nw.startswith(w) for nw in name_words) for w in wanted):
            score = 3
        else:
            continue
        scored.append((score, TYPE_PRIORITY.get(c["type"], 4), len(name), c["rect"][1], c))
    if not scored:
        return None
    scored.sort(key=lambda s: s[:4])
    return scored[0][4]


def find_control(query: str, hwnd: Optional[int] = None) -> Optional[Dict]:
    """Find the control named like `query` in the given (default: foreground) window."""
    try:
        if hwnd is None:
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd:
            return None
        return best_match(query, list_controls(hwnd))
    except Exception as e:
        logger.debug(f"UI Automation lookup failed: {e}")
        return None
