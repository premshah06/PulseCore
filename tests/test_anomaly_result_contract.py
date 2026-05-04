"""Contract test: AnomalyResult output shape pinned for Phase 5 consumption.

Phase 5 (FastAPI backend) calls POST /predict and reads these exact fields.
Any change here must be coordinated with Phase 5 and CONTRACTS.md.
"""

import json
from collections import deque
from datetime import UTC, datetime
from unittest.mock import MagicMock

import numpy as np
import pytest

from inference.predictor import Predictor
from inference.schemas import AnomalyResult, PredictRequest
from ml.train import get_feature_names

_REQUIRED_FIELDS = {
    "source_id", "domain", "timestamp", "anomaly_score",
    "confidence_tier", "is_anomaly", "raw_label", "latency_ms",
}
_VALID_TIERS = {"auto_flag", "soft_alert", "log_only"}


def _mock_predictor(domain: str = "infra", label: int = 1, raw_score: float = 0.07) -> Predictor:
    p = Predictor.__new__(Predictor)
    p._domain = domain
    p._feature_names = get_feature_names(domain)
    p._n_features = len(p._feature_names)
    p._request_count = 0
    p._recent_latencies = deque(maxlen=100)
    p._input_name = "float_input"
    mock_sess = MagicMock()
    mock_sess.run.return_value = [np.array([[label]]), np.array([[raw_score]])]
    p._session = mock_sess
    return p


def _make_result(domain: str = "infra", label: int = -1, raw_score: float = -0.5) -> AnomalyResult:
    p = _mock_predictor(domain=domain, label=label, raw_score=raw_score)
    feature_names = get_feature_names(domain)
    req = PredictRequest(
        source_id="contract-src",
        domain=domain,
        metrics={f: 50.0 for f in feature_names},
        timestamp=datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC),
    )
    return p.predict(req)


class TestAnomalyResultContract:
    """Every assertion here is a Phase 5 dependency."""

    def setup_method(self):
        self.result = _make_result()

    # ── Required field presence ────────────────────────────────────────────────

    def test_all_required_fields_present(self):
        data = self.result.model_dump()
        missing = _REQUIRED_FIELDS - set(data.keys())
        assert not missing, f"Phase 5 contract broken — missing fields: {missing}"

    # ── Field types ───────────────────────────────────────────────────────────

    def test_source_id_is_str(self):
        assert isinstance(self.result.source_id, str)

    def test_domain_is_str(self):
        assert isinstance(self.result.domain, str)

    def test_timestamp_is_utc_datetime(self):
        assert isinstance(self.result.timestamp, datetime)
        assert self.result.timestamp.tzinfo is not None

    def test_anomaly_score_is_float(self):
        assert isinstance(self.result.anomaly_score, float)

    def test_anomaly_score_in_0_1(self):
        assert 0.0 <= self.result.anomaly_score <= 1.0

    def test_confidence_tier_is_valid_literal(self):
        assert self.result.confidence_tier in _VALID_TIERS

    def test_is_anomaly_is_bool(self):
        assert isinstance(self.result.is_anomaly, bool)

    def test_raw_label_is_int(self):
        assert isinstance(self.result.raw_label, int)

    def test_raw_label_is_1_or_minus1(self):
        assert self.result.raw_label in {1, -1}

    def test_latency_ms_is_positive_float(self):
        assert isinstance(self.result.latency_ms, float)
        assert self.result.latency_ms > 0

    # ── Semantic invariants ────────────────────────────────────────────────────

    def test_is_anomaly_true_iff_auto_flag(self):
        for label, raw_score in [(-1, -0.5), (1, 0.5)]:
            r = _make_result(label=label, raw_score=raw_score)
            assert r.is_anomaly == (r.confidence_tier == "auto_flag"), (
                f"is_anomaly={r.is_anomaly} inconsistent with tier={r.confidence_tier}"
            )

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_domain_field_matches_request(self, domain):
        r = _make_result(domain=domain)
        assert r.domain == domain

    # ── JSON serialization ────────────────────────────────────────────────────

    def test_model_dump_json_is_valid_utf8(self):
        raw = self.result.model_dump_json()
        assert isinstance(raw, str)
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)

    def test_json_contains_all_required_keys(self):
        parsed = json.loads(self.result.model_dump_json())
        missing = _REQUIRED_FIELDS - set(parsed.keys())
        assert not missing, f"JSON missing fields: {missing}"

    def test_json_anomaly_score_is_number(self):
        parsed = json.loads(self.result.model_dump_json())
        assert isinstance(parsed["anomaly_score"], (int, float))

    def test_json_confidence_tier_is_string(self):
        parsed = json.loads(self.result.model_dump_json())
        assert isinstance(parsed["confidence_tier"], str)

    def test_json_is_anomaly_is_boolean(self):
        parsed = json.loads(self.result.model_dump_json())
        assert isinstance(parsed["is_anomaly"], bool)

    def test_json_round_trip_preserves_score(self):
        raw = self.result.model_dump_json()
        restored = AnomalyResult.model_validate_json(raw)
        assert abs(restored.anomaly_score - self.result.anomaly_score) < 1e-6

    # ── Three-domain coverage ─────────────────────────────────────────────────

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_all_domains_produce_valid_result(self, domain):
        r = _make_result(domain=domain, label=-1, raw_score=-0.5)
        assert r.confidence_tier in _VALID_TIERS
        assert 0.0 <= r.anomaly_score <= 1.0
        assert r.raw_label in {1, -1}

    # ── Confidence tier contract values ───────────────────────────────────────

    def test_auto_flag_tier_produces_is_anomaly_true(self):
        r = _make_result(label=-1, raw_score=-0.5)
        assert r.confidence_tier == "auto_flag"
        assert r.is_anomaly is True

    def test_log_only_tier_produces_is_anomaly_false(self):
        r = _make_result(label=1, raw_score=0.5)
        assert r.confidence_tier == "log_only"
        assert r.is_anomaly is False
