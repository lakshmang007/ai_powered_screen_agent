"""
Voice training window: the user reads ~20 phrases, JARVIS learns their voice
(mic level, pauses, vocabulary, recurring mishearings) and reports the
accuracy before vs. after. Run with:  python main.py --train-voice
"""

import os
import json
import queue
import threading
import tkinter as tk
from pathlib import Path

from ..core import voice_training as vt

BG, PANEL, CYAN, TEXT, MUTED = "#05080d", "#0b1520", "#3fd6ff", "#d9f6ff", "#6c8a96"
GOOD, BAD, WARN = "#4dffa6", "#ff6b6b", "#ffb347"
REPORT_TXT = vt.ROOT / "logs" / "voice_training_report.txt"


def _known_contacts():
    try:
        data = json.loads((vt.ROOT / "data" / "whatsapp_contacts.json").read_text(encoding="utf-8"))
        return [v.get("search", k) if isinstance(v, dict) else str(v) for k, v in data.items()]
    except Exception:
        return []


class VoiceTrainerWindow:
    def __init__(self, master=None, on_finish=None):
        self.root = tk.Toplevel(master) if master else tk.Tk()
        self.root.title("JARVIS - Voice Training")
        self.root.geometry("720x500")
        self.root.configure(bg=BG)
        self.queue = queue.Queue()
        self.trainer = None
        self.index = 0
        self.cancelled = False
        self.redo = False
        self.skip = False
        self.on_finish = on_finish
        self.saved = False

        self.title = tk.Label(self.root, text="VOICE TRAINING", fg=CYAN, bg=BG, font=("Segoe UI Semibold", 18))
        self.title.pack(pady=(22, 4))
        self.subtitle = tk.Label(self.root, text="", fg=MUTED, bg=BG, font=("Segoe UI", 10), wraplength=640, justify="center")
        self.subtitle.pack()

        self.panel = tk.Frame(self.root, bg=PANEL, padx=24, pady=20)
        self.panel.pack(fill="both", expand=True, padx=28, pady=18)
        self.big = tk.Label(self.panel, text="", fg=TEXT, bg=PANEL, font=("Segoe UI", 20), wraplength=620, justify="center")
        self.big.pack(pady=(10, 14))
        self.status = tk.Label(self.panel, text="", fg=MUTED, bg=PANEL, font=("Segoe UI", 11))
        self.status.pack()
        self.heard = tk.Label(self.panel, text="", fg=MUTED, bg=PANEL, font=("Segoe UI", 11, "italic"), wraplength=620)
        self.heard.pack(pady=(8, 0))
        self.body = tk.Text(self.panel, height=12, bg=PANEL, fg=TEXT, relief="flat", font=("Consolas", 10),
                            wrap="word", highlightthickness=0)

        self.controls = tk.Frame(self.root, bg=BG)
        self.controls.pack(pady=(0, 18))
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self._intro()
        self._poll()

    # ------------------------------------------------------------------ screens
    def _button(self, text, command, color=CYAN):
        return tk.Button(self.controls, text=text, command=command, bg=PANEL, fg=color, activebackground="#13283a",
                         activeforeground=color, relief="flat", font=("Segoe UI Semibold", 10), padx=16, pady=6,
                         cursor="hand2")

    def _clear_controls(self):
        for w in self.controls.winfo_children():
            w.destroy()

    def _intro(self):
        self.subtitle.config(text="You'll read about 20 short commands. JARVIS learns your microphone, how you pause, "
                                  "your contacts' names and the words it tends to mishear from you. Takes ~3 minutes.")
        self.big.config(text="Who do you message on WhatsApp?", font=("Segoe UI", 16))
        self.status.config(text="Contact names, separated by commas (as they appear in WhatsApp)")
        self.names = tk.Entry(self.panel, font=("Segoe UI", 13), bg="#0f2030", fg=TEXT, insertbackground=TEXT,
                              relief="flat", justify="center", width=40)
        self.names.insert(0, ", ".join(_known_contacts() or ["Mohith"]))
        self.names.pack(pady=12, ipady=6)
        self.heard.config(text="Use your normal voice and microphone, in the room you usually use JARVIS in.")
        self._clear_controls()
        self._button("Start training", self._start).pack()

    def _start(self):
        names = [n.strip() for n in self.names.get().split(",") if n.strip()]
        self.names.destroy()
        self.trainer = vt.VoiceTrainer(names, self._transcribe)
        self._clear_controls()
        self._button("Re-record previous", self._redo, WARN).pack(side="left", padx=6)
        self._button("Skip this one", self._skip, MUTED).pack(side="left", padx=6)
        threading.Thread(target=self._record_all, daemon=True).start()

    # ------------------------------------------------------------------ audio worker
    def _ui(self, **changes):
        self.queue.put(changes)

    def _transcribe(self, audio, prompt):
        text = None
        if self._stt._groq_stt_client is not None:
            text = self._stt._transcribe_with_groq(audio, prompt)
        else:
            try:
                text = self._stt.recognizer.recognize_google(audio, language="en-IN")
            except Exception:
                text = None
        return self._stt._apply_phonetic_corrections(text) if text else ""

    def _record_all(self):
        import speech_recognition as sr
        from ..core.indian_english_voice_processor import IndianEnglishVoiceProcessor
        stt = IndianEnglishVoiceProcessor.__new__(IndianEnglishVoiceProcessor)
        stt.recognizer = sr.Recognizer()
        stt._init_stt_settings()
        stt.voice_profile = {}  # measure "before" without any previous training
        self._stt = stt
        rec = stt.recognizer
        rec.dynamic_energy_threshold = False
        rec.pause_threshold = 1.2
        rec.non_speaking_duration = 0.8

        try:
            mic = sr.Microphone()
            self._ui(big="Stay quiet for 3 seconds...", status="Measuring your room's background noise", heard="")
            with mic as source:
                noise = rec.record(source, duration=2.5)
            self.trainer.set_noise_sample(noise)
            rec.energy_threshold = max(120.0, self.trainer.noise_rms * 2.2)

            total = len(self.trainer.phrases)
            while self.index < total and not self.cancelled:
                i = self.index
                phrase = self.trainer.phrases[i]
                self.skip = False
                self._ui(big=f"“{phrase}”", status=f"Phrase {i + 1} of {total}  •  speak now",
                         status_color=CYAN, heard="")
                try:
                    with mic as source:
                        audio = rec.listen(source, timeout=10, phrase_time_limit=12)
                except sr.WaitTimeoutError:
                    if self.skip or self.cancelled:
                        self.index += 1
                        continue
                    self._ui(status="I didn't hear anything - let's try that again", status_color=WARN)
                    threading.Event().wait(1.5)
                    continue
                if self.skip:
                    self.index += 1
                    continue
                self._ui(status="Recognising...", status_color=MUTED)
                sample = self.trainer.add_sample(i, audio)
                ok = sample["wer"] == 0
                mark = "✓" if ok else "✗"
                heard_text = sample["heard"] or "(nothing)"
                self._ui(heard=f"Heard: “{heard_text}”   {mark}", heard_color=GOOD if ok else BAD)
                threading.Event().wait(1.4)
                if self.redo:
                    self.redo = False
                    self.index = max(0, self.index - 1)
                else:
                    self.index += 1

            if self.cancelled:
                return
            self._ui(big="Analysing your voice...", status="Re-checking every recording with your personal vocabulary",
                     heard="", controls="none")
            report = self.trainer.finish(progress=lambda n, t: self._ui(status=f"Re-checking recording {n} of {t}"))
            self.trainer.save()
            self.saved = True
            self._write_text_report(report)
            self._ui(report=report)
        except Exception as e:
            self._ui(big="Training stopped", status=f"Error: {e}", status_color=BAD)

    def _skip(self):
        # Takes effect when the current recording ends (speech or 10 s timeout)
        self.skip = True
        self._ui(status="Skipping after this recording...", status_color=MUTED)

    def _redo(self):
        self.redo = True

    # ------------------------------------------------------------------ results
    def _write_text_report(self, r):
        REPORT_TXT.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "JARVIS voice training report",
            f"Recordings: {r['samples']}",
            f"Word error rate: {r['wer_before']:.1%} -> {r['wer_after']:.1%}",
            f"Phrases recognised perfectly: {r['exact_before']} -> {r['exact_after']} of {r['samples']}",
            f"Background noise level: {r['noise_rms']:.0f}   your speech level: {r['speech_rms']:.0f}",
            f"Mic sensitivity (energy threshold): {r['energy_threshold']:.0f}",
            f"Your longest natural pause: {r['typical_pause']:.2f}s -> end-of-command pause set to {r['pause_threshold']:.2f}s",
            "Learned corrections: " + (", ".join(f"'{k}' -> '{v}'" for k, v in r["corrections"].items()) or "none needed"),
            "",
            "Per phrase (said | heard before | heard after):",
        ]
        for row in r["rows"]:
            mark = "OK " if row["wer_after"] == 0 else "ERR"
            lines.append(f"  {mark} {row['phrase']!r} | {row['before']!r} | {row['after']!r}")
        REPORT_TXT.write_text("\n".join(lines), encoding="utf-8")

    def _show_report(self, r):
        self.title.config(text="TRAINING COMPLETE")
        self.subtitle.config(text="Your voice profile is saved and JARVIS uses it from now on.")
        self.big.config(text=f"Accuracy  {1 - r['wer_before']:.0%}  →  {1 - r['wer_after']:.0%}",
                        font=("Segoe UI Semibold", 22), fg=GOOD if r["wer_after"] <= r["wer_before"] else WARN)
        self.status.config(text=f"Perfectly recognised: {r['exact_before']} → {r['exact_after']} of {r['samples']} phrases",
                           fg=TEXT)
        self.heard.config(text="")
        self.body.pack(fill="both", expand=True, pady=(10, 0))
        self.body.delete("1.0", "end")
        self.body.insert("end", REPORT_TXT.read_text(encoding="utf-8").split("\n", 1)[1])
        self.body.config(state="disabled")
        self._clear_controls()
        self._button("Done", self._close).pack()

    def _poll(self):
        try:
            while True:
                c = self.queue.get_nowait()
                if "big" in c:
                    self.big.config(text=c["big"])
                if "status" in c:
                    self.status.config(text=c["status"], fg=c.get("status_color", MUTED))
                if "heard" in c:
                    self.heard.config(text=c["heard"], fg=c.get("heard_color", MUTED))
                if c.get("controls") == "none":
                    self._clear_controls()
                if "report" in c:
                    self._show_report(c["report"])
        except queue.Empty:
            pass
        except tk.TclError:
            return
        self.root.after(80, self._poll)

    def _close(self):
        self.cancelled = True
        if self.saved and self.on_finish:
            try:
                self.on_finish()
            except Exception:
                pass
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def run(self):
        self.root.mainloop()


def run_voice_training():
    VoiceTrainerWindow().run()
