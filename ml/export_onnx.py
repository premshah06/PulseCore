"""Export trained IsolationForest models (.pkl) to ONNX + write feature_map.json.

Environment variables:
  MODEL_DIR - directory containing isolation_forest_{domain}.pkl files (default: ml/models)

Output files (all under MODEL_DIR):
  pulsecore_anomaly_{domain}.onnx   - one per domain
  feature_map.json              - Phase 4 input tensor contract
"""

import json
import logging
import os
import pickle
from pathlib import Path

from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
from sklearn.ensemble import IsolationForest

from ml.train import GENERATOR_CLASSES, get_feature_names

logger = logging.getLogger(__name__)


def export_to_onnx(
    model: IsolationForest,
    domain: str,
    feature_names: list[str],
    output_dir: Path,
) -> Path:
    """Convert a fitted IsolationForest to ONNX and write it to output_dir.

    Input tensor name:  "float_input"
    Input tensor shape: [N, len(feature_names)]  (N = batch size, any value)
    Input tensor dtype: float32
    """
    n_features = len(feature_names)
    initial_types = [("float_input", FloatTensorType([None, n_features]))]

    onnx_model = convert_sklearn(
        model,
        initial_types=initial_types,
        target_opset={"": 17, "ai.onnx.ml": 3},
    )

    onnx_path = output_dir / f"pulsecore_anomaly_{domain}.onnx"
    onnx_path.write_bytes(onnx_model.SerializeToString())
    logger.info("Exported ONNX for domain=%s (%d features) → %s", domain, n_features, onnx_path)
    return onnx_path


def _introspect_outputs(onnx_path: Path) -> list[dict]:
    """Return output metadata by running onnxruntime on the saved model."""
    import onnxruntime as rt

    sess = rt.InferenceSession(str(onnx_path))
    return [
        {"name": o.name, "type": str(o.type), "shape": list(o.shape or [])}
        for o in sess.get_outputs()
    ]


def build_feature_map(
    domain_features: dict[str, list[str]],
    output_dir: Path,
) -> Path:
    """Write feature_map.json — the Phase 4 input tensor contract.

    Schema:
      domains.<domain>.features     — ordered list of StreamEvent.metrics keys
      domains.<domain>.n_features   — len(features)
      domains.<domain>.model_file   — ONNX filename in MODEL_DIR
      domains.<domain>.input_name   — ONNX input tensor name
      domains.<domain>.input_dtype  — always "float32"
      domains.<domain>.input_shape  — [null, n_features]  (null = dynamic batch)
      domains.<domain>.outputs      — list of {name, description} for Phase 4
    """
    domains_section = {}
    for domain, features in domain_features.items():
        onnx_path = output_dir / f"pulsecore_anomaly_{domain}.onnx"
        raw_outputs = _introspect_outputs(onnx_path) if onnx_path.exists() else []

        domains_section[domain] = {
            "features": features,
            "n_features": len(features),
            "model_file": f"pulsecore_anomaly_{domain}.onnx",
            "input_name": "float_input",
            "input_dtype": "float32",
            "input_shape": [None, len(features)],
            "outputs": raw_outputs or [
                {
                    "name": "label",
                    "description": "Anomaly label: 1=normal, -1=anomaly (int64)",
                },
                {
                    "name": "scores",
                    "description": (
                        "Per-class anomaly score map. "
                        "scores[-1] is the anomaly confidence (lower = more anomalous)."
                    ),
                },
            ],
        }

    feature_map = {
        "version": "1.0",
        "description": (
            "Canonical input tensor specification for PulseCore anomaly models. "
            "Phase 4 must extract StreamEvent.metrics in the exact column order "
            "specified by domains.<domain>.features."
        ),
        "domains": domains_section,
    }

    feature_map_path = output_dir / "feature_map.json"
    feature_map_path.write_text(json.dumps(feature_map, indent=2))
    logger.info("Wrote feature_map.json → %s", feature_map_path)
    return feature_map_path


def export_all(model_dir: Path) -> dict[str, Path]:
    """Load .pkl models, export each domain to ONNX, write feature_map.json.

    Returns {domain: onnx_path}.
    Raises FileNotFoundError if any domain .pkl is missing (run ml/train.py first).
    """
    model_dir.mkdir(parents=True, exist_ok=True)

    domain_features: dict[str, list[str]] = {}
    onnx_paths: dict[str, Path] = {}

    for domain in GENERATOR_CLASSES:
        pkl_path = model_dir / f"isolation_forest_{domain}.pkl"
        if not pkl_path.exists():
            raise FileNotFoundError(
                f"isolation_forest_{domain}.pkl not found in {model_dir}. "
                "Run `python -m ml.train` first."
            )

        with open(pkl_path, "rb") as f:
            model: IsolationForest = pickle.load(f)

        feature_names = get_feature_names(domain)
        domain_features[domain] = feature_names
        onnx_paths[domain] = export_to_onnx(model, domain, feature_names, model_dir)

    build_feature_map(domain_features, model_dir)
    return onnx_paths


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    model_dir = Path(os.environ.get("MODEL_DIR", "ml/models"))
    logger.info("Exporting models from %s …", model_dir)

    paths = export_all(model_dir)
    for domain, path in paths.items():
        logger.info("  %-12s → %s", domain, path)
    logger.info("Export complete.")


if __name__ == "__main__":
    main()
