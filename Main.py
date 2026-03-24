from pynput import keyboard
import threading
from Detector import Detector
from Listener import Listener
import time

keys = []
running = True

def addKey(key):
    keys.append((key, time.time()))

def onRelease(key):
    global running
    if key == keyboard.Key.esc:
        running = False

def analyse_loop():
    while running:
        time.sleep(3)
        detector.analyse(keys.copy())
        keys.clear()

detector = Detector()
listener = Listener(on_press=addKey, on_release=onRelease)
listener.listen()

t = threading.Thread(target=analyse_loop, daemon=True)
t.start()

while running:
    time.sleep(0.1)

listener.stop()
print("stopped")