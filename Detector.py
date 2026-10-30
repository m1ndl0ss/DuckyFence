import sys
import os

import joblib

import features
from Lockscreen import Lockscreen
from Fullscreen import Fullscreen

# windows that must score malicious back-to-back before input is blocked.
# a single noisy window can't lock the machine anymore; a real payload
# stays inside the 3s window long enough to confirm on the next tick.
CONFIRM_WINDOWS = 2


def _resource_path(filename):
    """Works both in dev and when bundled by PyInstaller."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)


class Detector:
    def __init__(self):
        self.Lockscreen = Lockscreen()
        self.Fullscreen = Fullscreen()
        self.blocked = False
        self.hits = 0
        self.model = None
        self.threshold = 0.5
        self.min_gaps = features.MIN_GAPS

        model_path = _resource_path("Data/model.pkl")
        if os.path.exists(model_path):
            bundle = joblib.load(model_path)
            if isinstance(bundle, dict):
                self.model = bundle['model']
                self.threshold = bundle['threshold']
                self.min_gaps = bundle.get('min_gaps', self.min_gaps)
            else:
                self.model = bundle  # old flat v1 pickle
            # single-row predicts: the n_jobs=-1 thread pool costs ~50ms per call
            self.model.n_jobs = 1
            print(f"[Detector] model loaded, threshold {self.threshold:.3f}")
        else:
            print("[Detector] model.pkl not found — falling back to rate rule")

    def analyse(self, keys, trigger_event=None):
        if self.blocked:
            return

        gaps = [keys[i][1] - keys[i - 1][1] for i in range(1, len(keys))]
        if len(gaps) < self.min_gaps:
            self.hits = 0
            return

        if self._predict(gaps):
            self.hits += 1
        else:
            self.hits = 0

        if self.hits >= CONFIRM_WINDOWS:
            self.hits = 0
            self.blocked = True
            self.Lockscreen.block()
            if trigger_event is not None:
                trigger_event.set()

    def _predict(self, gaps):
        if self.model is None:
            return len(gaps) >= 10
        vec = features.from_gaps(gaps)
        return self.model.predict_proba([vec])[0][1] >= self.threshold
