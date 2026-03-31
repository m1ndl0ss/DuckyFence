from tkinter import Tk
from pynput import keyboard
import threading
import time
import pystray
from PIL import Image, ImageDraw
from Detector import Detector
from Listener import Listener
from Splash import Splash

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
        detector.Fullscreen.trigger(root)   # blocks via wait_window until dismissed
        detector.Lockscreen.unblock()       # restore input after user unlocks
    if running:
        root.after(100, check_trigger)


# ── tray icon ─────────────────────────────────────────────────
def _make_tray_image():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    # shield shape
    shield = [(32, 2), (60, 13), (60, 35), (32, 62), (4, 35), (4, 13)]
    d.polygon(shield, fill="#e53935")
    # inner cutout
    inner = [(32, 12), (50, 20), (50, 36), (32, 52), (14, 36), (14, 20)]
    d.polygon(inner, fill="#7f1c1c")
    return img

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
