"""Tests for API endpoints."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from configs.config import config
from src.db.database import Base, get_db
from src.db.models import (  # noqa: F401
    Project, RegressionCycle, BugReport,
    ClassificationAuditLog, ModelVersion, User,
)


def create_test_app(get_db_override):
    """Create a fresh test app with its own lifespan that doesn't touch real DB."""

    @asynccontextmanager
    async def test_lifespan(application: FastAPI):
        yield

    test_app = FastAPI(lifespan=test_lifespan)
    test_app.mount("/static", StaticFiles(directory=str(config.app.static_dir)), name="static")

    # Import and include all routers
    from src.api.routes import upload, projects, cycles, bugs, classification, analytics, export
    test_app.include_router(upload.router)
    test_app.include_router(projects.router)
    test_app.include_router(cycles.router)
    test_app.include_router(bugs.router)
    test_app.include_router(classification.router)
    test_app.include_router(analytics.router)
    test_app.include_router(export.router)

    # Add page routes
    templates = Jinja2Templates(directory=str(config.app.templates_dir))

    from fastapi import Request, Depends
    from sqlalchemy.orm import Session as DBSession
    from src.db import crud
    from src.metrics.calculator import cycle_metrics

    @test_app.get("/dashboard")
    @test_app.get("/")
    def dashboard(request: Request, db: DBSession = Depends(get_db)):
        all_projects = crud.get_projects(db)
        project_data = []
        all_cycles_data = []
        global_totals = {"total_bugs": 0, "valid": 0, "invalid": 0, "duplicate": 0}
        for p in all_projects:
            p_cycles = crud.get_cycles_for_project(db, p.id)
            latest_accuracy = None
            cycles_list = []
            for c in sorted(p_cycles, key=lambda c: c.created_at):
                m = cycle_metrics(db, c.id)
                cycles_list.append({"id": c.id, "name": c.name, "metrics": m})
                all_cycles_data.append({"id": c.id, "name": c.name, "project": p.name, "metrics": m})
                global_totals["total_bugs"] += m["total_bugs"]
                for k in ("valid", "invalid", "duplicate"):
                    global_totals[k] += m["classification_distribution"].get(k, 0)
            if p_cycles:
                latest = sorted(p_cycles, key=lambda c: c.created_at, reverse=True)[0]
                latest_accuracy = cycle_metrics(db, latest.id)["testing_accuracy"]
            project_data.append({
                "id": p.id, "name": p.name, "description": p.description,
                "cycle_count": len(p_cycles), "latest_accuracy": latest_accuracy,
                "latest_metrics": None, "cycles": cycles_list,
            })
        return templates.TemplateResponse("dashboard.html", {
            "request": request, "projects": project_data,
            "global_totals": global_totals, "all_cycles": all_cycles_data,
        })

    @test_app.get("/upload")
    def upload_page(request: Request, db: DBSession = Depends(get_db)):
        all_projects = crud.get_projects(db)
        return templates.TemplateResponse("upload.html", {
            "request": request,
            "projects": [{"id": p.id, "name": p.name} for p in all_projects],
        })

    test_app.dependency_overrides[get_db] = get_db_override
    return test_app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    test_app = create_test_app(override_get_db)
    with TestClient(test_app) as c:
        yield c


class TestProjectsAPI:
    def test_create_project(self, client):
        resp = client.post("/api/projects", json={"name": "Test Project", "description": "Desc"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test Project"

    def test_list_projects(self, client):
        client.post("/api/projects", json={"name": "P1"})
        client.post("/api/projects", json={"name": "P2"})
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_get_project(self, client):
        create_resp = client.post("/api/projects", json={"name": "P1"})
        pid = create_resp.json()["id"]
        resp = client.get(f"/api/projects/{pid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "P1"

    def test_get_nonexistent_project(self, client):
        resp = client.get("/api/projects/999")
        assert resp.status_code == 404

    def test_duplicate_project_name(self, client):
        client.post("/api/projects", json={"name": "Same"})
        resp = client.post("/api/projects", json={"name": "Same"})
        assert resp.status_code == 400


class TestUploadAPI:
    def test_upload_csv(self, client):
        client.post("/api/projects", json={"name": "Upload Test"})
        csv_content = b"Issue key,Summary,Description,Status,Priority,Component/s,Reporter,Issue Type\nTEST-1,Login bug,Cannot login,Open,Major,Auth,alice,Bug\n"
        resp = client.post(
            "/api/upload",
            data={"project_id": "1", "cycle_name": "Cycle 1", "source_system": "auto"},
            files={"file": ("test.csv", csv_content, "text/csv")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_bugs"] == 1
        assert data["source_system"] == "jira"

    def test_upload_bad_file_type(self, client):
        client.post("/api/projects", json={"name": "Upload Test"})
        resp = client.post(
            "/api/upload",
            data={"project_id": "1", "cycle_name": "Cycle 1"},
            files={"file": ("test.txt", b"not csv", "text/plain")},
        )
        assert resp.status_code == 400


class TestPageRoutes:
    def test_dashboard_page(self, client):
        resp = client.get("/dashboard")
        assert resp.status_code == 200
        assert b"Dashboard" in resp.content

    def test_upload_page(self, client):
        resp = client.get("/upload")
        assert resp.status_code == 200
        assert b"Upload" in resp.content

    def test_index_page(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
