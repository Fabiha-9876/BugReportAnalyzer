"""Orchestrator: upload -> preprocess -> classify -> store."""
import numpy as np
from sqlalchemy.orm import Session

from configs.config import config
from src.db import crud
from src.ingest.parser import parse_upload
from src.ingest.normalizer import normalize_records
from src.ml.preprocessor import preprocess_bug
from src.ml.feature_extractor import FeatureExtractor
from src.ml.duplicate_detector import DuplicateDetector
from src.ml.classifier import BugClassifier
from src.ml.explainer import ClassificationExplainer
from src.ml.active_learner import ActiveLearner


class Pipeline:
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.duplicate_detector = DuplicateDetector()
        self.classifier = BugClassifier()
        self.active_learner = ActiveLearner(self.feature_extractor, self.classifier)
        self._explainer = None

    @property
    def explainer(self):
        if self._explainer is None and self.feature_extractor.is_fitted:
            self._explainer = ClassificationExplainer(
                self.feature_extractor.get_feature_names()
            )
        return self._explainer

    def process_upload(
        self, db: Session, file_source, filename: str,
        project_id: int, cycle_name: str, source_system: str = "auto",
    ) -> dict:
        records, detected_source = parse_upload(file_source, filename, source_system)
        normalized = normalize_records(records)

        cycle = crud.create_cycle(
            db, project_id=project_id, name=cycle_name,
            source_system=detected_source, upload_file_name=filename,
        )

        bugs_data = [{"cycle_id": cycle.id, **rec} for rec in normalized]
        bugs = crud.bulk_create_bugs(db, bugs_data)

        result = {
            "cycle_id": cycle.id,
            "total_bugs": len(bugs),
            "source_system": detected_source,
        }

        if self.feature_extractor.is_fitted and self.classifier.is_trained:
            classify_result = self.classify_cycle(db, cycle.id)
            result.update(classify_result)

        return result

    def classify_cycle(self, db: Session, cycle_id: int) -> dict:
        bugs = crud.get_bugs_for_cycle(db, cycle_id)
        if not bugs:
            return {"classified": 0}

        texts = [preprocess_bug(b.summary, b.description) for b in bugs]
        vectors = self.feature_extractor.transform(texts)

        # Duplicate detection - use summary-only vectors for more precise matching
        summary_texts = [preprocess_bug(b.summary) for b in bugs]
        summary_vectors = self.feature_extractor.transform(summary_texts)

        bug_ids = [b.id for b in bugs]
        duplicates = self.duplicate_detector.find_duplicates(summary_vectors, bug_ids)
        dup_ids = set()
        for dup in duplicates:
            crud.set_duplicate(db, dup["bug_id"], dup["duplicate_of_id"], dup["similarity"])
            dup_ids.add(dup["bug_id"])

            if self.explainer:
                dup_bug = crud.get_bug(db, dup["bug_id"])
                orig_bug = crud.get_bug(db, dup["duplicate_of_id"])
                if dup_bug and orig_bug:
                    explanation = self.explainer.explain_duplicate(
                        dup_bug.summary, orig_bug.summary, dup["similarity"]
                    )
                    dup_bug.ml_explanation = explanation
                    dup_bug.ml_confidence = dup["similarity"]
                    db.commit()

        # Classification for non-duplicates
        non_dup_indices = [i for i, b in enumerate(bugs) if b.id not in dup_ids]
        classified = 0
        low_confidence = 0

        if non_dup_indices:
            non_dup_vectors = vectors[non_dup_indices]
            predictions = self.classifier.predict(non_dup_vectors)

            for idx, pred in zip(non_dup_indices, predictions):
                bug = bugs[idx]
                explanation = ""
                if self.explainer:
                    explanation = self.explainer.explain(
                        vectors[idx], pred["classification"],
                        pred["probabilities"],
                    )

                crud.update_bug_classification(
                    db, bug.id,
                    classification=pred["classification"],
                    confidence=pred["confidence"],
                    explanation=explanation,
                )

                # Store TF-IDF vector
                bug.tfidf_vector_json = vectors[idx].tolist()
                db.commit()

                classified += 1
                if pred["confidence"] < config.ml.confidence_threshold:
                    low_confidence += 1

        return {
            "classified": classified,
            "duplicates_found": len(duplicates),
            "low_confidence": low_confidence,
        }

    def train_initial_model(self, db: Session, labeled_data: list[dict]) -> dict:
        texts = [preprocess_bug(d["summary"], d.get("description", "")) for d in labeled_data]
        labels = np.array([d["label"] for d in labeled_data])

        X = self.feature_extractor.fit_transform(texts)
        metrics = self.classifier.fit(X, labels)
        self._explainer = None  # Reset so it picks up new feature names

        version = "v1"
        avg_f1 = (metrics["svm_f1"] + metrics["lr_f1"]) / 2
        crud.create_model_version(
            db, version=version,
            training_samples=metrics["training_samples"],
            accuracy=avg_f1, f1_score=avg_f1,
            model_path=str(self.classifier.model_path),
        )

        return {"status": "trained", "version": version, "metrics": metrics}

    def retrain_if_needed(self, db: Session) -> dict:
        if self.active_learner.should_retrain(db):
            result = self.active_learner.retrain(db)
            self._explainer = None
            return result
        return {"status": "not_needed"}
