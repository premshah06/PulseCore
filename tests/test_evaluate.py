"""Unit tests for ml/evaluate.py — anomaly injection, inference, metrics."""

from pathlib import Path

import numpy as np
import pytest
from sklearn.metrics import f1_score, precision_score, recall_score

from ml.evaluate import evaluate_domain, inject_anomalies, run_inference
from ml.export_onnx import export_all
from ml.train import generate_training_data, save_models, train_all

# ── Module-scoped fixture: models ready for evaluation ────────────────────────

@pytest.fixture(scope="module")
def model_dir(tmp_path_factory) -> Path:
    d = tmp_path_factory.mktemp("eval_models")
    models = train_all(n_samples=400, n_estimators=15, contamination=0.05, random_seed=42)
    save_models(models, d)
    export_all(d)
    return d


# ── inject_anomalies ───────────────────────────────────────────────────────────

class TestInjectAnomalies:
    def test_total_length_is_normal_plus_anomaly(self):
        X_n = np.ones((100, 5), dtype=np.float32)
        X, y = inject_anomalies(X_n, anomaly_rate=0.20, seed=0)
        assert len(X) == len(y)
        assert len(y) == 100 + 20

    def test_anomaly_count(self):
        X_n = np.ones((100, 5), dtype=np.float32)
        X, y = inject_anomalies(X_n, anomaly_rate=0.20, seed=0)
        assert int((y == -1).sum()) == 20

    def test_normal_count_equals_input_size(self):
        X_n = np.ones((80, 4), dtype=np.float32)
        X, y = inject_anomalies(X_n, anomaly_rate=0.25, seed=7)
        assert int((y == 1).sum()) == 80

    def test_labels_are_only_1_or_minus1(self):
        X_n = np.random.rand(50, 3).astype(np.float32)
        X, y = inject_anomalies(X_n, anomaly_rate=0.10, seed=1)
        assert set(y.tolist()).issubset({-1, 1})

    def test_output_dtype_float32(self):
        X_n = np.ones((40, 4), dtype=np.float32)
        X, _ = inject_anomalies(X_n, anomaly_rate=0.10, seed=0)
        assert X.dtype == np.float32

    def test_label_dtype_int64(self):
        X_n = np.ones((40, 4), dtype=np.float32)
        _, y = inject_anomalies(X_n, anomaly_rate=0.10, seed=0)
        assert y.dtype == np.int64

    def test_shuffled_output(self):
        # After shuffling, the last element should not always be -1
        X_n = np.ones((100, 5), dtype=np.float32)
        _, y = inject_anomalies(X_n, anomaly_rate=0.10, seed=3)
        # With shuffling, labels should not be all 1s then all -1s
        assert not np.all(y[:90] == 1) or not np.all(y[90:] == -1)

    def test_anomalous_values_differ_from_normal(self):
        X_n = np.ones((50, 5), dtype=np.float32) * 2.0
        X, y = inject_anomalies(X_n, anomaly_rate=0.5, seed=99)
        X_anomaly = X[y == -1]
        # At least one feature should be larger than 10 (2.0 * 15 = 30 minimum)
        assert X_anomaly.max() > 10.0, "Anomaly injection did not produce extreme values"

    def test_minimum_one_anomaly(self):
        X_n = np.ones((5, 3), dtype=np.float32)
        X, y = inject_anomalies(X_n, anomaly_rate=0.01, seed=0)
        assert (y == -1).sum() >= 1


# ── run_inference ──────────────────────────────────────────────────────────────

class TestRunInference:
    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_returns_int64_array(self, model_dir, domain):
        X, _ = generate_training_data(domain, n_samples=10, seed=0)
        onnx_path = model_dir / f"pulsecore_anomaly_{domain}.onnx"
        labels = run_inference(onnx_path, X)
        assert labels.dtype == np.int64

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_labels_are_1_or_minus1(self, model_dir, domain):
        X, _ = generate_training_data(domain, n_samples=20, seed=2)
        onnx_path = model_dir / f"pulsecore_anomaly_{domain}.onnx"
        labels = run_inference(onnx_path, X)
        assert set(labels.tolist()).issubset({-1, 1})

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_output_length_equals_input_rows(self, model_dir, domain):
        X, _ = generate_training_data(domain, n_samples=13, seed=3)
        onnx_path = model_dir / f"pulsecore_anomaly_{domain}.onnx"
        labels = run_inference(onnx_path, X)
        assert len(labels) == 13


# ── evaluate_domain ────────────────────────────────────────────────────────────

class TestEvaluateDomain:
    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_returns_dict(self, model_dir, domain):
        result = evaluate_domain(domain, model_dir, n_holdout=200, anomaly_rate=0.20, seed=99)
        assert isinstance(result, dict)

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_required_keys_present(self, model_dir, domain):
        result = evaluate_domain(domain, model_dir, n_holdout=200, anomaly_rate=0.20, seed=99)
        for key in ("domain", "n_samples", "n_true_anomaly", "n_pred_anomaly",
                    "precision", "recall", "f1"):
            assert key in result, f"Missing key {key!r} for domain {domain}"

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_domain_field_matches(self, model_dir, domain):
        result = evaluate_domain(domain, model_dir, n_holdout=150, anomaly_rate=0.15, seed=5)
        assert result["domain"] == domain

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_metrics_in_0_1_range(self, model_dir, domain):
        result = evaluate_domain(domain, model_dir, n_holdout=200, anomaly_rate=0.20, seed=99)
        for metric in ("precision", "recall", "f1"):
            val = result[metric]
            assert 0.0 <= val <= 1.0, f"{domain}.{metric}={val} out of [0,1]"

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_report_covers_all_domains(self, model_dir, domain):
        result = evaluate_domain(domain, model_dir, n_holdout=100, anomaly_rate=0.15, seed=7)
        assert result["domain"] in {"infra", "ecommerce", "iot"}

    def test_raises_on_missing_onnx(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            evaluate_domain("infra", tmp_path, n_holdout=100, anomaly_rate=0.1, seed=0)

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_n_true_anomaly_matches_injection_rate(self, model_dir, domain):
        n_holdout = 200
        anomaly_rate = 0.20
        result = evaluate_domain(domain, model_dir, n_holdout=n_holdout,
                                 anomaly_rate=anomaly_rate, seed=99)
        expected_anomalies = int(n_holdout * anomaly_rate)
        assert result["n_true_anomaly"] == expected_anomalies


# ── Precision/recall arithmetic against a ground-truth case ───────────────────

class TestMetricArithmetic:
    """Verify precision/recall/F1 arithmetic matches sklearn directly."""

    def test_perfect_classifier(self):
        y_true = np.array([1, 1, 1, -1, -1])
        y_pred = np.array([1, 1, 1, -1, -1])
        assert precision_score(y_true, y_pred, pos_label=-1) == pytest.approx(1.0)
        assert recall_score(y_true, y_pred, pos_label=-1) == pytest.approx(1.0)
        assert f1_score(y_true, y_pred, pos_label=-1) == pytest.approx(1.0)

    def test_one_tp_one_fn_no_fp(self):
        # 2 anomalies: correctly catches 1, misses 1, no false positives
        y_true = np.array([1, 1, 1, 1, 1, 1, 1, 1, -1, -1])
        y_pred = np.array([1, 1, 1, 1, 1, 1, 1, 1, -1, 1])
        p = precision_score(y_true, y_pred, pos_label=-1, zero_division=0)
        r = recall_score(y_true, y_pred, pos_label=-1, zero_division=0)
        f1 = f1_score(y_true, y_pred, pos_label=-1, zero_division=0)
        assert p == pytest.approx(1.0)
        assert r == pytest.approx(0.5)
        assert f1 == pytest.approx(2 / 3)

    def test_all_predicted_normal(self):
        y_true = np.array([1, 1, -1, -1])
        y_pred = np.array([1, 1, 1, 1])
        p = precision_score(y_true, y_pred, pos_label=-1, zero_division=0)
        r = recall_score(y_true, y_pred, pos_label=-1, zero_division=0)
        assert p == 0.0
        assert r == 0.0
