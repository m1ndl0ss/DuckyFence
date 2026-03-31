from tkinter import Toplevel, Label, Frame

BG     = "#0d0d0d"
ACCENT = "#e53935"
DIM    = "#2a2a2a"


class Splash:
    _TEXT = "DUCKY FENCE"

    def __init__(self, root, on_done):
        self.root     = root
        self.on_done  = on_done
        self._idx     = 0
        self._cursor  = True

        win = Toplevel(root)
        self.win = win
        win.configure(bg=BG)
        win.overrideredirect(True)
        win.attributes("-topmost", True)

        W, H = 560, 260
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        win.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")

        # thin red top border
        Frame(win, bg=ACCENT, height=3).pack(fill="x")

        inner = Frame(win, bg=BG)
        inner.place(relx=0.5, rely=0.45, anchor="center")

        self.title_lbl = Label(
            inner, text="", font=("Courier New", 42, "bold"),
            fg=ACCENT, bg=BG
        )
        self.title_lbl.pack()

        self.status_lbl = Label(
            inner, text="", font=("Segoe UI", 10),
            fg="#444444", bg=BG
        )
        self.status_lbl.pack(pady=(18, 0))

        # thin red bottom border
        Frame(win, bg=DIM, height=1).pack(side="bottom", fill="x")

        self._type_next()

    def _type_next(self):
        if self._idx <= len(self._TEXT):
            cursor = "█" if self._cursor else " "
            self._cursor = not self._cursor
            self.title_lbl.config(text=self._TEXT[:self._idx] + cursor)
            self._idx += 1
            self.win.after(75, self._type_next)
        else:
            self.title_lbl.config(text=self._TEXT)
            self.status_lbl.config(text="●  PROTECTION ACTIVE", fg="#3a7a3a")
            self.win.after(1400, self._finish)

    def _finish(self):
        self.win.destroy()
        self.on_done()
