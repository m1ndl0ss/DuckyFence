import numpy as np

# single place that defines what the model sees, so training and the live
# detector can never drift apart again (v1 had this logic duplicated)
FEATURE_NAMES = ['key_count', 'avg_gap', 'variance', 'cv', 'span']

# minimum number of inter-key gaps before a window is worth scoring
MIN_GAPS = 5


def from_gaps(gaps):
    """Feature vector from a list of inter-key gaps (seconds)."""
    if len(gaps) == 0:
        return [0, 0.0, 0.0, 0.0, 0.0]
    key_count = len(gaps)
    avg_gap = float(np.mean(gaps))
    variance = float(np.var(gaps))
    return from_aggregates(key_count, avg_gap, variance)


def from_aggregates(key_count, avg_gap, variance):
    # cv: how consistent the rhythm is relative to its own speed.
    # fast-but-human typing keeps a high cv, injected input sits near zero.
    cv = (variance ** 0.5) / avg_gap if avg_gap > 0 else 0.0
    # span: how long the burst actually took. a payload dumps dozens of
    # keys in a fraction of a second, a human spreads them over the window.
    span = avg_gap * key_count
    return [key_count, avg_gap, variance, cv, span]
