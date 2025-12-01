"""
Macro recording module to capture mouse and keyboard events with timestamps.

- Records mouse moves/clicks/scroll and keyboard presses/releases using pynput
- Supports skipping events occurring inside a provided exclusion region (e.g., app window)
- Serializes to JSON for later playback or inspection
"""

from dataclasses import dataclass, asdict
from typing import Callable, Dict, List, Optional, Tuple, Any
import time
import json
import threading
import logging
from pathlib import Path

try:
    from pynput import mouse, keyboard
    HAS_PYNPUT = True
except Exception:
    HAS_PYNPUT = False
    mouse = None
    keyboard = None
    import pyautogui
else:
    import pyautogui


@dataclass
class MacroEvent:
    """Single macro event with relative timestamp."""
    t: float  # seconds since start
    type: str  # 'mouse_move', 'mouse_click', 'mouse_scroll', 'key_press', 'key_release'
    data: Dict[str, Any]


class MacroRecorder:
    """Records mouse and keyboard activity as a timeline of events."""

    def __init__(
        self,
        name: str,
        save_dir: str,
        exclude_predicate: Optional[Callable[[int, int], bool]] = None,
    ):
        """
        Args:
            name: Macro name (used as filename)
            save_dir: Directory to store macro JSON
            exclude_predicate: Function returning True if (x,y) should be excluded
        """
        self.name = name
        self.save_dir = Path(save_dir)
        self.exclude_predicate = exclude_predicate
        self.logger = logging.getLogger(__name__)

        self._events: List[MacroEvent] = []
        self._start_time: float = 0.0
        self._running = False
        self._lock = threading.Lock()

        self._mouse_listener = None
        self._keyboard_listener = None

    @property
    def events(self) -> List[MacroEvent]:
        with self._lock:
            return list(self._events)

    def start(self):
        if not HAS_PYNPUT:
            raise RuntimeError("pynput is not available. Please install dependencies.")

        if self._running:
            return

        self._events.clear()
        self._start_time = time.time()
        self._running = True

        # Mouse callbacks
        def on_move(x, y):
            if not self._running:
                return False
            if self.exclude_predicate and self.exclude_predicate(int(x), int(y)):
                return
            self._append_event('mouse_move', {'x': int(x), 'y': int(y)})

        def on_click(x, y, button, pressed):
            if not self._running:
                return False
            if self.exclude_predicate and self.exclude_predicate(int(x), int(y)):
                return
            self._append_event('mouse_click', {
                'x': int(x), 'y': int(y), 'button': str(button), 'pressed': bool(pressed)
            })

        def on_scroll(x, y, dx, dy):
            if not self._running:
                return False
            # Always record scroll events - they are usually intentional user actions
            # even if they occur within the app window
            self._append_event('mouse_scroll', {'x': int(x), 'y': int(y), 'dx': int(dx), 'dy': int(dy)})

        # Keyboard callbacks
        def on_press(key):
            if not self._running:
                return False
            self._append_event('key_press', {'key': self._key_to_str(key)})

        def on_release(key):
            if not self._running:
                return False
            self._append_event('key_release', {'key': self._key_to_str(key)})

        self._mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
        self._keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)

        self._mouse_listener.start()
        self._keyboard_listener.start()
        self.logger.info("Macro recording started")

    def stop_and_save(self) -> Path:
        if not self._running:
            raise RuntimeError("Recorder not running")
        self._running = False

        try:
            if self._mouse_listener:
                self._mouse_listener.stop()
            if self._keyboard_listener:
                self._keyboard_listener.stop()
        except Exception:
            pass

        self.save_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.save_dir / f"{self._sanitize(self.name)}.json"
        payload = {
            'name': self.name,
            'created_at': time.time(),
            'duration': self.duration(),
            'events': [asdict(e) for e in self.events],
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)
        self.logger.info("Macro saved: %s", output_path)
        return output_path

    def stop(self):
        """Stop recording without saving."""
        if not self._running:
            return
        self._running = False

        try:
            if self._mouse_listener:
                self._mouse_listener.stop()
            if self._keyboard_listener:
                self._keyboard_listener.stop()
        except Exception:
            pass

    def save(self) -> Path:
        """Save the recorded macro to file."""
        if self._running:
            raise RuntimeError("Cannot save while recording. Stop recording first.")
        
        self.save_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.save_dir / f"{self._sanitize(self.name)}.json"
        payload = {
            'name': self.name,
            'created_at': time.time(),
            'duration': self.duration(),
            'events': [asdict(e) for e in self.events],
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)
        self.logger.info("Macro saved: %s", output_path)
        return output_path

    def duration(self) -> float:
        if not self._start_time:
            return 0.0
        last_t = self.events[-1].t if self.events else 0.0
        return last_t

    def trim(self, start_s: float, end_s: float) -> List[MacroEvent]:
        """Trim events to a time range, returning new event instances with rebased timestamps."""
        with self._lock:
            trimmed = [e for e in self._events if start_s <= e.t <= end_s]
            # Rebase timestamps so trimmed starts at 0
            # Create NEW MacroEvent instances to avoid modifying originals
            if trimmed:
                base = trimmed[0].t
                trimmed = [MacroEvent(t=e.t - base, type=e.type, data=e.data.copy()) for e in trimmed]
            return trimmed

    def _append_event(self, event_type: str, data: Dict[str, Any]):
        rel_t = time.time() - self._start_time
        event = MacroEvent(t=rel_t, type=event_type, data=data)
        with self._lock:
            self._events.append(event)

    @staticmethod
    def _key_to_str(key) -> str:
        try:
            return key.char if hasattr(key, 'char') and key.char is not None else str(key)
        except Exception:
            return str(key)

    @staticmethod
    def _sanitize(name: str) -> str:
        invalid = '<>:"/\\|?*'
        for ch in invalid:
            name = name.replace(ch, '_')
        return name.strip()

    # -------- Playback utilities --------
    @staticmethod
    def play_events(events: List[MacroEvent], speed: float = 1.0, scroll_amplifier: float = 3.0):
        """
        Play a sequence of events respecting their relative timestamps.

        Args:
            events: Event list (MacroEvent)
            speed: Speed multiplier (>1.0 faster)
            scroll_amplifier: Multiplier for scroll amounts to make them more noticeable (default: 3.0)
        """
        logger = logging.getLogger(__name__)
        if not events:
            logger.info("No events to play")
            return
        
        logger.info(f"Playing {len(events)} events...")
        start_t = events[0].t
        base = start_t
        t0 = time.time()
        
        for i, e in enumerate(events):
            target_dt = (e.t - base) / max(speed, 0.1)
            now_dt = time.time() - t0
            if target_dt > now_dt:
                time.sleep(target_dt - now_dt)
            try:
                logger.debug(f"Event {i+1}/{len(events)}: {e.type} - {e.data}")
                if e.type == 'mouse_move':
                    x = int(e.data.get('x', 0)); y = int(e.data.get('y', 0))
                    pyautogui.moveTo(x, y, duration=0)
                elif e.type == 'mouse_click':
                    x = int(e.data.get('x', 0)); y = int(e.data.get('y', 0))
                    btn = str(e.data.get('button', 'Button.left')).lower()
                    button = 'left' if 'left' in btn else ('right' if 'right' in btn else 'middle')
                    pressed = bool(e.data.get('pressed', True))
                    pyautogui.moveTo(x, y, duration=0)
                    if pressed:
                        pyautogui.mouseDown(button=button)
                    else:
                        pyautogui.mouseUp(button=button)
                elif e.type == 'mouse_scroll':
                    x = int(e.data.get('x', 0)); y = int(e.data.get('y', 0))
                    dx = int(e.data.get('dx', 0)); dy = int(e.data.get('dy', 0))
                    pyautogui.moveTo(x, y, duration=0)
                    # pyautogui scroll uses vertical clicks only
                    if dy != 0:
                        # Amplify scroll amount for better visibility
                        scroll_amount = int(dy * scroll_amplifier)
                        pyautogui.scroll(scroll_amount, x=x, y=y)
                elif e.type == 'key_press':
                    key_str = str(e.data.get('key', ''))
                    MacroRecorder._handle_key_press(key_str)
                elif e.type == 'key_release':
                    key_str = str(e.data.get('key', ''))
                    MacroRecorder._handle_key_release(key_str)
            except Exception as ex:
                # Log individual playback errors but continue
                logger.warning(f"Error playing event {e.type}: {ex}")
                # Continue with next event
        
        logger.info(f"Finished playing {len(events)} events")

    @staticmethod
    def _handle_key_press(key_str: str):
        """Handle key press event during playback."""
        key = MacroRecorder._normalize_key(key_str)
        if MacroRecorder._is_modifier(key):
            # For modifiers, hold them down
            try:
                pyautogui.keyDown(key)
                return
            except Exception:
                pass
        else:
            # For non-modifier keys, press and release immediately
            # This handles the full key action
            try:
                pyautogui.press(key)
            except Exception as e:
                # If press fails, try typing it as a character
                try:
                    pyautogui.write(key_str)
                except Exception:
                    pass

    @staticmethod
    def _handle_key_release(key_str: str):
        """Handle key release event during playback."""
        key = MacroRecorder._normalize_key(key_str)
        if MacroRecorder._is_modifier(key):
            # Only release modifiers (they were held down)
            try:
                pyautogui.keyUp(key)
            except Exception:
                pass
        # For non-modifier keys, do nothing on release
        # (the press event already handled the full key action)

    @staticmethod
    def _normalize_key(key_str: str) -> str:
        # Convert pynput key string to pyautogui key name
        key_str = key_str.replace('Key.', '').lower()
        mapping = {
            'ctrl_l': 'ctrl', 'ctrl_r': 'ctrl', 'control': 'ctrl',
            'shift': 'shift', 'shift_l': 'shift', 'shift_r': 'shift',
            'alt_l': 'alt', 'alt_r': 'alt', 'alt_gr': 'alt',
            'cmd': 'win', 'cmd_r': 'win', 'cmd_l': 'win', 'windows': 'win',
            'enter': 'enter', 'return': 'enter', 'space': 'space', 'tab': 'tab',
            'backspace': 'backspace', 'delete': 'delete', 'insert': 'insert',
            'esc': 'esc', 'escape': 'esc',
            'up': 'up', 'down': 'down', 'left': 'left', 'right': 'right',
            'page_up': 'pageup', 'page_down': 'pagedown', 'home': 'home', 'end': 'end',
            'caps_lock': 'capslock', 'print_screen': 'printscreen',
        }
        if key_str.startswith('f') and key_str[1:].isdigit():
            return key_str  # function keys f1..f24
        if key_str in mapping:
            return mapping[key_str]
        return key_str

    @staticmethod
    def _is_modifier(key: str) -> bool:
        return key in {'ctrl', 'shift', 'alt', 'win'}

    @staticmethod
    def play_file(path: str, speed: float = 1.0, scroll_amplifier: float = 3.0):
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(str(p))
        with open(p, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        events = [MacroEvent(**e) for e in payload.get('events', [])]
        MacroRecorder.play_events(events, speed=speed, scroll_amplifier=scroll_amplifier)



