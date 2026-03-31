from Lockscreen import Lockscreen
import numpy as np
import statistics
from Fullscreen import Fullscreen
import joblib
import sys
import os

MIN_KEYS = 5


def _resource_path(filename):
    """Works both in dev and when bundled by PyInstaller."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)


class Detector:
    def __init__(self):
        self.keys = []
        self.keysWithGaps = []
        self.Lockscreen = Lockscreen()
        self.Fullscreen = Fullscreen()
        self.blocked = False

        model_path = _resource_path("Data/model.pkl")
        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
            print("[Detector] ML model loaded")
        else:
            self.model = None
            print("[Detector] model.pkl not found — falling back to threshold (>=10 keys)")

    def analyse(self, keys, trigger_event=None):
        if self.blocked:
            return

        self.keys = keys
        self.keysWithGaps = []
        for i in range(1, len(self.keys)):
            gap = self.keys[i][1] - self.keys[i-1][1]
            self.keysWithGaps.append((self.keys[i-1][0], gap))

        if len(self.keys) >= MIN_KEYS:
            key_count, avg_gap, var = self.Format(self.keysWithGaps)
            is_malicious = self._predict(key_count, avg_gap, var)

            if is_malicious:
                self.blocked = True
                self.Lockscreen.block()
                if trigger_event is not None:
                    trigger_event.set()

    def _predict(self, key_count, avg_gap, var):
        if self.model is not None:
            prediction = self.model.predict([[key_count, avg_gap, var]])[0]
            return prediction == 1
        else:
            return len(self.keysWithGaps) >= 10

    def Format(self, keysWithGaps):
        if len(keysWithGaps) == 0:
            return 0, 0, 0
        gaps = [gap for _, gap in keysWithGaps]
        key_count = len(keysWithGaps)
        avg_gap = statistics.mean(gaps)
        var = np.var(gaps)
        return key_count, avg_gap, var
