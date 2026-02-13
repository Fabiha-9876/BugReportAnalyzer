"""Analytics endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db import crud
from src.metrics.calculator import cycle_metrics, project_trends

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/cycle/{cycle_id}")
def get_cycle_analytics(cycle_id: int, db: Session = Depends(get_db)):
    cycle = crud.get_cycle(db, cycle_id)
    if not cycle:
        raise HTTPException(404, "Cycle not found")
    return cycle_metrics(db, cycle_id)


@router.get("/project/{project_id}")
def get_project_analytics(project_id: int, db: Session = Depends(get_db)):
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return {
        "project_id": project.id,
        "project_name": project.name,
        "trends": project_trends(db, project_id),
    }


@router.get("/review-queue/{cycle_id}")
def get_review_queue(cycle_id: int, db: Session = Depends(get_db)):
    cycle = crud.get_cycle(db, cycle_id)
    if not cycle:
        raise HTTPException(404, "Cycle not found")
    bugs = crud.get_low_confidence_bugs(db, cycle_id)
    return [
        {
            "id": b.id, "external_id": b.external_id,
            "summary": b.summary, "component": b.component,
            "reporter": b.reporter,
            "ml_classification": b.ml_classification,
            "ml_confidence": b.ml_confidence,
            "ml_explanation": b.ml_explanation,
            "final_classification": b.final_classification,
        }
        for b in bugs
    ]
