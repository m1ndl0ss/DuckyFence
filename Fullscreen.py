from tkinter import *
import random
import string


class Fullscreen:
    def __init__(self):
        self.quit_string = ''.join(random.choices(string.ascii_uppercase, k=6))

    def trigger(self):
        self.tk = Tk()
        self.tk.attributes("-fullscreen", True)
        Label(self.tk, text="MALICIOUS TYPING PATTERN DETECTED").pack()
        Label(self.tk, text=f"Type this to unlock: {self.quit_string}").pack()

        self.entry = Entry(self.tk)
        self.entry.pack()
        self.entry.bind("<Return>", self.check_input)

        self.tk.mainloop()

    def check_input(self, event):
        if self.entry.get() == self.quit_string:
            self.tk.destroy()