from Lockscreen import Lockscreen
class Detector:
    def __init__(self):
        self.keys = []
        self.Lockscreen = Lockscreen()

    def analyse(self, keys):
        self.keys = keys
        print("Analysing", len(keys), "keys:", self.keys)
        if len(self.keys)>=10:
            self.Lockscreen.block()
