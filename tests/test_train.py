"""Unit tests for ml/train.py — data generation and model fitting."""

import numpy as np
import pytest
from sklearn.ensemble import IsolationForest

from ml.train import (
    _parse_max_samples,
    generate_training_data,
    get_feature_names,
    save_models,
    train_all,
    train_isolation_forest,
)

# ── _parse_max_samples ─────────────────────────────────────────────────────────

class TestParseMaxSamples:
    def test_auto_string(self):
        assert _parse_max_samples("auto") == "auto"

    def test_auto_uppercase(self):
        assert _parse_max_samples("AUTO") == "auto"

    def test_fraction(self):
        assert _parse_max_samples("0.7") == pytest.approx(0.7)

    def test_integer_string(self):
        assert _parse_max_samples("256") == 256
        assert isinstance(_parse_max_samples("256"), int)

    def test_float_above_1_becomes_int(self):
        assert _parse_max_samples("256.0") == 256

    def test_invalid_falls_back_to_auto(self):
        assert _parse_max_samples("not-a-number") == "auto"


# ── get_feature_names ──────────────────────────────────────────────────────────

class TestGetFeatureNames:
    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_returns_sorted_list(self, domain):
        names = get_feature_names(domain)
        assert names == sorted(names), f"Feature names for {domain} are not sorted"

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_returns_non_empty_list(self, domain):
        assert len(get_feature_names(domain)) > 0

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_all_strings(self, domain):
        for name in get_feature_names(domain):
            assert isinstance(name, str)

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_consistent_across_calls(self, domain):
        assert get_feature_names(domain) == get_feature_names(domain)

    def test_domains_have_different_features(self):
        infra = set(get_feature_names("infra"))
        ecom = set(get_feature_names("ecommerce"))
        iot = set(get_feature_names("iot"))
        assert infra != ecom
        assert infra != iot
        assert ecom != iot


# ── generate_training_data ─────────────────────────────────────────────────────

class TestGenerateTrainingData:
    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_output_shape(self, domain):
        X, names = generate_training_data(domain, n_samples=50, seed=0)
        assert X.shape == (50, len(names))

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_dtype_is_float32(self, domain):
        X, _ = generate_training_data(domain, n_samples=20, seed=0)
        assert X.dtype == np.float32

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_feature_names_match_get_feature_names(self, domain):
        _, names = generate_training_data(domain, n_samples=10, seed=0)
        assert names == get_feature_names(domain)

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_no_nan_or_inf(self, domain):
        X, _ = generate_training_data(domain, n_samples=100, seed=1)
        assert not np.any(np.isnan(X)), "NaN values in training data"
        assert not np.any(np.isinf(X)), "Inf values in training data"

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_shape_for_large_sample(self, domain):
        X, names = generate_training_data(domain, n_samples=500, seed=7)
        assert X.shape[0] == 500
        assert X.shape[1] == len(get_feature_names(domain))


# ── train_isolation_forest ─────────────────────────────────────────────────────

class TestTrainIsolationForest:
    @pytest.fixture
    def small_X(self):
        X, _ = generate_training_data("infra", n_samples=200, seed=42)
        return X

    def test_returns_isolation_forest(self, small_X):
        model = train_isolation_forest(small_X, n_estimators=10)
        assert isinstance(model, IsolationForest)

    def test_correct_n_estimators(self, small_X):
        model = train_isolation_forest(small_X, n_estimators=17, contamination=0.05)
        assert model.n_estimators == 17

    def test_contamination_stored(self, small_X):
        model = train_isolation_forest(small_X, n_estimators=10, contamination=0.08)
        assert model.contamination == pytest.approx(0.08)

    def test_model_is_fitted_predict_works(self, small_X):
        model = train_isolation_forest(small_X, n_estimators=10)
        preds = model.predict(small_X[:5])
        assert set(preds.tolist()).issubset({-1, 1})

    def test_contamination_respected_on_training_data(self, small_X):
        # IsolationForest guarantees that exactly contamination fraction of
        # training samples are classified as anomalies when predicting on train set.
        model = train_isolation_forest(
            small_X, n_estimators=50, contamination=0.10, random_seed=42
        )
        preds = model.predict(small_X)
        anomaly_rate = (preds == -1).mean()
        assert anomaly_rate == pytest.approx(0.10, abs=0.01)

    def test_max_samples_auto(self, small_X):
        model = train_isolation_forest(small_X, n_estimators=5, max_samples="auto")
        assert model is not None

    def test_decision_function_returns_scores(self, small_X):
        model = train_isolation_forest(small_X, n_estimators=10)
        scores = model.decision_function(small_X[:10])
        assert scores.shape == (10,)
        assert scores.dtype in (np.float32, np.float64)

    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_fits_all_domains(self, domain):
        X, _ = generate_training_data(domain, n_samples=150, seed=0)
        model = train_isolation_forest(X, n_estimators=5)
        assert isinstance(model, IsolationForest)
        assert model.predict(X[:3]).shape == (3,)


# ── train_all ──────────────────────────────────────────────────────────────────

class TestTrainAll:
    def test_returns_all_three_domains(self):
        models = train_all(n_samples=100, n_estimators=5, contamination=0.05, random_seed=0)
        assert set(models.keys()) == {"infra", "ecommerce", "iot"}

    def test_each_value_is_model_and_features(self):
        models = train_all(n_samples=100, n_estimators=5, contamination=0.05)
        for domain, (model, features) in models.items():
            assert isinstance(model, IsolationForest), f"domain {domain}: model wrong type"
            assert isinstance(features, list), f"domain {domain}: features wrong type"
            assert len(features) > 0, f"domain {domain}: empty feature list"

    def test_feature_names_match_get_feature_names(self):
        models = train_all(n_samples=80, n_estimators=5)
        for domain, (_, features) in models.items():
            assert features == get_feature_names(domain), f"Feature mismatch for {domain}"


# ── save_models ────────────────────────────────────────────────────────────────

class TestSaveModels:
    def test_pkl_files_created(self, tmp_path):
        models = train_all(n_samples=80, n_estimators=5)
        save_models(models, tmp_path)
        for domain in ["infra", "ecommerce", "iot"]:
            assert (tmp_path / f"isolation_forest_{domain}.pkl").exists()

    def test_pkl_is_loadable(self, tmp_path):
        import pickle

        models = train_all(n_samples=80, n_estimators=5)
        save_models(models, tmp_path)

        for domain in ["infra", "ecommerce", "iot"]:
            with open(tmp_path / f"isolation_forest_{domain}.pkl", "rb") as f:
                loaded = pickle.load(f)
            assert isinstance(loaded, IsolationForest)
            assert loaded.n_estimators == models[domain][0].n_estimators
