"""Unit tests for inference/predictor.py."""

import math
from collections import deque
from datetime import UTC, datetime
from unittest.mock import MagicMock

import numpy as np
import pytest

from inference.predictor import (
    _AUTO_FLAG_THRESHOLD,
    _SIGMOID_K,
    _SOFT_ALERT_THRESHOLD,
    Predictor,
    _get_tier,
)
from inference.schemas import AnomalyResult, PredictRequest
from ml.train import get_feature_names

# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_request(
    domain: str = "infra",
    source_id: str = "test-src",
    metrics: dict | None = None,
) -> PredictRequest:
    feature_names = get_feature_names(domain)
    return PredictRequest(
        source_id=source_id,
        domain=domain,
        metrics=metrics or {f: 50.0 for f in feature_names},
        timestamp=datetime.now(UTC),
    )


def _make_predictor(
    domain: str = "infra",
    label: int = 1,
    raw_score: float = 0.07,
) -> Predictor:
    """Build a Predictor with a mocked ONNX session — no model files required."""
    feature_names = get_feature_names(domain)

    p = Predictor.__new__(Predictor)
    p._domain = domain
    p._feature_names = feature_names
    p._n_features = len(feature_names)
    p._request_count = 0
    p._recent_latencies = deque(maxlen=100)
    p._input_name = "float_input"

    mock_sess = MagicMock()
    mock_sess.run.return_value = [
        np.array([[label]]),         # outputs[0]: label
        np.array([[raw_score]]),     # outputs[1]: raw anomaly score
    ]
    p._session = mock_sess
    return p


# ── Module-scoped fixture: real tiny ONNX model ────────────────────────────────

@pytest.fixture(scope="module")
def model_dir(tmp_path_factory):
    from ml.export_onnx import export_all
    from ml.train import save_models, train_all

    d = tmp_path_factory.mktemp("pred_models")
    models = train_all(n_samples=400, n_estimators=15, contamination=0.05, random_seed=42)
    save_models(models, d)
    export_all(d)
    return d


@pytest.fixture(scope="module")
def real_predictor(model_dir):
    return Predictor(
        model_path=model_dir / "vigil_anomaly_infra.onnx",
        feature_map_path=model_dir / "feature_map.json",
    )


# ── _get_tier ──────────────────────────────────────────────────────────────────

class TestGetTier:
    def test_score_above_085_is_auto_flag(self):
        assert _get_tier(0.851) == "auto_flag"

    def test_score_at_085_is_soft_alert(self):
        # Boundary: 0.85 is NOT strictly > 0.85
        assert _get_tier(0.85) == "soft_alert"

    def test_score_at_060_is_soft_alert(self):
        assert _get_tier(0.60) == "soft_alert"

    def test_score_just_below_060_is_log_only(self):
        assert _get_tier(0.5999) == "log_only"

    def test_score_zero_is_log_only(self):
        assert _get_tier(0.0) == "log_only"

    def test_score_one_is_auto_flag(self):
        assert _get_tier(1.0) == "auto_flag"

    def test_score_0_75_is_soft_alert(self):
        assert _get_tier(0.75) == "soft_alert"

    @pytest.mark.parametrize("score,expected", [
        (0.0, "log_only"),
        (0.30, "log_only"),
        (0.599, "log_only"),
        (0.60, "soft_alert"),
        (0.72, "soft_alert"),
        (0.85, "soft_alert"),
        (0.851, "auto_flag"),
        (0.90, "auto_flag"),
        (1.0, "auto_flag"),
    ])
    def test_tier_table(self, score, expected):
        assert _get_tier(score) == expected


# ── Predictor scoring with mocked session ─────────────────────────────────────

class TestPredictorScoring:
    def test_known_anomalous_raw_score_produces_above_085(self):
        """Mock a very negative raw score → anomaly_score must exceed 0.85."""
        predictor = _make_predictor(label=-1, raw_score=-0.5)
        request = _make_request()
        result = predictor.predict(request)
        assert result.anomaly_score > _AUTO_FLAG_THRESHOLD, (
            f"Expected anomaly_score > {_AUTO_FLAG_THRESHOLD}, got {result.anomaly_score}"
        )

    def test_known_anomalous_raw_score_produces_auto_flag_tier(self):
        predictor = _make_predictor(label=-1, raw_score=-0.5)
        result = predictor.predict(_make_request())
        assert result.confidence_tier == "auto_flag"

    def test_known_normal_raw_score_produces_below_060(self):
        """Mock a positive raw score → anomaly_score must be below 0.60."""
        predictor = _make_predictor(label=1, raw_score=0.5)
        request = _make_request()
        result = predictor.predict(request)
        assert result.anomaly_score < _SOFT_ALERT_THRESHOLD, (
            f"Expected anomaly_score < {_SOFT_ALERT_THRESHOLD}, got {result.anomaly_score}"
        )

    def test_known_normal_raw_score_produces_log_only_tier(self):
        predictor = _make_predictor(label=1, raw_score=0.5)
        result = predictor.predict(_make_request())
        assert result.confidence_tier == "log_only"

    def test_zero_raw_score_produces_near_0_5(self):
        predictor = _make_predictor(raw_score=0.0)
        result = predictor.predict(_make_request())
        assert abs(result.anomaly_score - 0.5) < 0.01, (
            f"Zero raw score should give ~0.5, got {result.anomaly_score}"
        )

    def test_is_anomaly_true_for_auto_flag(self):
        predictor = _make_predictor(label=-1, raw_score=-0.5)
        result = predictor.predict(_make_request())
        assert result.is_anomaly is True

    def test_is_anomaly_false_for_non_auto_flag(self):
        predictor = _make_predictor(label=1, raw_score=0.5)
        result = predictor.predict(_make_request())
        assert result.is_anomaly is False

    def test_raw_label_preserved_from_onnx(self):
        predictor = _make_predictor(label=-1, raw_score=-0.3)
        result = predictor.predict(_make_request())
        assert result.raw_label == -1

    def test_latency_ms_is_positive(self):
        predictor = _make_predictor()
        result = predictor.predict(_make_request())
        assert result.latency_ms > 0

    def test_source_id_preserved(self):
        predictor = _make_predictor()
        result = predictor.predict(_make_request(source_id="my-host"))
        assert result.source_id == "my-host"

    def test_timestamp_preserved(self):
        ts = datetime(2024, 3, 1, 10, 0, 0, tzinfo=UTC)
        predictor = _make_predictor()
        req = PredictRequest(
            source_id="s",
            domain="infra",
            metrics={f: 1.0 for f in get_feature_names("infra")},
            timestamp=ts,
        )
        assert predictor.predict(req).timestamp == ts

    def test_sigmoid_math_precision(self):
        """Verify the sigmoid formula used in _compute_score is numerically correct."""
        raw = -0.05
        expected = 1.0 / (1.0 + math.exp(raw * _SIGMOID_K))
        predictor = _make_predictor(raw_score=raw)
        result = predictor.predict(_make_request())
        assert abs(result.anomaly_score - expected) < 1e-5


# ── Missing feature / validation errors ───────────────────────────────────────

class TestPredictorValidation:
    def test_missing_feature_raises_key_error(self):
        predictor = _make_predictor()
        req = PredictRequest(
            source_id="s",
            domain="infra",
            metrics={"cpu_user_pct": 50.0},  # only one feature, rest missing
            timestamp=datetime.now(UTC),
        )
        with pytest.raises(KeyError, match="Missing feature"):
            predictor.predict(req)

    def test_missing_feature_error_message_names_the_key(self):
        predictor = _make_predictor()
        req = PredictRequest(
            source_id="s",
            domain="infra",
            metrics={"cpu_user_pct": 50.0},
            timestamp=datetime.now(UTC),
        )
        try:
            predictor.predict(req)
        except KeyError as exc:
            assert "Missing feature" in str(exc)

    def test_domain_mismatch_raises_value_error(self):
        predictor = _make_predictor(domain="infra")
        req = _make_request(domain="iot")
        with pytest.raises(ValueError, match="domain"):
            predictor.predict(req)

    def test_domain_mismatch_error_names_both_domains(self):
        predictor = _make_predictor(domain="infra")
        req = _make_request(domain="iot")
        try:
            predictor.predict(req)
        except ValueError as exc:
            msg = str(exc)
            assert "infra" in msg
            assert "iot" in msg


# ── Model loading errors ───────────────────────────────────────────────────────

class TestPredictorInit:
    def test_missing_model_raises_runtime_error(self, tmp_path):
        with pytest.raises(RuntimeError, match="ONNX model not found"):
            Predictor(
                model_path=tmp_path / "nonexistent.onnx",
                feature_map_path=tmp_path / "feature_map.json",
            )

    def test_missing_feature_map_raises_runtime_error(self, tmp_path, model_dir):
        with pytest.raises(RuntimeError, match="feature_map.json not found"):
            Predictor(
                model_path=model_dir / "vigil_anomaly_infra.onnx",
                feature_map_path=tmp_path / "nonexistent.json",
            )

    def test_real_model_loads_correctly(self, real_predictor):
        assert real_predictor.domain == "infra"

    def test_real_model_domain_property(self, real_predictor):
        assert real_predictor.domain in {"infra", "ecommerce", "iot"}


# ── Real model inference (integration-level) ──────────────────────────────────

class TestPredictorRealModel:
    def test_predict_returns_anomaly_result(self, real_predictor):
        result = real_predictor.predict(_make_request())
        assert isinstance(result, AnomalyResult)

    def test_predict_score_in_0_1(self, real_predictor):
        result = real_predictor.predict(_make_request())
        assert 0.0 <= result.anomaly_score <= 1.0

    def test_extreme_input_gives_higher_score_than_normal(self, real_predictor):
        feature_names = get_feature_names("infra")
        normal_req = _make_request(metrics={f: 50.0 for f in feature_names})
        extreme_req = _make_request(metrics={f: 99999.0 for f in feature_names})
        normal_result = real_predictor.predict(normal_req)
        extreme_result = real_predictor.predict(extreme_req)
        assert extreme_result.anomaly_score > normal_result.anomaly_score, (
            f"Extreme input ({extreme_result.anomaly_score:.4f}) should score "
            f"higher than normal ({normal_result.anomaly_score:.4f})"
        )

    def test_extreme_input_produces_auto_flag(self, real_predictor):
        feature_names = get_feature_names("infra")
        result = real_predictor.predict(
            _make_request(metrics={f: 99999.0 for f in feature_names})
        )
        assert result.confidence_tier == "auto_flag", (
            f"Expected auto_flag for extreme input, got {result.confidence_tier} "
            f"(score={result.anomaly_score:.4f})"
        )

    def test_label_is_1_or_minus1(self, real_predictor):
        result = real_predictor.predict(_make_request())
        assert result.raw_label in {1, -1}

    def test_is_anomaly_consistent_with_tier(self, real_predictor):
        result = real_predictor.predict(_make_request())
        assert result.is_anomaly == (result.confidence_tier == "auto_flag")
