"""Export routes for CSV download."""
import io
import csv

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db import crud

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/cycle/{cycle_id}")
def export_cycle_csv(cycle_id: int, db: Session = Depends(get_db)):
    cycle = crud.get_cycle(db, cycle_id)
    if not cycle:
        raise HTTPException(404, "Cycle not found")

    bugs = crud.get_bugs_for_cycle(db, cycle_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "External ID", "Summary", "Status", "Priority", "Severity",
        "Component", "Reporter", "ML Classification", "ML Confidence",
        "Final Classification", "Classification Source", "Reviewed",
        "Duplicate Of", "Duplicate Similarity",
    ])

    for b in bugs:
        writer.writerow([
            b.id, b.external_id, b.summary, b.status, b.priority, b.severity,
            b.component, b.reporter, b.ml_classification or "",
            f"{b.ml_confidence:.2f}" if b.ml_confidence else "",
            b.final_classification or "", b.classification_source or "",
            "Yes" if b.reviewed else "No",
            b.duplicate_of_id or "",
            f"{b.duplicate_similarity:.2f}" if b.duplicate_similarity else "",
        ])

    output.seek(0)
    filename = f"cycle_{cycle_id}_{cycle.name.replace(' ', '_')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
