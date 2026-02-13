"""Regression cycle routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db import crud
from src.metrics.calculator import cycle_metrics

router = APIRouter(prefix="/api/cycles", tags=["cycles"])


@router.get("/{cycle_id}")
def get_cycle(cycle_id: int, db: Session = Depends(get_db)):
    cycle = crud.get_cycle(db, cycle_id)
    if not cycle:
        raise HTTPException(404, "Cycle not found")
    metrics = cycle_metrics(db, cycle_id)
    return {
        "id": cycle.id,
        "name": cycle.name,
        "project_id": cycle.project_id,
        "source_system": cycle.source_system,
        "upload_file_name": cycle.upload_file_name,
        "created_at": cycle.created_at.isoformat() if cycle.created_at else None,
        "metrics": metrics,
    }


@router.get("/{cycle_id}/bugs")
def get_cycle_bugs(cycle_id: int, db: Session = Depends(get_db)):
    cycle = crud.get_cycle(db, cycle_id)
    if not cycle:
        raise HTTPException(404, "Cycle not found")
    bugs = crud.get_bugs_for_cycle(db, cycle_id)
    return [
        {
            "id": b.id, "external_id": b.external_id,
            "summary": b.summary, "status": b.status,
            "priority": b.priority, "severity": b.severity,
            "component": b.component, "reporter": b.reporter,
            "ml_classification": b.ml_classification,
            "ml_confidence": b.ml_confidence,
            "final_classification": b.final_classification,
            "classification_source": b.classification_source,
            "reviewed": b.reviewed,
            "duplicate_of_id": b.duplicate_of_id,
        }
        for b in bugs
    ]
