"""Integration tests for the FastAPI inference sidecar."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

import inference.main as _main_module
from inference.main import app
from inference.schemas import AnomalyResult
from ml.train import get_feature_names

# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def model_dir(tmp_path_factory):
    from ml.export_onnx import export_all
    from ml.train import save_models, train_all

    d = tmp_path_factory.mktemp("api_models")
    models = train_all(n_samples=300, n_estimators=10, contamination=0.05, random_seed=0)
    save_models(models, d)
    export_all(d)
    return d


@pytest.fixture
def client(model_dir, monkeypatch):
    """TestClient that lets lifespan run normally against a real model."""
    monkeypatch.setenv("ONNX_MODEL_PATH", str(model_dir / "pulsecore_anomaly_infra.onnx"))
    monkeypatch.setenv("FEATURE_MAP_PATH", str(model_dir / "feature_map.json"))
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture
def client_no_model(model_dir, monkeypatch):
    """TestClient where predictor is cleared after startup — simulates missing model."""
    monkeypatch.setenv("ONNX_MODEL_PATH", str(model_dir / "pulsecore_anomaly_infra.onnx"))
    monkeypatch.setenv("FEATURE_MAP_PATH", str(model_dir / "feature_map.json"))
    with TestClient(app, raise_server_exceptions=True) as c:
        _main_module._predictor = None  # clear after successful startup
        yield c


def _infra_payload(**overrides) -> dict:
    feature_names = get_feature_names("infra")
    base = {
        "source_id": "test-host-001",
        "domain": "infra",
        "metrics": {f: 50.0 for f in feature_names},
        "timestamp": datetime.now(UTC).isoformat(),
    }
    base.update(overrides)
    return base


# ── GET /health ────────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_status_is_ok(self, client):
        assert resp.json()["status"] == "ok" if (resp := client.get("/health")) else True
        resp = client.get("/health")
        assert resp.json()["status"] == "ok"

    def test_model_loaded_is_true(self, client):
        resp = client.get("/health")
        assert resp.json()["model_loaded"] is True

    def test_domain_is_infra(self, client):
        resp = client.get("/health")
        assert resp.json()["domain"] == "infra"

    def test_model_loaded_false_when_no_predictor(self, client_no_model):
        resp = client_no_model.get("/health")
        assert resp.status_code == 200
        assert resp.json()["model_loaded"] is False


# ── POST /predict — happy path ─────────────────────────────────────────────────

class TestPredictHappyPath:
    def test_returns_200(self, client):
        resp = client.post("/predict", json=_infra_payload())
        assert resp.status_code == 200

    def test_response_is_valid_json(self, client):
        resp = client.post("/predict", json=_infra_payload())
        data = resp.json()
        assert isinstance(data, dict)

    def test_response_has_all_required_fields(self, client):
        resp = client.post("/predict", json=_infra_payload())
        data = resp.json()
        for field in (
            "source_id", "domain", "timestamp", "anomaly_score",
            "confidence_tier", "is_anomaly", "raw_label", "latency_ms",
        ):
            assert field in data, f"Missing field: {field!r}"

    def test_source_id_echoed(self, client):
        resp = client.post("/predict", json=_infra_payload(source_id="my-node"))
        assert resp.json()["source_id"] == "my-node"

    def test_domain_echoed(self, client):
        resp = client.post("/predict", json=_infra_payload())
        assert resp.json()["domain"] == "infra"

    def test_anomaly_score_in_0_1(self, client):
        resp = client.post("/predict", json=_infra_payload())
        score = resp.json()["anomaly_score"]
        assert 0.0 <= score <= 1.0

    def test_confidence_tier_is_valid(self, client):
        resp = client.post("/predict", json=_infra_payload())
        assert resp.json()["confidence_tier"] in {"auto_flag", "soft_alert", "log_only"}

    def test_is_anomaly_is_bool(self, client):
        resp = client.post("/predict", json=_infra_payload())
        assert isinstance(resp.json()["is_anomaly"], bool)

    def test_raw_label_is_1_or_minus1(self, client):
        resp = client.post("/predict", json=_infra_payload())
        assert resp.json()["raw_label"] in {1, -1}

    def test_latency_ms_is_positive(self, client):
        resp = client.post("/predict", json=_infra_payload())
        assert resp.json()["latency_ms"] > 0

    def test_is_anomaly_consistent_with_tier(self, client):
        resp = client.post("/predict", json=_infra_payload())
        data = resp.json()
        expected = data["confidence_tier"] == "auto_flag"
        assert data["is_anomaly"] == expected

    def test_pydantic_validates_response_shape(self, client):
        resp = client.post("/predict", json=_infra_payload())
        # Will raise ValidationError if shape doesn't match AnomalyResult
        result = AnomalyResult.model_validate(resp.json())
        assert isinstance(result, AnomalyResult)


# ── POST /predict — 422 cases ──────────────────────────────────────────────────

class TestPredictValidationErrors:
    def test_missing_source_id_returns_422(self, client):
        payload = _infra_payload()
        del payload["source_id"]
        resp = client.post("/predict", json=payload)
        assert resp.status_code == 422

    def test_missing_domain_returns_422(self, client):
        payload = _infra_payload()
        del payload["domain"]
        resp = client.post("/predict", json=payload)
        assert resp.status_code == 422

    def test_missing_metrics_returns_422(self, client):
        payload = _infra_payload()
        del payload["metrics"]
        resp = client.post("/predict", json=payload)
        assert resp.status_code == 422

    def test_missing_timestamp_returns_422(self, client):
        payload = _infra_payload()
        del payload["timestamp"]
        resp = client.post("/predict", json=payload)
        assert resp.status_code == 422

    def test_invalid_domain_returns_422(self, client):
        payload = _infra_payload(domain="blockchain")
        resp = client.post("/predict", json=payload)
        assert resp.status_code == 422

    def test_missing_metric_feature_returns_422(self, client):
        payload = _infra_payload()
        payload["metrics"] = {"cpu_user_pct": 50.0}  # only one feature
        resp = client.post("/predict", json=payload)
        assert resp.status_code == 422

    def test_empty_body_returns_422(self, client):
        resp = client.post("/predict", content=b"")
        assert resp.status_code == 422

    def test_empty_source_id_returns_422(self, client):
        payload = _infra_payload(source_id="")
        resp = client.post("/predict", json=payload)
        assert resp.status_code == 422


# ── 503 when no model loaded ───────────────────────────────────────────────────

class TestPredictNoModel:
    def test_returns_503(self, client_no_model):
        resp = client_no_model.post("/predict", json=_infra_payload())
        assert resp.status_code == 503
