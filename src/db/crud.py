from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.db.models import (
    Project, RegressionCycle, BugReport,
    ClassificationAuditLog, ModelVersion, User,
)


# ── Projects ──

def create_project(db: Session, name: str, description: str = "") -> Project:
    project = Project(name=name, description=description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id: int) -> Optional[Project]:
    return db.query(Project).filter(Project.id == project_id).first()


def get_projects(db: Session) -> list[Project]:
    return db.query(Project).order_by(Project.created_at.desc()).all()


def get_project_by_name(db: Session, name: str) -> Optional[Project]:
    return db.query(Project).filter(Project.name == name).first()


# ── Regression Cycles ──

def create_cycle(
    db: Session, project_id: int, name: str,
    source_system: str = "generic", upload_file_name: str = "",
    start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
) -> RegressionCycle:
    cycle = RegressionCycle(
        project_id=project_id, name=name, source_system=source_system,
        upload_file_name=upload_file_name, start_date=start_date, end_date=end_date,
    )
    db.add(cycle)
    db.commit()
    db.refresh(cycle)
    return cycle


def get_cycle(db: Session, cycle_id: int) -> Optional[RegressionCycle]:
    return db.query(RegressionCycle).filter(RegressionCycle.id == cycle_id).first()


def get_cycles_for_project(db: Session, project_id: int) -> list[RegressionCycle]:
    return (
        db.query(RegressionCycle)
        .filter(RegressionCycle.project_id == project_id)
        .order_by(RegressionCycle.created_at.desc())
        .all()
    )


# ── Bug Reports ──

def create_bug(db: Session, **kwargs) -> BugReport:
    bug = BugReport(**kwargs)
    db.add(bug)
    db.commit()
    db.refresh(bug)
    return bug


def bulk_create_bugs(db: Session, bugs_data: list[dict]) -> list[BugReport]:
    bugs = [BugReport(**data) for data in bugs_data]
    db.add_all(bugs)
    db.commit()
    for b in bugs:
        db.refresh(b)
    return bugs


def get_bug(db: Session, bug_id: int) -> Optional[BugReport]:
    return db.query(BugReport).filter(BugReport.id == bug_id).first()


def get_bugs_for_cycle(db: Session, cycle_id: int) -> list[BugReport]:
    return (
        db.query(BugReport)
        .filter(BugReport.cycle_id == cycle_id)
        .order_by(BugReport.id)
        .all()
    )


def get_unreviewed_bugs(db: Session, cycle_id: int) -> list[BugReport]:
    return (
        db.query(BugReport)
        .filter(BugReport.cycle_id == cycle_id, BugReport.reviewed == False)  # noqa: E712
        .order_by(BugReport.ml_confidence.asc())
        .all()
    )


def get_low_confidence_bugs(db: Session, cycle_id: int, threshold: float = 0.6) -> list[BugReport]:
    return (
        db.query(BugReport)
        .filter(
            BugReport.cycle_id == cycle_id,
            BugReport.reviewed == False,  # noqa: E712
            BugReport.ml_confidence != None,  # noqa: E711
            BugReport.ml_confidence < threshold,
        )
        .order_by(BugReport.ml_confidence.asc())
        .all()
    )


def update_bug_classification(
    db: Session, bug_id: int, classification: str, confidence: float,
    explanation: str = "", source: str = "ml",
) -> Optional[BugReport]:
    bug = get_bug(db, bug_id)
    if not bug:
        return None
    bug.ml_classification = classification
    bug.ml_confidence = confidence
    bug.ml_explanation = explanation
    if source == "ml" and not bug.reviewed:
        bug.final_classification = classification
        bug.classification_source = "ml"
    db.commit()
    db.refresh(bug)
    return bug


def override_bug_classification(
    db: Session, bug_id: int, new_classification: str,
    changed_by: str = "reviewer", reason: str = "",
) -> Optional[BugReport]:
    bug = get_bug(db, bug_id)
    if not bug:
        return None
    previous = bug.final_classification
    log = ClassificationAuditLog(
        bug_id=bug_id,
        previous_classification=previous,
        new_classification=new_classification,
        source="human",
        changed_by=changed_by,
        reason=reason,
    )
    db.add(log)
    bug.final_classification = new_classification
    bug.classification_source = "human"
    bug.reviewed = True
    bug.reviewed_by = changed_by
    bug.override_reason = reason
    db.commit()
    db.refresh(bug)
    return bug


def set_duplicate(
    db: Session, bug_id: int, duplicate_of_id: int, similarity: float,
) -> Optional[BugReport]:
    bug = get_bug(db, bug_id)
    if not bug:
        return None
    bug.duplicate_of_id = duplicate_of_id
    bug.duplicate_similarity = similarity
    bug.ml_classification = "duplicate"
    bug.final_classification = "duplicate"
    db.commit()
    db.refresh(bug)
    return bug


def count_human_overrides(db: Session, since: Optional[datetime] = None) -> int:
    q = db.query(func.count(ClassificationAuditLog.id)).filter(
        ClassificationAuditLog.source == "human"
    )
    if since:
        q = q.filter(ClassificationAuditLog.timestamp >= since)
    return q.scalar() or 0


def get_reviewed_bugs(db: Session) -> list[BugReport]:
    return (
        db.query(BugReport)
        .filter(BugReport.reviewed == True)  # noqa: E712
        .all()
    )


# ── Model Versions ──

def create_model_version(
    db: Session, version: str, training_samples: int,
    accuracy: float, f1_score: float, model_path: str,
) -> ModelVersion:
    db.query(ModelVersion).update({ModelVersion.is_active: False})
    mv = ModelVersion(
        version=version, training_samples=training_samples,
        accuracy=accuracy, f1_score=f1_score,
        model_path=model_path, is_active=True,
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)
    return mv


def get_active_model(db: Session) -> Optional[ModelVersion]:
    return db.query(ModelVersion).filter(ModelVersion.is_active == True).first()  # noqa: E712


# ── Users ──

def create_user(db: Session, username: str, display_name: str, role: str = "viewer") -> User:
    user = User(username=username, display_name=display_name, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


# ── Analytics helpers ──

def get_cycle_bug_counts(db: Session, cycle_id: int) -> dict:
    bugs = get_bugs_for_cycle(db, cycle_id)
    total = len(bugs)
    counts = {"valid": 0, "invalid": 0, "duplicate": 0, "enhancement": 0, "wont_fix": 0}
    for bug in bugs:
        cls = bug.final_classification or bug.ml_classification or "valid"
        if cls in counts:
            counts[cls] += 1
        else:
            counts[cls] = 1
    return {"total": total, **counts}


def get_bugs_by_reporter(db: Session, cycle_id: int) -> dict[str, list[BugReport]]:
    bugs = get_bugs_for_cycle(db, cycle_id)
    by_reporter: dict[str, list[BugReport]] = {}
    for bug in bugs:
        reporter = bug.reporter or "Unknown"
        by_reporter.setdefault(reporter, []).append(bug)
    return by_reporter


def get_audit_logs_for_bug(db: Session, bug_id: int) -> list[ClassificationAuditLog]:
    return (
        db.query(ClassificationAuditLog)
        .filter(ClassificationAuditLog.bug_id == bug_id)
        .order_by(ClassificationAuditLog.timestamp.desc())
        .all()
    )
