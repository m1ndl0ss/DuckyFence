from pynput import keyboard

class Listener:
    def __init__(self, on_press, on_release):
        self.on_press = on_press
        self.on_release = on_release
        self.listener = None

    def listen(self):
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

    def stop(self):
        self.listener.stop()