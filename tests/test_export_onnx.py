"""Unit tests for ml/export_onnx.py — ONNX export and onnxruntime inference."""

import json
from pathlib import Path

import numpy as np
import onnxruntime as rt
import pytest
from sklearn.ensemble import IsolationForest

from ml.export_onnx import build_feature_map, export_all, export_to_onnx
from ml.train import (
    generate_training_data,
    get_feature_names,
    save_models,
    train_all,
    train_isolation_forest,
)

# ── Module-scoped fixture: train + export once for the whole test module ───────

@pytest.fixture(scope="module")
def trained_dir(tmp_path_factory) -> Path:
    """Train small models for all domains, export to ONNX, return model_dir."""
    model_dir = tmp_path_factory.mktemp("models")
    models = train_all(n_samples=300, n_estimators=10, contamination=0.05, random_seed=42)
    save_models(models, model_dir)
    export_all(model_dir)
    return model_dir


def _train_small(domain: str) -> tuple[IsolationForest, list[str]]:
    X, names = generate_training_data(domain, n_samples=200, seed=42)
    model = train_isolation_forest(X, n_estimators=10, contamination=0.05, random_seed=42)
    return model, names


# ── export_to_onnx ─────────────────────────────────────────────────────────────

class TestExportToOnnx:
    def test_onnx_file_created(self, tmp_path):
        model, names = _train_small("infra")
        path = export_to_onnx(model, "infra", names, tmp_path)
        assert path.exists()

    def test_onnx_suffix(self, tmp_path):
        model, names = _train_small("iot")
        path = export_to_onnx(model, "iot", names, tmp_path)
        assert path.suffix == ".onnx"

    def test_filename_includes_domain(self, tmp_path):
        for domain in ("infra", "ecommerce", "iot"):
            model, names = _train_small(domain)
            path = export_to_onnx(model, domain, names, tmp_path)
            assert domain in path.name, f"Domain {domain!r} not in filename {path.name!r}"

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_onnx_file_is_non_empty(self, tmp_path, domain):
        model, names = _train_small(domain)
        path = export_to_onnx(model, domain, names, tmp_path)
        assert path.stat().st_size > 0

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_inference_runs_without_error(self, trained_dir, domain):
        onnx_path = trained_dir / f"vigil_anomaly_{domain}.onnx"
        X, _ = generate_training_data(domain, n_samples=10, seed=0)
        sess = rt.InferenceSession(str(onnx_path))
        outputs = sess.run(None, {sess.get_inputs()[0].name: X.astype(np.float32)})
        assert len(outputs) >= 1

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_label_output_values_are_1_or_minus1(self, trained_dir, domain):
        onnx_path = trained_dir / f"vigil_anomaly_{domain}.onnx"
        X, _ = generate_training_data(domain, n_samples=30, seed=1)
        sess = rt.InferenceSession(str(onnx_path))
        outputs = sess.run(None, {sess.get_inputs()[0].name: X.astype(np.float32)})
        labels = np.array(outputs[0]).flatten()
        assert set(labels.tolist()).issubset({-1, 1}), f"Unexpected labels: {set(labels)}"

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_input_shape_matches_n_features(self, trained_dir, domain):
        onnx_path = trained_dir / f"vigil_anomaly_{domain}.onnx"
        sess = rt.InferenceSession(str(onnx_path))
        # shape[1] must equal n_features
        input_shape = sess.get_inputs()[0].shape
        expected_n = len(get_feature_names(domain))
        assert input_shape[1] == expected_n, (
            f"ONNX input dim {input_shape[1]} ≠ feature_map n_features {expected_n}"
        )

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_label_count_equals_batch_size(self, trained_dir, domain):
        onnx_path = trained_dir / f"vigil_anomaly_{domain}.onnx"
        X, _ = generate_training_data(domain, n_samples=7, seed=2)
        sess = rt.InferenceSession(str(onnx_path))
        outputs = sess.run(None, {sess.get_inputs()[0].name: X.astype(np.float32)})
        assert len(np.array(outputs[0]).flatten()) == 7

    def test_input_shape_mismatch_raises(self, trained_dir):
        onnx_path = trained_dir / "vigil_anomaly_infra.onnx"
        expected_n = len(get_feature_names("infra"))
        X_bad = np.zeros((3, expected_n + 5), dtype=np.float32)
        sess = rt.InferenceSession(str(onnx_path))
        with pytest.raises(Exception):
            sess.run(None, {sess.get_inputs()[0].name: X_bad})


# ── build_feature_map ──────────────────────────────────────────────────────────

class TestBuildFeatureMap:
    def test_creates_json_file(self, tmp_path):
        path = build_feature_map({"infra": ["a", "b"]}, tmp_path)
        assert path.exists()
        assert path.name == "feature_map.json"

    def test_valid_json(self, tmp_path):
        path = build_feature_map({"infra": ["x"]}, tmp_path)
        data = json.loads(path.read_text())
        assert isinstance(data, dict)

    def test_contains_all_domains(self, tmp_path):
        path = build_feature_map({"infra": ["a"], "ecommerce": ["b"], "iot": ["c"]}, tmp_path)
        data = json.loads(path.read_text())
        assert set(data["domains"].keys()) == {"infra", "ecommerce", "iot"}

    def test_feature_list_preserved(self, tmp_path):
        features = ["f1", "f2", "f3"]
        path = build_feature_map({"iot": features}, tmp_path)
        data = json.loads(path.read_text())
        assert data["domains"]["iot"]["features"] == features

    def test_n_features_correct(self, tmp_path):
        path = build_feature_map({"infra": ["a", "b", "c", "d"]}, tmp_path)
        data = json.loads(path.read_text())
        assert data["domains"]["infra"]["n_features"] == 4

    def test_model_file_naming(self, tmp_path):
        for domain in ("infra", "ecommerce", "iot"):
            path = build_feature_map({domain: ["x"]}, tmp_path)
            data = json.loads(path.read_text())
            assert data["domains"][domain]["model_file"] == f"vigil_anomaly_{domain}.onnx"

    def test_input_shape_has_correct_n(self, tmp_path):
        path = build_feature_map({"infra": ["a", "b", "c"]}, tmp_path)
        data = json.loads(path.read_text())
        assert data["domains"]["infra"]["input_shape"] == [None, 3]

    def test_input_name_is_float_input(self, tmp_path):
        path = build_feature_map({"infra": ["x"]}, tmp_path)
        data = json.loads(path.read_text())
        assert data["domains"]["infra"]["input_name"] == "float_input"

    def test_input_dtype_is_float32(self, tmp_path):
        path = build_feature_map({"infra": ["x"]}, tmp_path)
        data = json.loads(path.read_text())
        assert data["domains"]["infra"]["input_dtype"] == "float32"

    def test_has_version_field(self, tmp_path):
        path = build_feature_map({"infra": ["x"]}, tmp_path)
        data = json.loads(path.read_text())
        assert "version" in data


# ── export_all ─────────────────────────────────────────────────────────────────

class TestExportAll:
    def test_creates_all_onnx_files(self, trained_dir):
        for domain in ("infra", "ecommerce", "iot"):
            assert (trained_dir / f"vigil_anomaly_{domain}.onnx").exists()

    def test_creates_feature_map_json(self, trained_dir):
        assert (trained_dir / "feature_map.json").exists()

    def test_returns_dict_with_all_domains(self, tmp_path):
        models = train_all(n_samples=150, n_estimators=5)
        save_models(models, tmp_path)
        paths = export_all(tmp_path)
        assert set(paths.keys()) == {"infra", "ecommerce", "iot"}

    def test_returned_paths_exist(self, tmp_path):
        models = train_all(n_samples=150, n_estimators=5)
        save_models(models, tmp_path)
        paths = export_all(tmp_path)
        for domain, path in paths.items():
            assert path.exists(), f"Missing ONNX for {domain}"

    def test_raises_on_missing_pkl(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="isolation_forest"):
            export_all(tmp_path)

    def test_feature_map_matches_get_feature_names(self, trained_dir):
        data = json.loads((trained_dir / "feature_map.json").read_text())
        for domain in ("infra", "ecommerce", "iot"):
            assert data["domains"][domain]["features"] == get_feature_names(domain), (
                f"feature_map features mismatch for {domain}"
            )
