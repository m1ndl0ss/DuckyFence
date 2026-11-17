"""Tray app entry point: keyboard listener, 4 Hz analysis loop, lockscreen trigger."""

import ctypes
import sys

# ── single-instance guard ──────────────────────────────────────
_mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Global\\DuckyFenceMutex")
if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
    import tkinter.messagebox as _mb
    from tkinter import Tk

    _r = Tk()
    _r.withdraw()
    _mb.showwarning("DuckyFence", "DuckyFence is already running in the system tray.")
    _r.destroy()
    sys.exit(0)

import threading
import time
from tkinter import Tk

import pystray
from PIL import Image
from pynput import keyboard

import config
from Detector import Detector
from Listener import Listener
from Splash import Splash

# ── shared state ──────────────────────────────────────────────
keys = []
keys_lock = threading.Lock()  # listener thread appends, analysis thread prunes
running = True
trigger_event = threading.Event()
root = Tk()
root.withdraw()  # hidden — all UI is Toplevel or tray


# ── keyboard callbacks ────────────────────────────────────────
def add_key(key):
    with keys_lock:
        keys.append((key, time.time()))


def on_release(key):
    global running
    if key == keyboard.Key.ctrl_r:
        running = False
        root.after(0, root.quit)


# ── analysis loop (background thread) ────────────────────────
def analyse_loop():
    while running:
        time.sleep(config.TICK_SECONDS)
        now = time.time()
        with keys_lock:
            keys[:] = [k for k in keys if now - k[1] <= config.WINDOW_SECONDS]
            window = list(keys)
        detector.analyse(window, trigger_event)


# ── main-thread trigger poll ──────────────────────────────────
def check_trigger():
    if trigger_event.is_set():
        trigger_event.clear()
        detector.Lockscreen.unblock()  # unblock first so user can type in captcha
        detector.Fullscreen.trigger(root)  # blocks via wait_window until dismissed
        detector.blocked = False  # reset so detector can fire again next time
    if running:
        root.after(100, check_trigger)


# ── tray icon ─────────────────────────────────────────────────
def _make_tray_image():
    icon = Image.open(config.resource_path(config.TRAY_ICON_FILE))
    return icon.convert("RGBA").resize((64, 64), Image.LANCZOS)


def _on_tray_exit(icon, item):
    global running
    running = False
    icon.stop()
    root.after(0, root.quit)


tray = pystray.Icon(
    "DuckyFence",
    _make_tray_image(),
    "DuckyFence — Active",
    pystray.Menu(pystray.MenuItem("Exit", _on_tray_exit)),
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
