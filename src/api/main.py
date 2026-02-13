"""FastAPI application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from configs.config import config
from src.db.database import get_db, init_db
from src.db import crud
from src.metrics.calculator import cycle_metrics, project_trends
from src.api.routes import upload, projects, cycles, bugs, classification, analytics, export


@asynccontextmanager
async def lifespan(application: FastAPI):
    init_db()
    yield


app = FastAPI(title=config.app.title, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(config.app.static_dir)), name="static")
templates = Jinja2Templates(directory=str(config.app.templates_dir))

# Include API routers
app.include_router(upload.router)
app.include_router(projects.router)
app.include_router(cycles.router)
app.include_router(bugs.router)
app.include_router(classification.router)
app.include_router(analytics.router)
app.include_router(export.router)


# ── Page routes ──

@app.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    return dashboard(request, db)


@app.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    all_projects = crud.get_projects(db)
    project_data = []
    all_cycles_data = []
    global_totals = {"total_bugs": 0, "valid": 0, "invalid": 0, "duplicate": 0}
    for p in all_projects:
        p_cycles = crud.get_cycles_for_project(db, p.id)
        latest_accuracy = None
        latest_metrics = None
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
            latest_metrics = cycle_metrics(db, latest.id)
            latest_accuracy = latest_metrics["testing_accuracy"]
        project_data.append({
            "id": p.id, "name": p.name, "description": p.description,
            "cycle_count": len(p_cycles),
            "latest_accuracy": latest_accuracy,
            "latest_metrics": latest_metrics,
            "cycles": cycles_list,
        })
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "projects": project_data,
        "global_totals": global_totals,
        "all_cycles": all_cycles_data,
    })


@app.get("/upload")
def upload_page(request: Request, db: Session = Depends(get_db)):
    all_projects = crud.get_projects(db)
    return templates.TemplateResponse("upload.html", {
        "request": request,
        "projects": [{"id": p.id, "name": p.name} for p in all_projects],
    })


@app.get("/cycles/{cycle_id}")
def cycle_detail_page(cycle_id: int, request: Request, db: Session = Depends(get_db)):
    cycle = crud.get_cycle(db, cycle_id)
    if not cycle:
        return templates.TemplateResponse("dashboard.html", {"request": request, "projects": []})
    metrics = cycle_metrics(db, cycle_id)
    bug_list = crud.get_bugs_for_cycle(db, cycle_id)
    return templates.TemplateResponse("cycle_detail.html", {
        "request": request, "cycle": cycle, "metrics": metrics, "bugs": bug_list,
    })


@app.get("/bugs/{bug_id}")
def bug_detail_page(bug_id: int, request: Request, db: Session = Depends(get_db)):
    bug = crud.get_bug(db, bug_id)
    if not bug:
        return templates.TemplateResponse("dashboard.html", {"request": request, "projects": []})
    audit_logs = crud.get_audit_logs_for_bug(db, bug_id)
    similar = []
    if bug.duplicate_of_id:
        orig = crud.get_bug(db, bug.duplicate_of_id)
        if orig:
            similar.append(orig)
    return templates.TemplateResponse("bug_detail.html", {
        "request": request, "bug": bug, "audit_logs": audit_logs, "similar_bugs": similar,
    })


@app.get("/review/{cycle_id}")
def review_queue_page(cycle_id: int, request: Request, db: Session = Depends(get_db)):
    cycle = crud.get_cycle(db, cycle_id)
    if not cycle:
        return templates.TemplateResponse("dashboard.html", {"request": request, "projects": []})
    low_conf = crud.get_low_confidence_bugs(db, cycle_id)
    unreviewed = crud.get_unreviewed_bugs(db, cycle_id)
    return templates.TemplateResponse("review_queue.html", {
        "request": request, "cycle": cycle,
        "low_confidence_bugs": low_conf, "unreviewed_bugs": unreviewed,
    })


@app.get("/analytics/{project_id}")
def analytics_page(project_id: int, request: Request, db: Session = Depends(get_db)):
    project = crud.get_project(db, project_id)
    if not project:
        return templates.TemplateResponse("dashboard.html", {"request": request, "projects": []})
    trends = project_trends(db, project_id)
    return templates.TemplateResponse("analytics.html", {
        "request": request, "project": project, "trends": trends,
    })
