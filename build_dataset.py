"""
Builds Data/dataset_v2.csv, the training corpus for the v2 model.

Human windows come from two places:
  - the CMU keystroke dynamics benchmark (Killourhy & Maxion, DSN 2009):
    51 subjects x 400 repetitions of a fixed password, keydown-keydown
    latencies. Practiced password typing is about as fast and rhythmic as
    humans get, which makes it a hard negative set.
    https://www.cs.cmu.edu/~keystroke/
  - my own free-typing windows collected for v1 (Data/training_data.csv)

Attack windows:
  - real injection runs captured with DataCollector in v1
  - simulated HID injection profiles: fixed per-keystroke delay (1-75 ms,
    the range a Rubber Ducky's STRING/DELAY settings actually produce)
    plus scheduling jitter and occasional USB frame hiccups. Simulated
    rows are tagged in the 'source' column so they can be excluded.
"""
import os
import urllib.request

import numpy as np
import pandas as pd

from features import MIN_GAPS

BASE = os.path.dirname(os.path.abspath(__file__))
CMU_CSV = os.path.join(BASE, "Data/DSL-StrongPasswordData.csv")
CMU_URL = "https://www.cs.cmu.edu/~keystroke/DSL-StrongPasswordData.csv"
V1_CSV = os.path.join(BASE, "Data/training_data.csv")
OUT = os.path.join(BASE, "Data/dataset_v2.csv")

SEED = 42

# per-keystroke delays (seconds) a scripted payload realistically runs at
PROFILE_DELAYS = [0.001, 0.002, 0.005, 0.010, 0.020, 0.035, 0.050, 0.075]
WINDOWS_PER_PROFILE = 250


def cmu_rows():
    if not os.path.exists(CMU_CSV):
        print(f"Downloading CMU benchmark to {CMU_CSV} ...")
        urllib.request.urlretrieve(CMU_URL, CMU_CSV)
    df = pd.read_csv(CMU_CSV)
    dd_cols = [c for c in df.columns if c.startswith('DD.')]
    gaps = df[dd_cols].values
    return pd.DataFrame({
        'key_count': gaps.shape[1],
        'avg_gap': gaps.mean(axis=1),
        'variance': gaps.var(axis=1),
        'label': 0,
        'source': 'cmu',
        'subject': df['subject'],
    })


def v1_rows():
    df = pd.read_csv(V1_CSV)
    df = df[df['key_count'] >= MIN_GAPS].reset_index(drop=True)
    df['source'] = np.where(df['label'] == 1, 'collected_attack', 'collected_human')
    df['subject'] = np.where(df['label'] == 1, 'attack_real', 'local')
    return df[['key_count', 'avg_gap', 'variance', 'label', 'source', 'subject']]


def simulated_rows():
    rng = np.random.default_rng(SEED)
    rows = []
    for delay in PROFILE_DELAYS:
        for _ in range(WINDOWS_PER_PROFILE):
            n = rng.integers(MIN_GAPS, 81)
            gaps = delay + np.abs(rng.normal(0, delay * 0.05 + 0.0002, n))
            # USB polling / scheduler hiccups: a few gaps land a frame late
            hiccups = rng.random(n) < 0.03
            gaps[hiccups] += rng.uniform(0.001, 0.008, hiccups.sum())
            rows.append({
                'key_count': n,
                'avg_gap': gaps.mean(),
                'variance': gaps.var(),
                'label': 1,
                'source': 'simulated_attack',
                'subject': f'attack_sim_{int(delay * 1000)}ms',
            })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    out = pd.concat([cmu_rows(), v1_rows(), simulated_rows()], ignore_index=True)
    out.to_csv(OUT, index=False)
    print(f"{len(out)} windows -> {OUT}")
    print(out.groupby(['label', 'source']).size().to_string())
