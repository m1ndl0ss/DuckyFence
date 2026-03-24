from Lockscreen import Lockscreen
import numpy as np
import statistics
from DataCollector import DataCollector

class Detector:
    def __init__(self):
        self.keys = []
        self.keysWithGaps =[]
        self.Lockscreen = Lockscreen()
        self.DataCollector = DataCollector()
        self.blocked = False

    def analyse(self, keys):
        if self.blocked:
            return

        self.keys = keys
        self.keysWithGaps = []
        for i in range (1, len(self.keys)):
            gap= self.keys[i][1] - self.keys[i-1][1]
            self.keysWithGaps.append((self.keys[i-1][0], gap))
        print("Analysing", len(self.keysWithGaps), "keys:", self.keysWithGaps)
        if len(self.keysWithGaps)>=10:
            self.blocked=True
            self.Lockscreen.block()
        #output to csv
        key_count, avg_gap, var = self.Format(self.keysWithGaps)
        self.DataCollector.save(key_count, avg_gap, var)
    def Format(self,keysWithGaps):
        gaps = []
        for key, gap in self.keysWithGaps:
            gaps.append(gap)
        if len(keysWithGaps) == 0:
            return 0, 0, 0
        key_count = len(keysWithGaps)
        avg_gap = statistics.mean(gaps)
        var = np.var(gaps)
        return key_count, avg_gap, var