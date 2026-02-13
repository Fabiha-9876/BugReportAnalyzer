"""Detect duplicate bug reports using cosine similarity on TF-IDF vectors."""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from configs.config import config


class DuplicateDetector:
    def __init__(self, threshold: float | None = None):
        self.threshold = threshold or config.ml.duplicate_threshold

    def find_duplicates(
        self, vectors: np.ndarray, bug_ids: list[int],
    ) -> list[dict]:
        if len(vectors) < 2:
            return []

        sim_matrix = cosine_similarity(vectors)
        np.fill_diagonal(sim_matrix, 0.0)

        duplicates = []
        marked_as_dup = set()
        originals = set()

        # Process in order: later bugs are more likely to be duplicates of earlier ones
        for i in range(len(vectors)):
            if bug_ids[i] in marked_as_dup:
                continue
            # Only compare against earlier bugs that aren't already dups
            best_sim = 0.0
            best_j = -1
            for j in range(i):
                if bug_ids[j] in marked_as_dup:
                    continue
                if sim_matrix[i][j] > best_sim:
                    best_sim = sim_matrix[i][j]
                    best_j = j

            if best_sim >= self.threshold and best_j >= 0:
                duplicates.append({
                    "bug_id": bug_ids[i],
                    "duplicate_of_id": bug_ids[best_j],
                    "similarity": float(best_sim),
                })
                marked_as_dup.add(bug_ids[i])
                originals.add(bug_ids[best_j])

        return duplicates

    def check_single(
        self, vector: np.ndarray, existing_vectors: np.ndarray,
        existing_ids: list[int],
    ) -> dict | None:
        if len(existing_vectors) == 0:
            return None

        sims = cosine_similarity(vector.reshape(1, -1), existing_vectors)[0]
        max_idx = np.argmax(sims)
        max_sim = sims[max_idx]

        if max_sim >= self.threshold:
            return {
                "duplicate_of_id": existing_ids[max_idx],
                "similarity": float(max_sim),
            }
        return None
