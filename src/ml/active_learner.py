"""Active learning: retrain model when enough human overrides accumulate."""
import numpy as np
from sqlalchemy.orm import Session

from configs.config import config
from src.db import crud
from src.ml.preprocessor import preprocess_bug
from src.ml.feature_extractor import FeatureExtractor
from src.ml.classifier import BugClassifier


class ActiveLearner:
    def __init__(
        self,
        feature_extractor: FeatureExtractor,
        classifier: BugClassifier,
        retrain_threshold: int | None = None,
    ):
        self.feature_extractor = feature_extractor
        self.classifier = classifier
        self.retrain_threshold = retrain_threshold or config.ml.retrain_override_count

    def should_retrain(self, db: Session) -> bool:
        active_model = crud.get_active_model(db)
        since = active_model.trained_at if active_model else None
        override_count = crud.count_human_overrides(db, since=since)
        return override_count >= self.retrain_threshold

    def retrain(self, db: Session) -> dict:
        reviewed_bugs = crud.get_reviewed_bugs(db)

        if len(reviewed_bugs) < 10:
            return {"status": "skipped", "reason": "Not enough reviewed samples (need >= 10)"}

        texts = [preprocess_bug(b.summary, b.description) for b in reviewed_bugs]
        labels = np.array([b.final_classification for b in reviewed_bugs])

        unique_labels = set(labels)
        if len(unique_labels) < 2:
            return {"status": "skipped", "reason": "Need at least 2 distinct labels"}

        X = self.feature_extractor.fit_transform(texts)
        metrics = self.classifier.fit(X, labels)

        version = f"v{len(db.query(crud.ModelVersion).all()) + 1}"
        avg_f1 = (metrics["svm_f1"] + metrics["lr_f1"]) / 2
        crud.create_model_version(
            db,
            version=version,
            training_samples=metrics["training_samples"],
            accuracy=avg_f1,
            f1_score=avg_f1,
            model_path=str(self.classifier.model_path),
        )

        return {
            "status": "retrained",
            "version": version,
            "metrics": metrics,
        }
