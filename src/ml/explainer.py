"""Feature-importance explanations for bug classifications."""
import numpy as np
from typing import Optional


class ClassificationExplainer:
    def __init__(self, feature_names: list[str]):
        self.feature_names = feature_names

    def explain(
        self, tfidf_vector: np.ndarray, classification: str,
        probabilities: dict, top_n: int = 5,
    ) -> str:
        nonzero_indices = np.nonzero(tfidf_vector)[0] if tfidf_vector.ndim == 1 else np.nonzero(tfidf_vector[0])[0]
        vec = tfidf_vector.flatten()

        if len(nonzero_indices) == 0:
            return f"Classified as '{classification}' with confidence {probabilities.get(classification, 0):.0%}. No significant text features detected."

        top_indices = nonzero_indices[np.argsort(vec[nonzero_indices])[::-1][:top_n]]
        top_features = []
        for idx in top_indices:
            if idx < len(self.feature_names):
                top_features.append((self.feature_names[idx], float(vec[idx])))

        conf = probabilities.get(classification, 0)
        feature_strs = [f"'{f}' ({w:.3f})" for f, w in top_features]

        explanation = (
            f"Classified as '{classification}' (confidence: {conf:.0%}). "
            f"Top contributing features: {', '.join(feature_strs)}."
        )

        # Add probability breakdown
        sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        prob_strs = [f"{k}: {v:.0%}" for k, v in sorted_probs[:3]]
        explanation += f" Probability breakdown: {', '.join(prob_strs)}."

        return explanation

    def explain_duplicate(
        self, bug_summary: str, duplicate_summary: str,
        similarity: float,
    ) -> str:
        return (
            f"Marked as DUPLICATE (similarity: {similarity:.0%}). "
            f"Similar to: '{duplicate_summary[:80]}...'" if len(duplicate_summary) > 80
            else f"Marked as DUPLICATE (similarity: {similarity:.0%}). "
                 f"Similar to: '{duplicate_summary}'"
        )
