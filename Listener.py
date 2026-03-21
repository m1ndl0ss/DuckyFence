from pynput import keyboard

class Listener:
    def __init__(self, on_press):
        self.on_press = on_press
        self.listener = None
    def listen(self):
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
    def stop(self):
        self.listener.stop()


