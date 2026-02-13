"""Tests for active learner."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from src.ml.active_learner import ActiveLearner
from src.ml.feature_extractor import FeatureExtractor
from src.ml.classifier import BugClassifier
from src.db import crud


class TestActiveLearner:
    def test_should_retrain_false(self, db_session):
        extractor = FeatureExtractor.__new__(FeatureExtractor)
        extractor.vectorizer = None
        classifier = BugClassifier.__new__(BugClassifier)
        classifier.svm = None
        classifier.lr = None
        learner = ActiveLearner(extractor, classifier, retrain_threshold=50)
        assert learner.should_retrain(db_session) is False

    def test_should_retrain_true(self, db_session, sample_bugs):
        extractor = FeatureExtractor.__new__(FeatureExtractor)
        extractor.vectorizer = None
        classifier = BugClassifier.__new__(BugClassifier)
        classifier.svm = None
        classifier.lr = None
        learner = ActiveLearner(extractor, classifier, retrain_threshold=2)

        # Create overrides
        for bug in sample_bugs[:3]:
            bug.ml_classification = "invalid"
            bug.final_classification = "invalid"
            db_session.commit()
            crud.override_bug_classification(db_session, bug.id, "valid", "reviewer", "test")

        assert learner.should_retrain(db_session) is True

    def test_retrain_not_enough_samples(self, db_session):
        extractor = FeatureExtractor.__new__(FeatureExtractor)
        extractor.vectorizer = None
        classifier = BugClassifier.__new__(BugClassifier)
        classifier.svm = None
        classifier.lr = None
        learner = ActiveLearner(extractor, classifier)
        result = learner.retrain(db_session)
        assert result["status"] == "skipped"
