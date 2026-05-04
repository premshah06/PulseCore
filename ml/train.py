"""Train one Isolation Forest per domain using the project's synthetic generators.

Environment variables:
  N_SAMPLES     - training samples per domain          (default: 5000)
  N_ESTIMATORS  - number of trees in each forest       (default: 100)
  MAX_SAMPLES   - samples per tree: int, float, "auto" (default: auto)
  CONTAMINATION - expected anomaly fraction            (default: 0.05)
  RANDOM_SEED   - global random seed                   (default: 42)
  MODEL_DIR     - output directory for .pkl files      (default: ml/models)
"""

import logging
import os
import pickle
from pathlib import Path

import numpy as np
from sklearn.ensemble import IsolationForest

from producer.generators import EcommerceGenerator, InfraGenerator, IotGenerator

logger = logging.getLogger(__name__)

GENERATOR_CLASSES: dict[str, type] = {
    "infra": InfraGenerator,
    "ecommerce": EcommerceGenerator,
    "iot": IotGenerator,
}


def _parse_max_samples(raw: str):
    """Parse MAX_SAMPLES env var: "auto" | float in (0,1] | positive int."""
    if raw.strip().lower() == "auto":
        return "auto"
    try:
        v = float(raw)
        return int(v) if v > 1.0 else v
    except ValueError:
        return "auto"


def get_feature_names(domain: str) -> list[str]:
    """Return a deterministic, sorted list of metric keys for the given domain.

    Sorted alphabetically so the ordering is stable across Python versions and runs.
    This list is the canonical column order for the ONNX input tensor.
    """
    gen = GENERATOR_CLASSES[domain]()
    return sorted(gen.generate().metrics.keys())


def generate_training_data(
    domain: str,
    n_samples: int,
    seed: int,
) -> tuple[np.ndarray, list[str]]:
    """Generate synthetic normal-mode training data for one domain.

    Returns:
        X            float32 array of shape (n_samples, n_features)
        feature_names sorted list of metric names — matches X column order
    """
    gen = GENERATOR_CLASSES[domain]()
    feature_names = get_feature_names(domain)
    rows = [[event.metrics[f] for f in feature_names] for _ in range(n_samples) if (event := gen.generate()) or True]
    return np.array(rows, dtype=np.float32), feature_names


def train_isolation_forest(
    X: np.ndarray,
    n_estimators: int = 100,
    max_samples="auto",
    contamination: float = 0.05,
    random_seed: int = 42,
) -> IsolationForest:
    """Fit an IsolationForest and return the fitted model."""
    model = IsolationForest(
        n_estimators=n_estimators,
        max_samples=max_samples,
        contamination=contamination,
        random_state=random_seed,
    )
    model.fit(X)
    logger.info(
        "Trained IsolationForest n_estimators=%d max_samples=%s contamination=%.3f",
        n_estimators,
        max_samples,
        contamination,
    )
    return model


def train_all(
    n_samples: int = 5000,
    n_estimators: int = 100,
    max_samples="auto",
    contamination: float = 0.05,
    random_seed: int = 42,
) -> dict[str, tuple[IsolationForest, list[str]]]:
    """Train one IsolationForest per domain.

    Returns:
        {domain: (fitted_model, feature_names)}
    """
    results = {}
    for domain in GENERATOR_CLASSES:
        logger.info("Generating %d samples for domain=%s …", n_samples, domain)
        X, feature_names = generate_training_data(domain, n_samples, seed=random_seed)
        model = train_isolation_forest(
            X,
            n_estimators=n_estimators,
            max_samples=max_samples,
            contamination=contamination,
            random_seed=random_seed,
        )
        results[domain] = (model, feature_names)
    return results


def save_models(
    models: dict[str, tuple[IsolationForest, list[str]]],
    model_dir: Path,
) -> None:
    """Pickle trained models for later ONNX export (not for production serving)."""
    model_dir.mkdir(parents=True, exist_ok=True)
    for domain, (model, _) in models.items():
        path = model_dir / f"isolation_forest_{domain}.pkl"
        with open(path, "wb") as f:
            pickle.dump(model, f)
        logger.info("Saved %s", path)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    n_samples = int(os.environ.get("N_SAMPLES", "5000"))
    n_estimators = int(os.environ.get("N_ESTIMATORS", "100"))
    max_samples = _parse_max_samples(os.environ.get("MAX_SAMPLES", "auto"))
    contamination = float(os.environ.get("CONTAMINATION", "0.05"))
    random_seed = int(os.environ.get("RANDOM_SEED", "42"))
    model_dir = Path(os.environ.get("MODEL_DIR", "ml/models"))

    logger.info(
        "Config: n_samples=%d n_estimators=%d max_samples=%s contamination=%.3f seed=%d",
        n_samples,
        n_estimators,
        max_samples,
        contamination,
        random_seed,
    )

    models = train_all(
        n_samples=n_samples,
        n_estimators=n_estimators,
        max_samples=max_samples,
        contamination=contamination,
        random_seed=random_seed,
    )
    save_models(models, model_dir)
    logger.info("Training complete. Models saved to %s", model_dir)


if __name__ == "__main__":
    main()
