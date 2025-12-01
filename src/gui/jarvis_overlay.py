import tkinter as tk
from tkinter import ttk
import queue

class JarvisOverlay:
    def __init__(self, master=None, on_interrupt=None):
        if master:
            self.root = tk.Toplevel(master)
        else:
            self.root = tk.Tk()
            
        self.root.title("JARVIS Overlay")
        self.root.geometry("400x150+50+50") # Top left
        self.root.overrideredirect(True) # No borders
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.85) # Slight transparency
        self.root.configure(bg='#000000')

        self.on_interrupt = on_interrupt
        self.queue = queue.Queue()

        # Status Label
        self.status_var = tk.StringVar(value="Initializing...")
        self.status_label = tk.Label(
            self.root, 
            textvariable=self.status_var, 
            font=("Segoe UI", 12, "bold"), 
            fg="#00FFFF", 
            bg="#000000"
        )
        self.status_label.pack(pady=(15, 5), fill='x')

        # Content/Text Label
        self.text_var = tk.StringVar(value="Waiting for command...")
        self.text_label = tk.Label(
            self.root, 
            textvariable=self.text_var, 
            font=("Segoe UI", 10), 
            fg="#FFFFFF", 
            bg="#000000",
            wraplength=380
        )
        self.text_label.pack(pady=5, fill='x', padx=10)

        # Buttons Frame
        self.btn_frame = tk.Frame(self.root, bg="#000000")
        self.btn_frame.pack(side='bottom', pady=15, fill='x')

        # Interrupt Button
        self.interrupt_btn = tk.Button(
            self.btn_frame, 
            text="🛑 STOP / NEW COMMAND", 
            command=self.handle_interrupt,
            bg="#330000",
            fg="#FF4444",
            activebackground="#550000",
            activeforeground="#FF4444",
            relief='flat',
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=5
        )
        self.interrupt_btn.pack(side='top')
        
        # Dragging functionality
        self.root.bind('<Button-1>', self.start_move)
        self.root.bind('<B1-Motion>', self.do_move)

        self.check_queue()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def handle_interrupt(self):
        if self.on_interrupt:
            self.on_interrupt()

    def update_status(self, text, color="#00FFFF"):
        self.queue.put(("status", text, color))

    def update_text(self, text):
        self.queue.put(("text", text))

    def check_queue(self):
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg[0] == "status":
                    self.status_var.set(msg[1])
                    self.status_label.config(fg=msg[2])
                elif msg[0] == "text":
                    self.text_var.set(msg[1])
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)

    def run(self):
        self.root.mainloop()
        
    def close(self):
        self.root.destroy()
