"""ONNX model wrapper: load once at startup, run inference per request.

Env vars (consumed by main.py, passed to Predictor.__init__):
  ONNX_MODEL_PATH   path to pulsecore_anomaly_{domain}.onnx
  FEATURE_MAP_PATH  path to feature_map.json  (default: same dir as model)
"""

import json
import logging
import math
import time
from collections import deque
from pathlib import Path

import numpy as np
import onnxruntime as rt

from inference.schemas import AnomalyResult, PredictRequest

logger = logging.getLogger(__name__)

_AUTO_FLAG_THRESHOLD: float = 0.85
_SOFT_ALERT_THRESHOLD: float = 0.60
_SIGMOID_K: float = 45.0  # calibrated for skl2onnx IF score range ≈ [-0.1, +0.1]
_P99_LOG_INTERVAL: int = 100  # log P99 latency every N requests


def _get_tier(score: float) -> str:
    if score > _AUTO_FLAG_THRESHOLD:
        return "auto_flag"
    if score >= _SOFT_ALERT_THRESHOLD:
        return "soft_alert"
    return "log_only"


class Predictor:
    """Stateless (after init) inference engine backed by a single ONNX model.

    Model is loaded once; all state is read-only after __init__ except for the
    latency deque, which is only written from the async event loop (safe under GIL).
    """

    def __init__(self, model_path: Path, feature_map_path: Path) -> None:
        if not model_path.exists():
            raise RuntimeError(
                f"ONNX model not found at {model_path}. "
                "Run `python -m ml.train && python -m ml.export_onnx` first."
            )
        if not feature_map_path.exists():
            raise RuntimeError(
                f"feature_map.json not found at {feature_map_path}. "
                "Run `python -m ml.export_onnx` first."
            )

        self._session = rt.InferenceSession(str(model_path))
        self._input_name: str = self._session.get_inputs()[0].name

        feature_map = json.loads(feature_map_path.read_text())

        # Infer domain from model filename: pulsecore_anomaly_{domain}.onnx
        self._domain = model_path.stem.replace("pulsecore_anomaly_", "")
        domain_config = feature_map["domains"].get(self._domain)
        if domain_config is None:
            raise RuntimeError(
                f"Domain {self._domain!r} not found in feature_map.json. "
                f"Available: {list(feature_map['domains'])}"
            )

        self._feature_names: list[str] = domain_config["features"]
        self._n_features: int = domain_config["n_features"]

        self._request_count = 0
        self._recent_latencies: deque[float] = deque(maxlen=_P99_LOG_INTERVAL)

        logger.info(
            "Predictor ready: domain=%s n_features=%d input=%s",
            self._domain,
            self._n_features,
            self._input_name,
        )

    @property
    def domain(self) -> str:
        return self._domain

    def predict(self, request: PredictRequest) -> AnomalyResult:
        """Run one inference. Raises:
        - ValueError  if request.domain doesn't match the loaded model
        - KeyError    if any feature_map key is absent from request.metrics
        """
        if request.domain != self._domain:
            raise ValueError(
                f"Model is loaded for domain {self._domain!r}; "
                f"received request for domain {request.domain!r}."
            )

        t0 = time.perf_counter()

        try:
            feature_vector = [request.metrics[f] for f in self._feature_names]
        except KeyError as exc:
            raise KeyError(
                f"Missing feature {exc} in metrics for domain {self._domain!r}. "
                f"Expected: {self._feature_names}"
            ) from exc

        X = np.array([feature_vector], dtype=np.float32)
        outputs = self._session.run(None, {self._input_name: X})

        label = int(np.array(outputs[0]).flatten()[0])
        anomaly_score = self._compute_score(outputs, label)
        tier = _get_tier(anomaly_score)

        latency_ms = (time.perf_counter() - t0) * 1000.0
        self._track_latency(latency_ms)

        return AnomalyResult(
            source_id=request.source_id,
            domain=request.domain,
            timestamp=request.timestamp,
            anomaly_score=round(anomaly_score, 6),
            confidence_tier=tier,
            is_anomaly=(tier == "auto_flag"),
            raw_label=label,
            latency_ms=round(latency_ms, 3),
        )

    def _compute_score(self, outputs: list, label: int) -> float:
        """Map ONNX raw output to an anomaly score in [0.0, 1.0].

        IsolationForest decision_function semantics:
            More negative → more anomalous.
            More positive → more normal.

        We apply sigmoid(-raw_score * k) so that (with k=45 for skl2onnx range ~[-0.1, +0.1]):
            raw_score = -0.05 → sigmoid(2.25) ≈ 0.905  (auto_flag)
            raw_score =  0.00 → sigmoid(0.0)  = 0.500  (soft_alert boundary)
            raw_score = +0.07 → sigmoid(-3.15) ≈ 0.041 (log_only)

        If the raw score cannot be extracted, fall back to a label-based heuristic.
        """
        raw_score: float | None = self._extract_raw_score(outputs)

        if raw_score is None:
            logger.debug("Raw score unavailable; using label heuristic (label=%d)", label)
            return 0.9 if label == -1 else 0.15

        anomaly_score = 1.0 / (1.0 + math.exp(raw_score * _SIGMOID_K))
        return float(np.clip(anomaly_score, 0.0, 1.0))

    @staticmethod
    def _extract_raw_score(outputs: list) -> float | None:
        """Extract the class-(-1) score from outputs[1] if present."""
        if len(outputs) < 2:
            return None

        scores_output = outputs[1]

        if isinstance(scores_output, (list, tuple)) and scores_output:
            first = scores_output[0]
            if isinstance(first, dict):
                # skl2onnx SequenceType[MapType[int64, float32]]
                for k, v in first.items():
                    if int(k) == -1:
                        return float(v)
            elif isinstance(first, (int, float, np.floating)):
                return float(first)

        if isinstance(scores_output, np.ndarray):
            return float(scores_output.flat[0])

        return None

    def _track_latency(self, latency_ms: float) -> None:
        self._recent_latencies.append(latency_ms)
        self._request_count += 1
        if self._request_count % _P99_LOG_INTERVAL == 0:
            sorted_lats = sorted(self._recent_latencies)
            p99_idx = max(0, int(len(sorted_lats) * 0.99) - 1)
            logger.info(
                "P99 inference latency (last %d requests): %.3fms  "
                "[mean=%.3fms  max=%.3fms]",
                len(sorted_lats),
                sorted_lats[p99_idx],
                sum(sorted_lats) / len(sorted_lats),
                sorted_lats[-1],
            )
