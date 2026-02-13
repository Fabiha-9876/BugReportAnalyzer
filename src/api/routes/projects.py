"""Project CRUD routes."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db import crud

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    description: str = ""


@router.get("")
def list_projects(db: Session = Depends(get_db)):
    projects = crud.get_projects(db)
    return [
        {
            "id": p.id, "name": p.name, "description": p.description,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "cycle_count": len(p.cycles),
        }
        for p in projects
    ]


@router.post("")
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    existing = crud.get_project_by_name(db, data.name)
    if existing:
        raise HTTPException(400, "Project with this name already exists")
    project = crud.create_project(db, data.name, data.description)
    return {"id": project.id, "name": project.name}


@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    cycles = crud.get_cycles_for_project(db, project_id)
    return {
        "id": project.id, "name": project.name, "description": project.description,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "cycles": [
            {"id": c.id, "name": c.name, "source_system": c.source_system,
             "created_at": c.created_at.isoformat() if c.created_at else None,
             "bug_count": len(c.bugs)}
            for c in cycles
        ],
    }
