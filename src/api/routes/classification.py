"""Classification endpoints: classify, override, retrain."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db import crud
from src.api.dependencies import get_pipeline
from src.pipeline import Pipeline

router = APIRouter(prefix="/api", tags=["classification"])


class OverrideRequest(BaseModel):
    bug_id: int
    new_classification: str
    changed_by: str = "reviewer"
    reason: str = ""


@router.post("/classify/{cycle_id}")
def classify_cycle(
    cycle_id: int,
    db: Session = Depends(get_db),
    pipeline: Pipeline = Depends(get_pipeline),
):
    cycle = crud.get_cycle(db, cycle_id)
    if not cycle:
        raise HTTPException(404, "Cycle not found")

    if not pipeline.classifier.is_trained:
        raise HTTPException(400, "Model not trained. Upload labeled data or train first.")

    result = pipeline.classify_cycle(db, cycle_id)
    return {"status": "success", **result}


@router.post("/override")
def override_classification(
    data: OverrideRequest,
    db: Session = Depends(get_db),
    pipeline: Pipeline = Depends(get_pipeline),
):
    bug = crud.get_bug(db, data.bug_id)
    if not bug:
        raise HTTPException(404, "Bug not found")

    updated = crud.override_bug_classification(
        db, data.bug_id, data.new_classification,
        data.changed_by, data.reason,
    )

    retrain_result = pipeline.retrain_if_needed(db)

    return {
        "status": "success",
        "bug_id": updated.id,
        "new_classification": updated.final_classification,
        "retrain_triggered": retrain_result.get("status") == "retrained",
        "retrain_result": retrain_result,
    }


class TrainRequest(BaseModel):
    labeled_data: list[dict]


@router.post("/retrain")
def retrain_model(
    db: Session = Depends(get_db),
    pipeline: Pipeline = Depends(get_pipeline),
):
    result = pipeline.active_learner.retrain(db)
    return result


@router.post("/train-initial")
def train_initial(
    data: TrainRequest,
    db: Session = Depends(get_db),
    pipeline: Pipeline = Depends(get_pipeline),
):
    if len(data.labeled_data) < 10:
        raise HTTPException(400, "Need at least 10 labeled samples")

    for item in data.labeled_data:
        if "summary" not in item or "label" not in item:
            raise HTTPException(400, "Each item needs 'summary' and 'label' fields")

    result = pipeline.train_initial_model(db, data.labeled_data)
    return {"status": "success", **result}
