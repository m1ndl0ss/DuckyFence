import numpy as np
import pytest

import config
from Detector import Detector


class StubLockscreen:
    def __init__(self):
        self.block_calls = 0

    def block(self):
        self.block_calls += 1

    def unblock(self):
        pass


class StubModel:
    """predict_proba returns a fixed malicious probability."""

    def __init__(self, prob):
        self.prob = prob

    def predict_proba(self, X):
        return [[1 - self.prob, self.prob]]


def window(gaps, start=1000.0):
    """Build a (key, timestamp) window from a list of inter-key gaps."""
    t = start
    keys = [(None, t)]
    for g in gaps:
        t += g
        keys.append((None, t))
    return keys


MALICIOUS = window([0.005] * 10)
HUMAN = window([0.2, 0.15, 0.4, 0.1, 0.3, 0.25])
TOO_SHORT = window([0.005] * 3)


@pytest.fixture
def detector():
    d = Detector()
    d.Lockscreen = StubLockscreen()
    d.threshold = 0.5
    return d


def set_verdict(detector, malicious):
    detector.model = StubModel(0.9 if malicious else 0.1)


def test_single_malicious_window_does_not_block(detector):
    set_verdict(detector, malicious=True)
    detector.analyse(MALICIOUS)
    assert not detector.blocked
    assert detector.Lockscreen.block_calls == 0


def test_consecutive_malicious_windows_block(detector):
    set_verdict(detector, malicious=True)
    for _ in range(config.CONFIRM_WINDOWS):
        detector.analyse(MALICIOUS)
    assert detector.blocked
    assert detector.Lockscreen.block_calls == 1


def test_benign_window_resets_confirmation(detector):
    set_verdict(detector, malicious=True)
    detector.analyse(MALICIOUS)
    set_verdict(detector, malicious=False)
    detector.analyse(HUMAN)
    set_verdict(detector, malicious=True)
    detector.analyse(MALICIOUS)
    assert not detector.blocked


def test_short_window_is_not_scored_and_resets(detector):
    set_verdict(detector, malicious=True)
    detector.analyse(MALICIOUS)
    detector.analyse(TOO_SHORT)  # fewer than min_gaps gaps
    detector.analyse(MALICIOUS)
    assert not detector.blocked


def test_no_further_analysis_while_blocked(detector):
    set_verdict(detector, malicious=True)
    for _ in range(config.CONFIRM_WINDOWS):
        detector.analyse(MALICIOUS)
    calls_after_block = detector.Lockscreen.block_calls
    detector.analyse(MALICIOUS)
    assert detector.Lockscreen.block_calls == calls_after_block


def test_shipped_model_separates_injection_from_typing():
    """The bundle in Data/model.pkl must flag a fast burst and pass human pacing."""
    d = Detector()
    assert d.model is not None, "Data/model.pkl missing"
    rng = np.random.default_rng(0)
    injected = (0.005 + np.abs(rng.normal(0, 0.0005, 40))).tolist()
    human = (0.15 + np.abs(rng.normal(0, 0.08, 20))).tolist()
    assert d._predict(injected)
    assert not d._predict(human)
