"""Evaluate trained ONNX models against a labeled holdout set.

Anomalies are injected into normal data by spiking random features to extreme
values — values that should be out-of-distribution for a normally trained model.

Environment variables:
  MODEL_DIR    - directory containing ONNX files (default: ml/models)
  N_HOLDOUT    - normal samples per domain      (default: 1000)
  ANOMALY_RATE - fraction of injected anomalies (default: 0.20)
  RANDOM_SEED  - seed for holdout generation    (default: 99)
"""

import logging
import os
from pathlib import Path

import numpy as np
import onnxruntime as rt
from sklearn.metrics import f1_score, precision_score, recall_score

from ml.train import GENERATOR_CLASSES, generate_training_data

logger = logging.getLogger(__name__)


def inject_anomalies(
    X_normal: np.ndarray,
    anomaly_rate: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Create a labeled holdout by appending synthetic anomalies to normal data.

    Anomaly injection: randomly spike 1–(n_features//2) columns by multiplying
    by an extreme factor, pushing values far outside the training distribution.

    Returns:
        X  — float32 array, shape (n_normal + n_anomaly, n_features), shuffled
        y  — int64 labels: 1 = normal, -1 = anomaly (sklearn convention)
    """
    rng = np.random.default_rng(seed)
    n_anomaly = max(1, int(len(X_normal) * anomaly_rate))

    anomaly_source_idx = rng.choice(len(X_normal), size=n_anomaly, replace=True)
    X_anomaly = X_normal[anomaly_source_idx].copy()

    for row in X_anomaly:
        n_spike = rng.integers(1, max(2, len(row) // 2) + 1)
        spike_cols = rng.choice(len(row), size=n_spike, replace=False)
        for col in spike_cols:
            # Multiply by large factor to create obvious out-of-distribution values
            factor = float(rng.choice([15.0, 20.0, 25.0, 30.0]))
            row[col] = abs(row[col]) * factor + factor

    X = np.vstack([X_normal, X_anomaly]).astype(np.float32)
    y = np.ones(len(X), dtype=np.int64)
    y[len(X_normal) :] = -1

    shuffle = rng.permutation(len(X))
    return X[shuffle], y[shuffle]


def run_inference(onnx_path: Path, X: np.ndarray) -> np.ndarray:
    """Run ONNX model inference and return integer label predictions.

    Returns:
        int64 array of shape (N,) with values {1=normal, -1=anomaly}.
    """
    sess = rt.InferenceSession(str(onnx_path))
    input_name = sess.get_inputs()[0].name
    outputs = sess.run(None, {input_name: X.astype(np.float32)})
    return np.array(outputs[0]).flatten().astype(np.int64)


def evaluate_domain(
    domain: str,
    model_dir: Path,
    n_holdout: int,
    anomaly_rate: float,
    seed: int,
) -> dict:
    """Evaluate one domain ONNX model on a freshly generated labeled holdout set.

    Returns a metrics dict with keys:
        domain, n_samples, n_true_anomaly, n_pred_anomaly,
        precision, recall, f1
    """
    X_normal, _ = generate_training_data(domain, n_holdout, seed=seed)
    X, y_true = inject_anomalies(X_normal, anomaly_rate=anomaly_rate, seed=seed)

    onnx_path = model_dir / f"pulsecore_anomaly_{domain}.onnx"
    if not onnx_path.exists():
        raise FileNotFoundError(
            f"{onnx_path} not found. Run ml/train.py then ml/export_onnx.py first."
        )

    y_pred = run_inference(onnx_path, X)

    precision = precision_score(y_true, y_pred, pos_label=-1, zero_division=0)
    recall = recall_score(y_true, y_pred, pos_label=-1, zero_division=0)
    f1 = f1_score(y_true, y_pred, pos_label=-1, zero_division=0)

    return {
        "domain": domain,
        "n_samples": int(len(y_true)),
        "n_true_anomaly": int((y_true == -1).sum()),
        "n_pred_anomaly": int((y_pred == -1).sum()),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
    }


def print_report(results: list[dict]) -> None:
    """Print a formatted evaluation report to stdout."""
    print()
    print("=" * 68)
    print("   PulseCore — Isolation Forest Anomaly Detection Report")
    print("=" * 68)
    print(
        f"   {'Domain':<14} {'Samples':>8} {'True+':<8} {'Pred+':<8} "
        f"{'Prec':>7} {'Recall':>8} {'F1':>7}"
    )
    print("-" * 68)
    for r in results:
        print(
            f"   {r['domain']:<14} {r['n_samples']:>8} "
            f"{r['n_true_anomaly']:<8} {r['n_pred_anomaly']:<8} "
            f"{r['precision']:>7.4f} {r['recall']:>8.4f} {r['f1']:>7.4f}"
        )
    print("=" * 68)
    avg_f1 = sum(r["f1"] for r in results) / len(results)
    avg_p = sum(r["precision"] for r in results) / len(results)
    avg_r = sum(r["recall"] for r in results) / len(results)
    print(
        f"   {'AVERAGE':<14} {'':>8} {'':>8} {'':>8} "
        f"{avg_p:>7.4f} {avg_r:>8.4f} {avg_f1:>7.4f}"
    )
    print("=" * 68)
    print()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    model_dir = Path(os.environ.get("MODEL_DIR", "ml/models"))
    n_holdout = int(os.environ.get("N_HOLDOUT", "1000"))
    anomaly_rate = float(os.environ.get("ANOMALY_RATE", "0.20"))
    seed = int(os.environ.get("RANDOM_SEED", "99"))

    results = []
    for domain in GENERATOR_CLASSES:
        logger.info("Evaluating domain=%s …", domain)
        result = evaluate_domain(domain, model_dir, n_holdout, anomaly_rate, seed)
        results.append(result)

    print_report(results)


if __name__ == "__main__":
    main()
