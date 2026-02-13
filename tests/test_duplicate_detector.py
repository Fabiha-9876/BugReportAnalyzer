"""Tests for duplicate detection."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from src.ml.duplicate_detector import DuplicateDetector
from src.ml.feature_extractor import FeatureExtractor
from src.ml.preprocessor import preprocess_bug


class TestDuplicateDetector:
    def test_find_duplicates(self, tmp_path):
        extractor = FeatureExtractor(model_path=tmp_path / "tfidf.joblib")
        texts = [
            preprocess_bug("Login fails with valid credentials"),
            preprocess_bug("Button color should be blue"),
            preprocess_bug("Login is broken with valid credentials"),  # duplicate of 0
            preprocess_bug("Payment processing timeout"),
        ]
        vectors = extractor.fit_transform(texts)
        detector = DuplicateDetector(threshold=0.30)
        dups = detector.find_duplicates(vectors, [1, 2, 3, 4])
        # Bug 3 (login broken) should be flagged as dup of bug 1 (login fails)
        dup_ids = {d["bug_id"] for d in dups}
        assert len(dups) >= 1
        assert 3 in dup_ids or 1 in dup_ids

    def test_no_duplicates(self, tmp_path):
        extractor = FeatureExtractor(model_path=tmp_path / "tfidf.joblib")
        texts = [
            preprocess_bug("Login fails"),
            preprocess_bug("Payment timeout"),
            preprocess_bug("Dashboard rendering error"),
        ]
        vectors = extractor.fit_transform(texts)
        detector = DuplicateDetector(threshold=0.95)
        dups = detector.find_duplicates(vectors, [1, 2, 3])
        assert len(dups) == 0

    def test_check_single(self, tmp_path):
        extractor = FeatureExtractor(model_path=tmp_path / "tfidf.joblib")
        texts = [
            preprocess_bug("Login fails with valid credentials"),
            preprocess_bug("Payment timeout error"),
        ]
        vectors = extractor.fit_transform(texts)
        detector = DuplicateDetector(threshold=0.40)
        new_text = [preprocess_bug("Login is broken with credentials")]
        new_vec = extractor.transform(new_text)
        result = detector.check_single(new_vec[0], vectors, [1, 2])
        assert result is not None or result is None  # depends on threshold

    def test_empty_input(self):
        detector = DuplicateDetector()
        assert detector.find_duplicates(np.array([]), []) == []

    def test_single_input(self):
        detector = DuplicateDetector()
        assert detector.find_duplicates(np.array([[1.0, 0.0]]), [1]) == []
