from Lockscreen import Lockscreen
class Detector:
    def __init__(self):
        self.keys = []
        self.keysWithGaps =[]
        self.Lockscreen = Lockscreen()

    def analyse(self, keys):
        self.keys = keys
        self.keysWithGaps = []
        for i in range (1, len(self.keys)):
            gap= self.keys[i][1] - self.keys[i-1][1]
            self.keysWithGaps.append((self.keys[i-1][0], gap))


        print("Analysing", len(self.keysWithGaps), "keys:", self.keysWithGaps)
        if len(self.keysWithGaps)>=10:
            self.Lockscreen.block()

