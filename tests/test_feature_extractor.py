"""Tests for TF-IDF feature extractor."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.ml.feature_extractor import FeatureExtractor


class TestFeatureExtractor:
    def test_fit_and_transform(self, tmp_path):
        extractor = FeatureExtractor(model_path=tmp_path / "test_tfidf.joblib")
        texts = [
            "login fails with valid credentials",
            "payment processing timeout error",
            "button color should be darker blue",
            "dashboard charts not rendering properly",
            "search returns no results for query",
        ]
        X = extractor.fit_transform(texts)
        assert X.shape[0] == 5
        assert X.shape[1] <= 250
        assert extractor.is_fitted

    def test_transform_without_fit(self, tmp_path):
        extractor = FeatureExtractor(model_path=tmp_path / "nonexistent.joblib")
        with pytest.raises(RuntimeError):
            extractor.transform(["test text"])

    def test_persistence(self, tmp_path):
        model_path = tmp_path / "tfidf.joblib"
        extractor1 = FeatureExtractor(model_path=model_path)
        texts = ["login failure", "payment error", "color issue"]
        X1 = extractor1.fit_transform(texts)

        extractor2 = FeatureExtractor(model_path=model_path)
        X2 = extractor2.transform(texts)
        assert X1.shape == X2.shape

    def test_feature_names(self, tmp_path):
        extractor = FeatureExtractor(model_path=tmp_path / "tfidf.joblib")
        texts = ["login failure", "payment error"]
        extractor.fit_transform(texts)
        names = extractor.get_feature_names()
        assert len(names) > 0
        assert all(isinstance(n, str) for n in names)
