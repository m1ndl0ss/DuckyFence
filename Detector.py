import os

import joblib

import config
import features
from Fullscreen import Fullscreen
from Lockscreen import Lockscreen


class Detector:
    """Scores sliding windows of keystrokes and blocks input on confirmation.

    A window only counts once it has at least `min_gaps` inter-key gaps, and
    `config.CONFIRM_WINDOWS` consecutive malicious windows are required before
    input is blocked, so a single noisy window can't lock the machine.
    """

    def __init__(self):
        self.Lockscreen = Lockscreen()
        self.Fullscreen = Fullscreen()
        self.blocked = False
        self.hits = 0
        self.model = None
        self.threshold = 0.5
        self.min_gaps = features.MIN_GAPS

        model_path = config.resource_path(config.MODEL_FILE)
        if os.path.exists(model_path):
            bundle = joblib.load(model_path)
            if isinstance(bundle, dict):
                self.model = bundle["model"]
                self.threshold = bundle["threshold"]
                self.min_gaps = bundle.get("min_gaps", self.min_gaps)
            else:
                self.model = bundle  # old flat v1 pickle
            # single-row predicts: the n_jobs=-1 thread pool costs ~50ms per call
            self.model.n_jobs = 1
            print(f"[Detector] model loaded, threshold {self.threshold:.3f}")
        else:
            print("[Detector] model.pkl not found — falling back to rate rule")

    def analyse(self, keys, trigger_event=None):
        """Score one window of (key, timestamp) tuples; block on confirmation."""
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

        if self.hits >= config.CONFIRM_WINDOWS:
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
