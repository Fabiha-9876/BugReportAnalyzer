"""TF-IDF feature extraction for bug reports."""
from pathlib import Path
from typing import Optional

import numpy as np
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

from configs.config import config


class FeatureExtractor:
    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or config.ml.model_dir / "tfidf_vectorizer.joblib"
        self.vectorizer: Optional[TfidfVectorizer] = None
        self._load()

    def _load(self):
        if self.model_path.exists():
            self.vectorizer = joblib.load(self.model_path)

    def fit(self, texts: list[str]) -> "FeatureExtractor":
        self.vectorizer = TfidfVectorizer(
            max_features=config.ml.tfidf_max_features,
            ngram_range=config.ml.tfidf_ngram_range,
            sublinear_tf=True,
            strip_accents="unicode",
        )
        self.vectorizer.fit(texts)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.vectorizer, self.model_path)
        return self

    def transform(self, texts: list[str]) -> np.ndarray:
        if self.vectorizer is None:
            raise RuntimeError("Vectorizer not fitted. Call fit() first.")
        return self.vectorizer.transform(texts).toarray()

    def fit_transform(self, texts: list[str]) -> np.ndarray:
        self.fit(texts)
        return self.vectorizer.transform(texts).toarray()

    @property
    def is_fitted(self) -> bool:
        return self.vectorizer is not None

    def get_feature_names(self) -> list[str]:
        if self.vectorizer is None:
            return []
        return list(self.vectorizer.get_feature_names_out())
