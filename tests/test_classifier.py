"""Tests for the SVM + LR ensemble classifier."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pytest
from src.ml.classifier import BugClassifier
from src.ml.feature_extractor import FeatureExtractor
from src.ml.preprocessor import preprocess_bug


class TestClassifier:
    def _get_training_data(self, tmp_path):
        extractor = FeatureExtractor(model_path=tmp_path / "tfidf.joblib")
        texts = [
            # Valid bugs
            preprocess_bug("Login fails with valid credentials on Firefox"),
            preprocess_bug("Payment processing timeout after 30 seconds"),
            preprocess_bug("Dashboard charts not rendering for large datasets"),
            preprocess_bug("Report export produces empty CSV file"),
            preprocess_bug("Search returns no results for exact match"),
            preprocess_bug("File upload fails silently for large files"),
            preprocess_bug("API rate limiting not enforced for users"),
            preprocess_bug("Password reset token expires prematurely"),
            preprocess_bug("CSRF token validation fails after refresh"),
            preprocess_bug("Bulk import skips rows with special characters"),
            # Invalid bugs
            preprocess_bug("The button color should be darker blue"),
            preprocess_bug("I think the font size is too small"),
            preprocess_bug("Application is slow on my old laptop"),
            preprocess_bug("Would be nice to have keyboard shortcuts"),
            preprocess_bug("The loading spinner is not centered"),
            preprocess_bug("Cannot reproduce after clearing cache"),
            preprocess_bug("Feature request add bulk delete option"),
            preprocess_bug("The error message could be friendlier"),
            preprocess_bug("UI looks different than old mockup"),
            preprocess_bug("Need more sorting options in table"),
        ]
        labels = np.array(["valid"] * 10 + ["invalid"] * 10)
        X = extractor.fit_transform(texts)
        return X, labels, extractor

    def test_fit_and_predict(self, tmp_path):
        X, labels, _ = self._get_training_data(tmp_path)
        classifier = BugClassifier(model_path=tmp_path / "clf.joblib")
        metrics = classifier.fit(X, labels)
        assert "svm_f1" in metrics
        assert "lr_f1" in metrics
        assert classifier.is_trained

        preds = classifier.predict(X[:3])
        assert len(preds) == 3
        for p in preds:
            assert "classification" in p
            assert "confidence" in p
            assert p["classification"] in ("valid", "invalid")

    def test_predict_single(self, tmp_path):
        X, labels, _ = self._get_training_data(tmp_path)
        classifier = BugClassifier(model_path=tmp_path / "clf.joblib")
        classifier.fit(X, labels)
        pred = classifier.predict_single(X[0])
        assert pred["classification"] in ("valid", "invalid")
        assert 0 <= pred["confidence"] <= 1

    def test_predict_without_training(self, tmp_path):
        classifier = BugClassifier(model_path=tmp_path / "nonexistent.joblib")
        with pytest.raises(RuntimeError):
            classifier.predict(np.array([[1.0, 0.0]]))

    def test_persistence(self, tmp_path):
        X, labels, _ = self._get_training_data(tmp_path)
        model_path = tmp_path / "clf.joblib"
        clf1 = BugClassifier(model_path=model_path)
        clf1.fit(X, labels)
        pred1 = clf1.predict(X[:2])

        clf2 = BugClassifier(model_path=model_path)
        pred2 = clf2.predict(X[:2])
        assert pred1[0]["classification"] == pred2[0]["classification"]
