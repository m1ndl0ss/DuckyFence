import sys
import os
import ctypes

# ── single-instance guard ──────────────────────────────────────
_mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Global\\DuckyFenceMutex")
if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
    from tkinter import Tk
    import tkinter.messagebox as _mb
    _r = Tk(); _r.withdraw()
    _mb.showwarning("DuckyFence", "DuckyFence is already running in the system tray.")
    _r.destroy()
    sys.exit(0)

from tkinter import Tk
from pynput import keyboard
import threading
import time
import pystray
from PIL import Image
from Detector import Detector
from Listener import Listener
from Splash import Splash


def _resource_path(filename):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)


# ── shared state ──────────────────────────────────────────────
keys          = []
running       = True
trigger_event = threading.Event()
root          = Tk()
root.withdraw()  # hidden — all UI is Toplevel or tray


# ── keyboard callbacks ────────────────────────────────────────
def add_key(key):
    keys.append((key, time.time()))

def on_release(key):
    global running
    if key == keyboard.Key.ctrl_r:
        running = False
        root.after(0, root.quit)


# ── analysis loop (background thread) ────────────────────────
def analyse_loop():
    while running:
        time.sleep(0.5)
        now = time.time()
        window = [k for k in keys if now - k[1] <= 3.0]
        keys[:] = window
        detector.analyse(window, trigger_event)


# ── main-thread trigger poll ──────────────────────────────────
def check_trigger():
    if trigger_event.is_set():
        trigger_event.clear()
        detector.Lockscreen.unblock()       # unblock first so user can type in captcha
        detector.Fullscreen.trigger(root)   # blocks via wait_window until dismissed
        detector.blocked = False            # reset so detector can fire again next time
    if running:
        root.after(100, check_trigger)


# ── tray icon ─────────────────────────────────────────────────
def _make_tray_image():
    return Image.open(_resource_path("Data/mk-logo.png")).convert("RGBA").resize((64, 64), Image.LANCZOS)

def _on_tray_exit(icon, item):
    global running
    running = False
    icon.stop()
    root.after(0, root.quit)

tray = pystray.Icon(
    "DuckyFence",
    _make_tray_image(),
    "DuckyFence — Active",
    pystray.Menu(pystray.MenuItem("Exit", _on_tray_exit))
)


# ── startup sequence ──────────────────────────────────────────
def _after_splash():
    threading.Thread(target=analyse_loop, daemon=True).start()
    check_trigger()

detector = Detector()
listener = Listener(on_press=add_key, on_release=on_release)
listener.listen()

threading.Thread(target=tray.run, daemon=True).start()

root.after(0, lambda: Splash(root, _after_splash))
root.mainloop()

listener.stop()
tray.stop()
