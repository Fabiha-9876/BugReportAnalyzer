"""Shared FastAPI dependencies."""
from src.db.database import get_db
from src.pipeline import Pipeline

_pipeline: Pipeline | None = None


def get_pipeline() -> Pipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = Pipeline()
    return _pipeline
