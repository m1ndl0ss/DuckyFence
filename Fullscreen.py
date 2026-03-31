from tkinter import Toplevel, Frame, Label, Entry, FLAT, X, END
import random
import string

BG           = "#0d0d0d"
PANEL_BG     = "#141414"
ACCENT       = "#e53935"
ACCENT_DIM   = "#7f1c1c"
TEXT_PRIMARY  = "#f5f5f5"
TEXT_SECONDARY = "#9e9e9e"
ENTRY_BG     = "#1e1e1e"
ENTRY_FG     = "#f5f5f5"
BORDER       = "#2a2a2a"


class Fullscreen:
    def __init__(self):
        self.quit_string = ''.join(random.choices(string.ascii_uppercase, k=6))

    def trigger(self, master):
        self.quit_string = ''.join(random.choices(string.ascii_uppercase, k=6))
        self.tk = Toplevel(master)
        self.tk.configure(bg=BG)
        self.tk.attributes("-fullscreen", True)
        self.tk.attributes("-topmost", True)
        self.tk.protocol("WM_DELETE_WINDOW", lambda: None)
        self.tk.resizable(False, False)

        self.tk.bind("<Alt-Tab>",  lambda e: "break")
        self.tk.bind("<Alt-F4>",   lambda e: "break")
        self.tk.bind("<Super_L>",  lambda e: "break")
        self.tk.bind("<Super_R>",  lambda e: "break")
        self.tk.bind("<Escape>",   lambda e: "break")
        self.tk.grab_set()
        self.tk.focus_force()

        self._build_ui()
        self._keep_focus()
        master.wait_window(self.tk)  # blocks here (nested event loop) until dismissed

    def _build_ui(self):
        outer = Frame(self.tk, bg=BG)
        outer.place(relx=0.5, rely=0.5, anchor="center")

        card = Frame(outer, bg=PANEL_BG, padx=60, pady=50,
                     highlightbackground=ACCENT_DIM, highlightthickness=1)
        card.pack()

        Frame(card, bg=ACCENT, height=4).pack(fill=X, pady=(0, 30))

        Label(card, text="⚠", font=("Segoe UI", 52), fg=ACCENT, bg=PANEL_BG).pack()

        Label(card, text="THREAT DETECTED",
              font=("Segoe UI", 28, "bold"),
              fg=TEXT_PRIMARY, bg=PANEL_BG).pack(pady=(12, 4))

        Label(card, text="Automated keystroke injection detected on this system.",
              font=("Segoe UI", 11),
              fg=TEXT_SECONDARY, bg=PANEL_BG).pack()

        Frame(card, bg=BORDER, height=1).pack(fill=X, pady=28)

        Label(card, text="UNLOCK CODE",
              font=("Segoe UI", 9, "bold"),
              fg=TEXT_SECONDARY, bg=PANEL_BG).pack()

        code_frame = Frame(card, bg=ENTRY_BG,
                           highlightbackground=ACCENT_DIM, highlightthickness=1,
                           padx=32, pady=14)
        code_frame.pack(pady=(8, 24))

        Label(code_frame, text=self.quit_string,
              font=("Courier New", 36, "bold"),
              fg=ACCENT, bg=ENTRY_BG).pack()

        Label(card, text="Type the code above and press Enter to unlock",
              font=("Segoe UI", 10),
              fg=TEXT_SECONDARY, bg=PANEL_BG).pack(pady=(0, 12))

        entry_frame = Frame(card, bg=ENTRY_BG,
                            highlightbackground=BORDER, highlightthickness=1)
        entry_frame.pack(fill=X, pady=(0, 4))

        self.entry = Entry(entry_frame,
                           font=("Courier New", 20, "bold"),
                           bg=ENTRY_BG, fg=ENTRY_FG,
                           insertbackground=ACCENT,
                           relief=FLAT, bd=0,
                           justify="center",
                           width=20)
        self.entry.pack(ipady=10, ipadx=10, fill=X)
        self.entry.bind("<Return>", self.check_input)
        self.entry.bind("<Key>", self._on_key)
        self.entry.focus_set()

        self.error_label = Label(card, text="",
                                  font=("Segoe UI", 10),
                                  fg=ACCENT, bg=PANEL_BG)
        self.error_label.pack(pady=(6, 0))

        Label(card, text="DuckyFence  •  Unauthorized device blocked",
              font=("Segoe UI", 8),
              fg="#444444", bg=PANEL_BG).pack(pady=(28, 0))

    def _on_key(self, event):
        self.error_label.config(text="")
        self.entry.master.config(highlightbackground=ACCENT, highlightthickness=1)

    def _keep_focus(self):
        try:
            self.tk.attributes("-topmost", True)
            self.tk.focus_force()
            self.entry.focus_set()
            self.tk.after(500, self._keep_focus)
        except Exception:
            pass

    def check_input(self, event):
        if self.entry.get() == self.quit_string:
            self.tk.grab_release()
            self.tk.destroy()  # wait_window in trigger() returns here
        else:
            self.entry.delete(0, END)
            self.error_label.config(text="Incorrect code. Try again.")
            self.entry.master.config(highlightbackground=ACCENT, highlightthickness=1)
