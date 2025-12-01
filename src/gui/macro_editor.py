import tkinter as tk
from tkinter import ttk, messagebox
import time
import json
from pathlib import Path

class MacroEditor:
    """
    Editor window for trimming macro recordings.
    Displays a timeline of events and allows setting start/end trim points.
    """
    def __init__(self, parent, recorder, on_save_callback):
        """
        Args:
            parent: Parent window
            recorder: MacroRecorder instance (stopped)
            on_save_callback: Function to call when saved (takes output_path)
        """
        self.recorder = recorder
        self.on_save_callback = on_save_callback
        self.events = recorder.events
        self.duration = recorder.duration()
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"Edit Macro: {recorder.name}")
        self.window.geometry("900x500")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.start_trim = 0.0
        self.end_trim = self.duration
        
        self._create_ui()
        self._draw_timeline()
        
    def _create_ui(self):
        # Main container
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        ttk.Label(main_frame, text="Trim your macro by adjusting the start and end points.").pack(pady=(0, 10))
        
        # Timeline Canvas
        self.canvas_height = 150
        self.canvas = tk.Canvas(main_frame, height=self.canvas_height, bg="white", highlightthickness=1, highlightbackground="#ccc")
        self.canvas.pack(fill=tk.X, expand=False, pady=10)
        self.canvas.bind("<Configure>", self._on_resize)
        
        # Sliders Frame
        sliders_frame = ttk.LabelFrame(main_frame, text="Trim Controls", padding="10")
        sliders_frame.pack(fill=tk.X, pady=10)
        
        # Start Slider
        ttk.Label(sliders_frame, text="Start Time:").grid(row=0, column=0, padx=5)
        self.start_var = tk.DoubleVar(value=0.0)
        self.start_slider = ttk.Scale(sliders_frame, from_=0.0, to=self.duration, variable=self.start_var, command=self._on_start_change)
        self.start_slider.grid(row=0, column=1, sticky="ew", padx=5)
        self.start_label = ttk.Label(sliders_frame, text="0.00s")
        self.start_label.grid(row=0, column=2, padx=5)
        
        # End Slider
        ttk.Label(sliders_frame, text="End Time:").grid(row=1, column=0, padx=5)
        self.end_var = tk.DoubleVar(value=self.duration)
        self.end_slider = ttk.Scale(sliders_frame, from_=0.0, to=self.duration, variable=self.end_var, command=self._on_end_change)
        self.end_slider.grid(row=1, column=1, sticky="ew", padx=5)
        self.end_label = ttk.Label(sliders_frame, text=f"{self.duration:.2f}s")
        self.end_label.grid(row=1, column=2, padx=5)
        
        sliders_frame.columnconfigure(1, weight=1)
        
        # Info
        self.info_label = ttk.Label(main_frame, text=f"Original Duration: {self.duration:.2f}s | New Duration: {self.duration:.2f}s")
        self.info_label.pack(pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Save Macro", command=self._save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Preview Trimmed", command=self._preview).pack(side=tk.LEFT, padx=5)

        # Metadata Frame (Name & Shortcut)
        meta_frame = ttk.LabelFrame(main_frame, text="Macro Details", padding="10")
        meta_frame.pack(fill=tk.X, pady=10, before=sliders_frame)
        
        # Name
        ttk.Label(meta_frame, text="Name:").grid(row=0, column=0, padx=5, sticky="w")
        self.name_var = tk.StringVar(value=self.recorder.name)
        self.name_entry = ttk.Entry(meta_frame, textvariable=self.name_var)
        self.name_entry.grid(row=0, column=1, padx=5, sticky="ew")
        
        # Shortcut
        ttk.Label(meta_frame, text="Shortcut:").grid(row=1, column=0, padx=5, sticky="w")
        self.shortcut_var = tk.StringVar()
        self.shortcut_entry = ttk.Entry(meta_frame, textvariable=self.shortcut_var, state="readonly")
        self.shortcut_entry.grid(row=1, column=1, padx=5, sticky="ew")
        
        self.capture_btn = ttk.Button(meta_frame, text="Capture Key", command=self._capture_shortcut)
        self.capture_btn.grid(row=1, column=2, padx=5)
        
        ttk.Button(meta_frame, text="Clear", command=lambda: self.shortcut_var.set("")).grid(row=1, column=3, padx=5)
        
        meta_frame.columnconfigure(1, weight=1)
        
    def _on_resize(self, event):
        self._draw_timeline()
        
    def _draw_timeline(self):
        self.canvas.delete("all")
        width = self.canvas.winfo_width()
        if width <= 1: return
        
        # Draw events
        # Scale factor: pixels per second
        if self.duration <= 0: return
        scale = width / self.duration
        
        # Draw background for trimmed areas
        start_x = self.start_trim * scale
        end_x = self.end_trim * scale
        
        # Trimmed out (left)
        self.canvas.create_rectangle(0, 0, start_x, self.canvas_height, fill="#ffebee", outline="")
        # Trimmed out (right)
        self.canvas.create_rectangle(end_x, 0, width, self.canvas_height, fill="#ffebee", outline="")
        # Active area
        self.canvas.create_rectangle(start_x, 0, end_x, self.canvas_height, fill="#e8f5e9", outline="")
        
        # Draw events
        for e in self.events:
            x = e.t * scale
            
            if e.type == 'mouse_move':
                # Small dots for moves
                self.canvas.create_oval(x-1, 50, x+1, 52, fill="gray", outline="")
            elif e.type == 'mouse_click':
                # Circles for clicks
                color = "blue" if e.data.get('pressed') else "lightblue"
                self.canvas.create_oval(x-3, 40, x+3, 60, fill=color, outline="black")
            elif e.type == 'key_press':
                # Lines for keys
                self.canvas.create_line(x, 70, x, 100, fill="red", width=2)
            elif e.type == 'mouse_scroll':
                # Triangles/Diamonds for scroll
                self.canvas.create_polygon(x, 110, x-3, 115, x+3, 115, fill="orange")

        # Draw trim lines
        self.canvas.create_line(start_x, 0, start_x, self.canvas_height, fill="red", width=2, dash=(4, 2))
        self.canvas.create_line(end_x, 0, end_x, self.canvas_height, fill="red", width=2, dash=(4, 2))
        
        # Labels on canvas
        self.canvas.create_text(10, 20, text="Mouse Clicks", anchor="w", fill="blue")
        self.canvas.create_text(10, 85, text="Keyboard", anchor="w", fill="red")
        
    def _on_start_change(self, value):
        val = float(value)
        if val >= self.end_trim:
            val = self.end_trim - 0.1
            if val < 0: val = 0
            self.start_var.set(val)
        
        self.start_trim = val
        self.start_label.config(text=f"{val:.2f}s")
        self._update_info()
        self._draw_timeline()
        
    def _on_end_change(self, value):
        val = float(value)
        if val <= self.start_trim:
            val = self.start_trim + 0.1
            if val > self.duration: val = self.duration
            self.end_var.set(val)
            
        self.end_trim = val
        self.end_label.config(text=f"{val:.2f}s")
        self._update_info()
        self._draw_timeline()
        
    def _update_info(self):
        new_dur = self.end_trim - self.start_trim
        self.info_label.config(text=f"Original Duration: {self.duration:.2f}s | New Duration: {new_dur:.2f}s")
        
    def _preview(self):
        """Play the trimmed portion."""
        trimmed_events = self.recorder.trim(self.start_trim, self.end_trim)
        if not trimmed_events:
            messagebox.showinfo("Preview", "No events in selected range.")
            return
            
        # Hide the window (can't iconify transient windows)
        self.window.withdraw()
        # Give time for window to hide
        self.window.update()
        time.sleep(0.3)
        
        try:
            # Replay
            from ..core.macro_recorder import MacroRecorder
            MacroRecorder.play_events(trimmed_events)
        except Exception as e:
            messagebox.showerror("Error", f"Playback failed: {e}")
        finally:
            # Restore the window
            self.window.deiconify()
            
    def _capture_shortcut(self):
        """Capture a single key press for shortcut."""
        self.capture_btn.config(text="Press any key...", state="disabled")
        self.window.focus_set()
        
        try:
            from pynput import keyboard
            
            def on_press(key):
                try:
                    # Use MacroRecorder's helper to get clean string
                    from ..core.macro_recorder import MacroRecorder
                    key_str = MacroRecorder._key_to_str(key)
                    
                    # Clean up key string (remove quotes if any)
                    key_str = key_str.replace("'", "")
                    
                    # Update UI in main thread
                    self.window.after(0, lambda: self._update_shortcut(key_str))
                    return False # Stop listener
                except Exception as e:
                    print(f"Error capturing key: {e}")
                    return False

            listener = keyboard.Listener(on_press=on_press)
            listener.start()
            
        except ImportError:
            messagebox.showerror("Error", "pynput not installed")
            self.capture_btn.config(text="Capture Key", state="normal")

    def _update_shortcut(self, key_str):
        self.shortcut_var.set(key_str)
        self.capture_btn.config(text="Capture Key", state="normal")

    def _save(self):
        """Save the trimmed macro."""
        try:
            # Get details
            new_name = self.name_var.get().strip()
            if not new_name:
                messagebox.showwarning("Invalid Name", "Please enter a macro name.")
                return
                
            shortcut = self.shortcut_var.get().strip()

            # Get trimmed events
            trimmed_events = self.recorder.trim(self.start_trim, self.end_trim)
            
            # Update filename based on new name
            safe_name = self.recorder._sanitize(new_name)
            output_path = self.recorder.save_dir / f"{safe_name}.json"
            
            # Calculate new duration
            new_duration = 0.0
            if trimmed_events:
                new_duration = trimmed_events[-1].t
            
            from dataclasses import asdict
            payload = {
                'name': new_name,
                'shortcut_key': shortcut,
                'created_at': time.time(),
                'duration': new_duration,
                'events': [asdict(e) for e in trimmed_events],
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2)
                
            if self.on_save_callback:
                self.on_save_callback(output_path)
                
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")
