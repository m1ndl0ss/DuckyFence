import csv
import os
import sys


class DataCollector:
    """Appends per-window aggregate timing features to Data/output.csv.

    Only key_count, avg_gap and variance are stored; key identities and
    typed content are never written to disk.
    """

    def __init__(self):
        self.fieldnames = ["key_count", "avg_gap", "variance", "label"]

        # When frozen by PyInstaller, __file__ points to the temp extraction dir.
        # sys.executable always points to the actual exe / script location.
        if getattr(sys, "frozen", False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.abspath(__file__))

        self.filepath = os.path.join(base, "Data/output.csv")

        if not os.path.exists(self.filepath):
            with open(self.filepath, "a", newline="") as f:
                csv.DictWriter(f, fieldnames=self.fieldnames).writeheader()

    def save(self, key_count, avg_gap, variance, label=1):
        if key_count == 0:
            return
        with open(self.filepath, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writerow(
                {
                    "key_count": key_count,
                    "avg_gap": avg_gap,
                    "variance": variance,
                    "label": label,
                }
            )
