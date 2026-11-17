"""Runtime configuration for the live detector.

Training and evaluation scripts keep their own constants at the top of each
file; everything the deployed app depends on lives here.
"""

import os
import sys

# seconds of typing the detector looks at
WINDOW_SECONDS = 3.0

# analysis rate; was 0.5 in v1, halving it halves time-to-block
TICK_SECONDS = 0.25

# windows that must score malicious back-to-back before input is blocked.
# a single noisy window can't lock the machine; a real payload stays inside
# the 3 s window long enough to confirm on the next tick.
CONFIRM_WINDOWS = 2

MODEL_FILE = "Data/model.pkl"
TRAY_ICON_FILE = "Data/mk-logo.png"


def resource_path(filename):
    """Resolve a bundled file both in dev and when frozen by PyInstaller."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)
