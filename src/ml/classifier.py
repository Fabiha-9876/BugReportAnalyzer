"""SVM + Logistic Regression ensemble classifier for bug validity."""
from pathlib import Path
from typing import Optional

import numpy as np
import joblib
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import cross_val_score

from configs.config import config


class BugClassifier:
    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or config.ml.model_dir / "classifier.joblib"
        self.svm: Optional[CalibratedClassifierCV] = None
        self.lr: Optional[LogisticRegression] = None
        self.classes_: Optional[np.ndarray] = None
        self._load()

    def _load(self):
        if self.model_path.exists():
            data = joblib.load(self.model_path)
            self.svm = data["svm"]
            self.lr = data["lr"]
            self.classes_ = data["classes"]

    def _save(self):
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "svm": self.svm,
            "lr": self.lr,
            "classes": self.classes_,
        }, self.model_path)

    def fit(self, X: np.ndarray, y: np.ndarray) -> dict:
        raw_svm = LinearSVC(max_iter=5000, class_weight="balanced")
        self.svm = CalibratedClassifierCV(raw_svm, cv=min(3, len(set(y))))
        self.svm.fit(X, y)

        self.lr = LogisticRegression(
            max_iter=1000, class_weight="balanced",
        )
        self.lr.fit(X, y)

        self.classes_ = np.unique(y)
        self._save()

        # Evaluate
        n_splits = min(5, min(np.bincount(np.searchsorted(self.classes_, y))))
        n_splits = max(2, n_splits)
        svm_scores = cross_val_score(
            CalibratedClassifierCV(LinearSVC(max_iter=5000, class_weight="balanced"), cv=min(3, len(set(y)))),
            X, y, cv=n_splits, scoring="f1_weighted",
        )
        lr_scores = cross_val_score(self.lr, X, y, cv=n_splits, scoring="f1_weighted")

        return {
            "svm_f1": float(np.mean(svm_scores)),
            "lr_f1": float(np.mean(lr_scores)),
            "training_samples": len(y),
        }

    def predict(self, X: np.ndarray) -> list[dict]:
        if self.svm is None or self.lr is None:
            raise RuntimeError("Classifier not trained. Call fit() first.")

        svm_proba = self.svm.predict_proba(X)
        lr_proba = self.lr.predict_proba(X)

        # Ensemble: average probabilities
        ensemble_proba = (svm_proba + lr_proba) / 2.0

        results = []
        for i in range(len(X)):
            pred_idx = np.argmax(ensemble_proba[i])
            label = str(self.classes_[pred_idx])
            confidence = float(ensemble_proba[i][pred_idx])
            results.append({
                "classification": label,
                "confidence": confidence,
                "probabilities": {
                    str(self.classes_[j]): float(ensemble_proba[i][j])
                    for j in range(len(self.classes_))
                },
            })
        return results

    def predict_single(self, x: np.ndarray) -> dict:
        return self.predict(x.reshape(1, -1))[0]

    @property
    def is_trained(self) -> bool:
        return self.svm is not None and self.lr is not None
