"""
JARVIS HUD: a small always-on-top arc-reactor display.

Modes animate the reactor: idle (dim), listening (pulsing ring), thinking
(spinning arcs), speaking (equaliser bars), success / error (flash).
Everything is driven through a queue, so any thread can update it safely.
"""

import math
import queue
import random
import tkinter as tk

BG = "#05080d"
CYAN = "#3fd6ff"
CYAN_DIM = "#145a73"
TEXT = "#d9f6ff"
MUTED = "#6c8a96"
MODE_COLORS = {"idle": CYAN_DIM, "listening": CYAN, "thinking": "#ffb347",
               "speaking": CYAN, "success": "#4dffa6", "error": "#ff5c5c"}

# Old callers pass a colour with update_status(); map those onto modes
_COLOR_TO_MODE = {"#00ffff": "listening", "#00ff00": "listening", "#ffff00": "thinking",
                  "#ffa500": "thinking", "#ff0000": "error", "#ff4444": "error",
                  "#888888": "idle", "#555555": "idle"}


class JarvisOverlay:
    WIDTH, HEIGHT = 440, 150

    def __init__(self, master=None, on_interrupt=None):
        self.root = tk.Toplevel(master) if master else tk.Tk()
        self.root.title("JARVIS")
        screen_w = self.root.winfo_screenwidth()
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{screen_w - self.WIDTH - 24}+24")  # top-right
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.92)
        self.root.configure(bg=BG)

        self.on_interrupt = on_interrupt
        self.queue = queue.Queue()
        self._closed = False
        self.mode = "idle"
        self.tick = 0
        self.flash_until = 0

        self.canvas = tk.Canvas(self.root, width=self.WIDTH, height=self.HEIGHT, bg=BG, highlightthickness=1,
                                highlightbackground=CYAN_DIM)
        self.canvas.pack(fill="both", expand=True)

        # Text area
        self.title_id = self.canvas.create_text(150, 22, text="J.A.R.V.I.S.", anchor="w", fill=CYAN,
                                                font=("Segoe UI Semibold", 13))
        self.status_id = self.canvas.create_text(150, 46, text="Initialising...", anchor="w", fill=MUTED,
                                                 font=("Segoe UI", 9))
        self.user_id = self.canvas.create_text(150, 74, text="", anchor="nw", fill=MUTED, width=270,
                                               font=("Segoe UI", 9, "italic"))
        self.reply_id = self.canvas.create_text(150, 96, text="", anchor="nw", fill=TEXT, width=270,
                                                font=("Segoe UI", 10))

        # Buttons
        self.stop_btn = tk.Button(self.root, text="■ STOP", command=self.handle_interrupt, bg="#1a0d0d", fg="#ff7070",
                                  activebackground="#2a1111", activeforeground="#ff9090", relief="flat",
                                  font=("Segoe UI", 8, "bold"), padx=6, pady=0, bd=0, cursor="hand2")
        self.canvas.create_window(self.WIDTH - 12, 12, window=self.stop_btn, anchor="ne")

        # Dragging
        for widget in (self.canvas,):
            widget.bind('<Button-1>', self.start_move)
            widget.bind('<B1-Motion>', self.do_move)

        self.check_queue()
        self._animate()

    # ------------------------------------------------------------ public API
    def set_mode(self, mode: str, status: str = None):
        self.queue.put(("mode", mode, status))

    def update_status(self, text, color="#00FFFF"):
        mode = _COLOR_TO_MODE.get(str(color).lower())
        self.queue.put(("mode", mode, text) if mode else ("status", text))

    def update_text(self, text):
        self.queue.put(("reply", text))

    def show_user(self, text):
        self.queue.put(("user", text))

    def close(self):
        """Close the overlay. Safe to call from any thread."""
        if not self._closed:
            self.queue.put(("close",))

    def run(self):
        self.root.mainloop()

    # ------------------------------------------------------------ internals
    def start_move(self, event):
        self._drag = (event.x, event.y)

    def do_move(self, event):
        x = self.root.winfo_x() + event.x - self._drag[0]
        y = self.root.winfo_y() + event.y - self._drag[1]
        self.root.geometry(f"+{x}+{y}")

    def handle_interrupt(self):
        if self.on_interrupt:
            self.on_interrupt()

    def check_queue(self):
        if self._closed:
            return
        try:
            while True:
                msg = self.queue.get_nowait()
                kind = msg[0]
                if kind == "mode":
                    _, mode, status = msg
                    if mode:
                        self.mode = mode
                        if mode in ("success", "error"):
                            self.flash_until = self.tick + 25
                    if status is not None:
                        self.canvas.itemconfig(self.status_id, text=status)
                elif kind == "status":
                    self.canvas.itemconfig(self.status_id, text=msg[1])
                elif kind == "reply":
                    self.canvas.itemconfig(self.reply_id, text=self._shorten(msg[1], 160))
                elif kind == "user":
                    self.canvas.itemconfig(self.user_id, text=f"“{self._shorten(msg[1], 70)}”")
                elif kind == "close":
                    self._destroy()
                    return
        except queue.Empty:
            pass
        self.root.after(60, self.check_queue)

    @staticmethod
    def _shorten(text, limit):
        text = str(text or "")
        return text if len(text) <= limit else text[:limit - 1] + "…"

    def _animate(self):
        if self._closed:
            return
        self.tick += 1
        mode = self.mode
        if mode in ("success", "error") and self.tick > self.flash_until:
            mode = self.mode = "idle"
        color = MODE_COLORS.get(mode, CYAN)
        c, cx, cy = self.canvas, 72, 75
        c.delete("reactor")

        # Outer ring segments (rotate while thinking)
        spin = self.tick * (9 if mode == "thinking" else 1.2)
        for i in range(8):
            start = spin + i * 45
            c.create_arc(cx - 56, cy - 56, cx + 56, cy + 56, start=start, extent=30, style="arc",
                         outline=color if mode != "idle" else CYAN_DIM, width=3, tags="reactor")

        # Pulse ring (breathes while listening)
        pulse = (math.sin(self.tick / 4) + 1) / 2 if mode == "listening" else 0.3
        r = 38 + pulse * 6
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=2, tags="reactor")

        # Core
        core = 20 + (pulse * 3 if mode == "listening" else 0)
        c.create_oval(cx - core, cy - core, cx + core, cy + core, fill=color if mode != "idle" else CYAN_DIM,
                      outline="", tags="reactor")
        c.create_oval(cx - 9, cy - 9, cx + 9, cy + 9, fill=BG, outline="", tags="reactor")

        # Equaliser bars inside the core while speaking
        if mode == "speaking":
            for i in range(5):
                h = 3 + random.random() * 12
                x = cx - 10 + i * 5
                c.create_line(x, cy - h / 2, x, cy + h / 2, fill=TEXT, width=2, tags="reactor")

        c.itemconfig(self.title_id, fill=color if mode != "idle" else CYAN)
        self.root.after(50, self._animate)

    def _destroy(self):
        if self._closed:
            return
        self._closed = True
        try:
            self.root.destroy()
        except tk.TclError:
            pass
