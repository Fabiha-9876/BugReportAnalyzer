"""Upload CSV/Excel files."""
from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.api.dependencies import get_pipeline
from src.pipeline import Pipeline

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    cycle_name: str = Form(...),
    source_system: str = Form("auto"),
    db: Session = Depends(get_db),
    pipeline: Pipeline = Depends(get_pipeline),
):
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("csv", "xlsx", "xls"):
        raise HTTPException(400, "Unsupported file type. Use CSV or Excel.")

    contents = await file.read()
    file_source = BytesIO(contents)

    try:
        result = pipeline.process_upload(
            db, file_source, file.filename,
            project_id, cycle_name, source_system,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {"status": "success", **result}
