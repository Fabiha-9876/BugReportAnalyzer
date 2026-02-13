"""Bug report CRUD routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db import crud

router = APIRouter(prefix="/api/bugs", tags=["bugs"])


@router.get("/{bug_id}")
def get_bug(bug_id: int, db: Session = Depends(get_db)):
    bug = crud.get_bug(db, bug_id)
    if not bug:
        raise HTTPException(404, "Bug not found")

    audit_logs = crud.get_audit_logs_for_bug(db, bug_id)

    similar_bugs = []
    if bug.duplicate_of_id:
        orig = crud.get_bug(db, bug.duplicate_of_id)
        if orig:
            similar_bugs.append({
                "id": orig.id, "summary": orig.summary,
                "similarity": bug.duplicate_similarity,
            })

    return {
        "id": bug.id, "cycle_id": bug.cycle_id,
        "external_id": bug.external_id,
        "summary": bug.summary, "description": bug.description,
        "status": bug.status, "priority": bug.priority,
        "severity": bug.severity, "component": bug.component,
        "reporter": bug.reporter, "assignee": bug.assignee,
        "created_date": bug.created_date.isoformat() if bug.created_date else None,
        "resolved_date": bug.resolved_date.isoformat() if bug.resolved_date else None,
        "resolution": bug.resolution, "labels": bug.labels,
        "original_type": bug.original_type,
        "ml_classification": bug.ml_classification,
        "ml_confidence": bug.ml_confidence,
        "ml_explanation": bug.ml_explanation,
        "final_classification": bug.final_classification,
        "classification_source": bug.classification_source,
        "reviewed": bug.reviewed, "reviewed_by": bug.reviewed_by,
        "override_reason": bug.override_reason,
        "duplicate_of_id": bug.duplicate_of_id,
        "duplicate_similarity": bug.duplicate_similarity,
        "similar_bugs": similar_bugs,
        "audit_logs": [
            {
                "id": log.id,
                "previous_classification": log.previous_classification,
                "new_classification": log.new_classification,
                "source": log.source,
                "changed_by": log.changed_by,
                "reason": log.reason,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            }
            for log in audit_logs
        ],
    }
