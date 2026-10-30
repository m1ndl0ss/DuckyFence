import os
import json

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import roc_curve, roc_auc_score, confusion_matrix

from features import FEATURE_NAMES, MIN_GAPS, from_aggregates

BASE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(BASE, "Data/dataset_v2.csv")
OUT = os.path.join(BASE, "Data/model.pkl")

# operating point: hold false positives on human windows at or under 0.1%,
# then take whatever recall that buys. v1 just used predict() at 0.5.
TARGET_FPR = 0.001
SEED = 42


def build_matrix(df):
    rows = [from_aggregates(kc, ag, var)
            for kc, ag, var in zip(df['key_count'], df['avg_gap'], df['variance'])]
    return np.array(rows)


def make_model():
    return RandomForestClassifier(
        n_estimators=300,
        class_weight='balanced',
        random_state=SEED,
        n_jobs=-1,
    )


def pick_threshold(y_true, probs, target_fpr=TARGET_FPR):
    """Highest-recall threshold that keeps FPR at or under target."""
    fpr, tpr, thr = roc_curve(y_true, probs)
    ok = np.where(fpr <= target_fpr)[0]
    best = ok[np.argmax(tpr[ok])]
    t = thr[best]
    # roc_curve pads the first threshold with inf
    return float(min(t, 1.0))


def grouped_oof(X, y, groups, factory=make_model, n_splits=5):
    """Out-of-fold probabilities with whole subjects held out per fold,
    so a typist (or attack profile) never appears in both train and test."""
    oof = np.zeros(len(y))
    skf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=SEED)
    for tr, te in skf.split(X, y, groups):
        m = factory()
        m.fit(X[tr], y[tr])
        oof[te] = m.predict_proba(X[te])[:, 1]
    return oof


if __name__ == "__main__":
    df = pd.read_csv(CSV)
    print(f"{len(df)} windows")
    print(df.groupby(['label', 'source']).size().to_string(), "\n")

    X = build_matrix(df)
    y = df['label'].values
    groups = df['subject'].values

    oof = grouped_oof(X, y, groups)
    threshold = pick_threshold(y, oof)
    pred = (oof >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(y, pred).ravel()
    print(f"Threshold @ FPR<={TARGET_FPR:.1%}: {threshold:.3f}")
    print(f"OOF ROC AUC: {roc_auc_score(y, oof):.4f}")
    print(f"OOF TPR: {tp / (tp + fn):.4f}   OOF FPR: {fp / (fp + tn):.4f}")
    print("Confusion matrix (rows: human, injection):")
    print(f"  {tn:>5}  {fp:>5}")
    print(f"  {fn:>5}  {tp:>5}\n")

    model = make_model()
    model.fit(X, y)

    print("Feature importances:")
    for name, imp in sorted(zip(FEATURE_NAMES, model.feature_importances_), key=lambda x: -x[1]):
        print(f"  {name}: {imp:.3f}")

    bundle = {
        'model': model,
        'threshold': threshold,
        'features': FEATURE_NAMES,
        'min_gaps': MIN_GAPS,
        'target_fpr': TARGET_FPR,
        'version': 2,
    }
    joblib.dump(bundle, OUT)
    print(f"\nModel bundle saved to {OUT}")

    meta = {k: bundle[k] for k in ('threshold', 'features', 'min_gaps', 'target_fpr', 'version')}
    with open(os.path.join(BASE, "Data/model_meta.json"), 'w') as f:
        json.dump(meta, f, indent=2)
