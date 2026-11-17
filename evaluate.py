"""
Benchmarks the original detector (v1, March) against the current one (v2)
so the numbers in the README are reproducible. Three questions:

  1. what did v1 look like on its own data, the way I measured it in March?
  2. how does that same v1 model hold up on 51 typists it has never seen?
  3. what does v2 achieve under a subject-held-out protocol?

Writes figures + metrics to results/. Run build_dataset.py first.
"""

import json
import os
import time

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, roc_auc_score, roc_curve
from sklearn.model_selection import (
    StratifiedGroupKFold,
    StratifiedKFold,
    cross_val_predict,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from train_model import (
    SEED,
    TARGET_FPR,
    build_matrix,
    grouped_oof,
    make_model,
    pick_threshold,
)

BASE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(BASE, "results")
os.makedirs(RESULTS, exist_ok=True)

V1_FEATURES = ["key_count", "avg_gap", "variance"]

BLUE = "#1f77b4"
ORANGE = "#ff7f0e"


def make_v1_model():
    # exactly what train_model.py built in March
    return RandomForestClassifier(
        n_estimators=200, class_weight="balanced", random_state=SEED, n_jobs=-1
    )


def metrics_from(y, pred, prob=None):
    tn, fp, fn, tp = confusion_matrix(y, pred).ravel()
    out = {
        "tpr": tp / (tp + fn),
        "fpr": fp / (fp + tn),
        "precision": tp / (tp + fp) if (tp + fp) else 0.0,
        "f1": 2 * tp / (2 * tp + fp + fn),
        "confusion": [[int(tn), int(fp)], [int(fn), int(tp)]],
    }
    if prob is not None:
        out["auc"] = roc_auc_score(y, prob)
    return out


def eval_v1_own_data(own):
    """The March protocol: my own data, plain 5-fold CV, default 0.5 threshold.
    Overlapping sliding windows end up in both train and test folds, so these
    numbers are optimistic -- that is the point of keeping them here."""
    X = own[V1_FEATURES].values
    y = own["label"].values
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    prob = cross_val_predict(make_v1_model(), X, y, cv=skf, method="predict_proba")[
        :, 1
    ]
    return metrics_from(y, (prob > 0.5).astype(int), prob)


def eval_v1_cross_dataset(own, rest):
    """Reality check: train v1 on everything I had in March, test on the CMU
    typists and the simulated payload profiles it has never seen."""
    m = make_v1_model()
    m.fit(own[V1_FEATURES].values, own["label"].values)
    y = rest["label"].values
    prob = m.predict_proba(rest[V1_FEATURES].values)[:, 1]
    return metrics_from(y, (prob > 0.5).astype(int), prob)


def eval_v2(X, y, groups):
    """Subject-held-out CV; the decision threshold is tuned inside each
    training fold (never on the test fold)."""
    prob = np.zeros(len(y))
    pred = np.zeros(len(y), dtype=int)
    outer = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    for tr, te in outer.split(X, y, groups):
        inner = grouped_oof(X[tr], y[tr], groups[tr], n_splits=3)
        t = pick_threshold(y[tr], inner)
        m = make_model()
        m.fit(X[tr], y[tr])
        p = m.predict_proba(X[te])[:, 1]
        prob[te] = p
        pred[te] = (p >= t).astype(int)
    return metrics_from(y, pred, prob), prob


def deployment_groups(y, groups):
    """Humans stay grouped by typist (a new user is always unseen), but
    attack windows are spread across folds: the deployed model trains on
    the full 1-75ms delay range, so attack speeds are not unseen at test
    time. The all-grouped variant answers the unseen-speed question."""
    return np.array(
        [
            g if label == 0 else f"atk_{i % 5}"
            for i, (label, g) in enumerate(zip(y, groups))
        ]
    )


def tpr_at(y, prob, target_fpr):
    fpr, tpr, _ = roc_curve(y, prob)
    return float(tpr[fpr <= target_fpr].max())


def model_comparison(X, y, groups):
    # sanity check that random forest is still the right pick for v2
    candidates = {
        "random_forest": make_model,
        "gradient_boosting": lambda: GradientBoostingClassifier(random_state=SEED),
        "logistic_regression": lambda: make_pipeline(
            StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=1000)
        ),
    }
    out = {}
    for name, factory in candidates.items():
        prob = grouped_oof(X, y, groups, factory=factory)
        out[name] = {
            "auc": roc_auc_score(y, prob),
            "tpr_at_target_fpr": tpr_at(y, prob, TARGET_FPR),
        }
    return out


def plot_confusion(cm, title, path):
    fig, ax = plt.subplots(figsize=(4.2, 3.6))
    im = ax.imshow(cm, cmap="Blues", vmin=0)
    classes = ["human", "injection"]
    ax.set_xticks([0, 1], classes)
    ax.set_yticks([0, 1], classes)
    ax.set_xlabel("predicted")
    ax.set_ylabel("actual")
    ax.set_title(title, fontsize=10)
    thresh = np.max(cm) / 2
    for i in range(2):
        for j in range(2):
            ax.text(
                j,
                i,
                f"{cm[i][j]}",
                ha="center",
                va="center",
                color="white" if cm[i][j] > thresh else "#1a1a1a",
                fontsize=14,
            )
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_roc(y, prob3, prob5, path):
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    for prob, label, color in (
        (prob3, "v1 feature set (3)", ORANGE),
        (prob5, "v2 feature set (5)", BLUE),
    ):
        fpr, tpr, _ = roc_curve(y, prob)
        ax.plot(
            fpr,
            tpr,
            label=f"{label}, AUC {roc_auc_score(y, prob):.4f}",
            color=color,
            linewidth=2,
        )
    ax.set_xscale("log")
    ax.set_xlim(1e-4, 1.0)
    ax.set_ylim(0.0, 1.02)
    ax.set_xlabel("false positive rate (log)")
    ax.set_ylabel("true positive rate")
    ax.set_title("ROC, subject-held-out 5-fold CV", fontsize=10)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def latency_bench():
    # end-to-end decision cost for one window: feature extraction + predict.
    # uses a realistic injected burst (40 keys at ~5ms gaps with small jitter)
    import joblib

    import features

    bundle = joblib.load(os.path.join(BASE, "Data/model.pkl"))
    model, threshold = bundle["model"], bundle["threshold"]
    # single-row predicts: the n_jobs=-1 thread pool costs ~50ms per call
    model.n_jobs = 1
    rng = np.random.default_rng(SEED)
    gaps = (0.005 + rng.normal(0, 0.0005, 40)).tolist()
    times = []
    for _ in range(300):
        t0 = time.perf_counter()
        vec = features.from_gaps(gaps)
        _ = model.predict_proba([vec])[0][1] >= threshold
        times.append((time.perf_counter() - t0) * 1000)
    return {
        "median_ms": float(np.median(times)),
        "p95_ms": float(np.percentile(times, 95)),
    }


def time_to_block_bench(n_runs=25):
    """Wall-clock time from the first injected keystroke to BlockInput.

    Replays Main.py's runtime loop (listener thread appends, analysis thread
    ticks at 4 Hz, two-window confirmation) against the shipped model bundle.
    The payload is a 5 ms/keystroke burst, a typical fast Rubber Ducky
    profile. The phase offset between payload start and the tick schedule is
    randomized per run, since that offset dominates the latency.
    """
    import threading

    from config import TICK_SECONDS, WINDOW_SECONDS
    from Detector import Detector

    class _RecordingLockscreen:
        def __init__(self):
            self.blocked_at = None

        def block(self):
            self.blocked_at = time.perf_counter()

        def unblock(self):
            pass

    detector = Detector()
    rng = np.random.default_rng(SEED)
    times = []
    for _ in range(n_runs):
        detector.blocked = False
        detector.hits = 0
        detector.Lockscreen = _RecordingLockscreen()
        keys = []
        keys_lock = threading.Lock()
        stop = threading.Event()
        first_key = []

        def inject(stop=stop, keys=keys, keys_lock=keys_lock, first_key=first_key):
            while not stop.is_set():
                with keys_lock:
                    if not first_key:
                        first_key.append(time.perf_counter())
                    keys.append((None, time.time()))
                time.sleep(0.005)

        injector = threading.Thread(target=inject, daemon=True)
        starter = threading.Timer(rng.uniform(0, TICK_SECONDS), injector.start)
        starter.start()
        for _tick in range(40):  # safety bound: 10 s
            time.sleep(TICK_SECONDS)
            now = time.time()
            with keys_lock:
                keys[:] = [k for k in keys if now - k[1] <= WINDOW_SECONDS]
                window = list(keys)
            detector.analyse(window)
            if detector.Lockscreen.blocked_at is not None:
                break
        stop.set()
        starter.cancel()
        if injector.is_alive():
            injector.join()
        if detector.Lockscreen.blocked_at is not None and first_key:
            times.append((detector.Lockscreen.blocked_at - first_key[0]) * 1000)
    return {
        "runs": len(times),
        "median_ms": float(np.median(times)),
        "p95_ms": float(np.percentile(times, 95)),
        "max_ms": float(np.max(times)),
    }


if __name__ == "__main__":
    df = pd.read_csv(os.path.join(BASE, "Data/dataset_v2.csv"))
    y = df["label"].values
    groups = df["subject"].values
    own = df[df["source"].isin(["collected_human", "collected_attack"])]
    rest = df[~df["source"].isin(["collected_human", "collected_attack"])]

    print(f"{len(df)} windows ({(y == 0).sum()} human, {(y == 1).sum()} injection)")

    v1_own = eval_v1_own_data(own)
    v1_cross = eval_v1_cross_dataset(own, rest)

    X5 = build_matrix(df)
    dep_groups = deployment_groups(y, groups)
    v2, prob5 = eval_v2(X5, y, dep_groups)
    v2_unseen, _ = eval_v2(X5, y, groups)
    prob3 = grouped_oof(df[V1_FEATURES].values, y, dep_groups, factory=make_v1_model)

    print("\n                        tpr      fpr      precision  auc")
    for name, m in (
        ("v1 (own data)", v1_own),
        ("v1 (cross-dataset)", v1_cross),
        ("v2 (deployment)", v2),
        ("v2 (unseen speeds)", v2_unseen),
    ):
        print(
            f"  {name:<22} {m['tpr']:.4f}   {m['fpr']:.4f}   {m['precision']:.4f}     {m['auc']:.4f}"
        )
        print(f"    confusion: {m['confusion']}")

    ablation = {
        "v1_features": {
            "auc": roc_auc_score(y, prob3),
            "tpr_at_target_fpr": tpr_at(y, prob3, TARGET_FPR),
        },
        "v2_features": {
            "auc": roc_auc_score(y, prob5),
            "tpr_at_target_fpr": tpr_at(y, prob5, TARGET_FPR),
        },
    }
    print(f"\nFeature ablation, grouped OOF, TPR @ FPR<={TARGET_FPR:.1%}:")
    for name, r in ablation.items():
        print(f"  {name:<12} AUC {r['auc']:.4f}   TPR {r['tpr_at_target_fpr']:.4f}")

    comparison = model_comparison(X5, y, dep_groups)
    print("\nModel comparison (v2 features, grouped OOF):")
    for name, r in comparison.items():
        print(
            f"  {name:<20} AUC {r['auc']:.4f}   TPR@target {r['tpr_at_target_fpr']:.4f}"
        )

    plot_confusion(
        v1_own["confusion"],
        "v1, own data, March protocol",
        os.path.join(RESULTS, "confusion_v1_own.png"),
    )
    plot_confusion(
        v1_cross["confusion"],
        "v1 model on 51 unseen typists",
        os.path.join(RESULTS, "confusion_v1_cross.png"),
    )
    plot_confusion(
        v2["confusion"],
        "v2, subject-held-out, FPR target 0.1%",
        os.path.join(RESULTS, "confusion_v2.png"),
    )
    plot_confusion(
        v2_unseen["confusion"],
        "v2, attack speeds held out of training",
        os.path.join(RESULTS, "confusion_v2_unseen.png"),
    )
    plot_roc(y, prob3, prob5, os.path.join(RESULTS, "roc.png"))

    lat = latency_bench()
    print(
        f"\nPer-window decision cost: median {lat['median_ms']:.2f} ms, "
        f"p95 {lat['p95_ms']:.2f} ms"
    )

    ttb = time_to_block_bench()
    print(
        f"Time from first injected key to input block ({ttb['runs']} runs): "
        f"median {ttb['median_ms']:.0f} ms, p95 {ttb['p95_ms']:.0f} ms, "
        f"max {ttb['max_ms']:.0f} ms"
    )

    with open(os.path.join(RESULTS, "metrics.json"), "w") as f:
        json.dump(
            {
                "dataset": {
                    "windows": len(df),
                    "human": int((y == 0).sum()),
                    "injection": int((y == 1).sum()),
                },
                "v1_own_data": v1_own,
                "v1_cross_dataset": v1_cross,
                "v2_deployment": v2,
                "v2_unseen_speeds": v2_unseen,
                "feature_ablation": ablation,
                "model_comparison": comparison,
                "latency": lat,
                "time_to_block": ttb,
                "protocol": "v2: 5-fold StratifiedGroupKFold by subject/profile, "
                "threshold tuned on inner 3-fold grouped CV of each training fold",
            },
            f,
            indent=2,
        )
    print(f"\nFigures and metrics written to {RESULTS}")
