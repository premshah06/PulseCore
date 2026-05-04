"""Contract test: LiveUpdate WebSocket payload pinned for Phase 6 (Next.js dashboard).

The frontend TypeScript interface is:
  interface LiveUpdate {
    type: "anomaly";
    data: {
      id: string;
      source_id: string;
      domain: string;
      timestamp: string;      // ISO-8601
      anomaly_score: number;  // [0, 1]
      confidence_tier: "auto_flag" | "soft_alert" | "log_only";
      is_anomaly: boolean;
      raw_label: number;      // 1 or -1
      latency_ms: number;
      detected_at: string;    // ISO-8601
    };
  }

Any change to LiveUpdate or AnomalyRecord must be coordinated with Phase 6.
"""

import json
from datetime import UTC, datetime

import pytest

from api.schemas import AnomalyRecord, LiveUpdate

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)

_REQUIRED_TOP_KEYS = {"type", "data"}
_REQUIRED_DATA_KEYS = {
    "id", "source_id", "domain", "timestamp",
    "anomaly_score", "confidence_tier", "is_anomaly",
    "raw_label", "latency_ms", "detected_at",
}
_VALID_TIERS = {"auto_flag", "soft_alert", "log_only"}


def _make_live_update(tier: str = "auto_flag", score: float = 0.92) -> LiveUpdate:
    record = AnomalyRecord(
        id="507f1f77bcf86cd799439011",
        source_id="host-1",
        domain="infra",
        timestamp=_NOW,
        anomaly_score=score,
        confidence_tier=tier,
        is_anomaly=(tier == "auto_flag"),
        raw_label=-1 if tier == "auto_flag" else 1,
        latency_ms=1.5,
        detected_at=_NOW,
    )
    return LiveUpdate(type="anomaly", data=record)


class TestLiveUpdateContract:
    """Every assertion here is a Phase 6 dependency."""

    def setup_method(self):
        self.update = _make_live_update()
        self.payload = json.loads(self.update.model_dump_json())

    # ── Top-level shape ────────────────────────────────────────────────────────

    def test_all_top_level_keys_present(self):
        missing = _REQUIRED_TOP_KEYS - set(self.payload.keys())
        assert not missing, f"Phase 6 contract broken — missing top keys: {missing}"

    def test_type_is_anomaly_string(self):
        assert self.payload["type"] == "anomaly"

    def test_data_is_object(self):
        assert isinstance(self.payload["data"], dict)

    # ── data sub-object keys ───────────────────────────────────────────────────

    def test_all_data_keys_present(self):
        missing = _REQUIRED_DATA_KEYS - set(self.payload["data"].keys())
        assert not missing, f"Phase 6 contract broken — missing data keys: {missing}"

    # ── data field types (match TypeScript interface) ──────────────────────────

    def test_id_is_string(self):
        assert isinstance(self.payload["data"]["id"], str)

    def test_source_id_is_string(self):
        assert isinstance(self.payload["data"]["source_id"], str)

    def test_domain_is_string(self):
        assert isinstance(self.payload["data"]["domain"], str)

    def test_timestamp_is_iso_string(self):
        ts = self.payload["data"]["timestamp"]
        assert isinstance(ts, str)
        datetime.fromisoformat(ts)  # must parse without raising

    def test_anomaly_score_is_number(self):
        assert isinstance(self.payload["data"]["anomaly_score"], (int, float))

    def test_anomaly_score_in_0_1(self):
        score = self.payload["data"]["anomaly_score"]
        assert 0.0 <= score <= 1.0

    def test_confidence_tier_is_valid_string(self):
        assert self.payload["data"]["confidence_tier"] in _VALID_TIERS

    def test_is_anomaly_is_boolean(self):
        assert isinstance(self.payload["data"]["is_anomaly"], bool)

    def test_raw_label_is_1_or_minus1(self):
        assert self.payload["data"]["raw_label"] in {1, -1}

    def test_latency_ms_is_number(self):
        assert isinstance(self.payload["data"]["latency_ms"], (int, float))

    def test_detected_at_is_iso_string(self):
        ts = self.payload["data"]["detected_at"]
        assert isinstance(ts, str)
        datetime.fromisoformat(ts)

    # ── Semantic invariants ────────────────────────────────────────────────────

    def test_is_anomaly_true_iff_auto_flag(self):
        for tier in _VALID_TIERS:
            update = _make_live_update(tier=tier, score=0.92 if tier == "auto_flag" else 0.5)
            payload = json.loads(update.model_dump_json())
            expected = tier == "auto_flag"
            assert payload["data"]["is_anomaly"] == expected, (
                f"tier={tier!r} → is_anomaly should be {expected}"
            )

    # ── JSON round-trip ────────────────────────────────────────────────────────

    def test_json_is_valid_utf8(self):
        raw = self.update.model_dump_json()
        assert isinstance(raw, str)
        json.loads(raw)

    def test_round_trip_preserves_score(self):
        raw = self.update.model_dump_json()
        restored = LiveUpdate.model_validate_json(raw)
        assert abs(restored.data.anomaly_score - self.update.data.anomaly_score) < 1e-6

    def test_round_trip_preserves_type(self):
        raw = self.update.model_dump_json()
        restored = LiveUpdate.model_validate_json(raw)
        assert restored.type == "anomaly"

    # ── Three-tier coverage ────────────────────────────────────────────────────

    @pytest.mark.parametrize("tier,score", [
        ("auto_flag", 0.92),
        ("soft_alert", 0.72),
        ("log_only", 0.30),
    ])
    def test_all_tiers_produce_valid_payload(self, tier, score):
        update = _make_live_update(tier=tier, score=score)
        payload = json.loads(update.model_dump_json())
        assert payload["data"]["confidence_tier"] == tier
        assert payload["type"] == "anomaly"
