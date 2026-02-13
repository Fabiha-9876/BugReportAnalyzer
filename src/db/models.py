from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON,
)
from sqlalchemy.orm import relationship

from src.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    cycles = relationship("RegressionCycle", back_populates="project", cascade="all, delete-orphan")


class RegressionCycle(Base):
    __tablename__ = "regression_cycles"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    source_system = Column(String(50), default="generic")
    upload_file_name = Column(String(255), default="")
    created_at = Column(DateTime, default=utcnow)

    project = relationship("Project", back_populates="cycles")
    bugs = relationship("BugReport", back_populates="cycle", cascade="all, delete-orphan")


class BugReport(Base):
    __tablename__ = "bug_reports"

    id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(Integer, ForeignKey("regression_cycles.id"), nullable=False)
    external_id = Column(String(100), default="")
    summary = Column(Text, nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), default="")
    priority = Column(String(50), default="")
    severity = Column(String(50), default="")
    component = Column(String(255), default="")
    reporter = Column(String(255), default="")
    assignee = Column(String(255), default="")
    created_date = Column(DateTime, nullable=True)
    resolved_date = Column(DateTime, nullable=True)
    resolution = Column(String(100), default="")
    labels = Column(Text, default="")
    original_type = Column(String(100), default="Bug")

    # ML fields
    ml_classification = Column(String(50), nullable=True)
    ml_confidence = Column(Float, nullable=True)
    ml_explanation = Column(Text, nullable=True)
    duplicate_of_id = Column(Integer, ForeignKey("bug_reports.id"), nullable=True)
    duplicate_similarity = Column(Float, nullable=True)
    tfidf_vector_json = Column(JSON, nullable=True)

    # Final classification
    final_classification = Column(String(50), nullable=True)
    classification_source = Column(String(20), default="ml")  # "ml" or "human"
    reviewed = Column(Boolean, default=False)
    reviewed_by = Column(String(255), nullable=True)
    override_reason = Column(Text, nullable=True)

    cycle = relationship("RegressionCycle", back_populates="bugs")
    duplicate_of = relationship("BugReport", remote_side=[id], foreign_keys=[duplicate_of_id])
    audit_logs = relationship("ClassificationAuditLog", back_populates="bug", cascade="all, delete-orphan")


class ClassificationAuditLog(Base):
    __tablename__ = "classification_audit_log"

    id = Column(Integer, primary_key=True, index=True)
    bug_id = Column(Integer, ForeignKey("bug_reports.id"), nullable=False)
    previous_classification = Column(String(50), nullable=True)
    new_classification = Column(String(50), nullable=False)
    source = Column(String(20), nullable=False)  # "ml" or "human"
    changed_by = Column(String(255), nullable=True)
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utcnow)

    bug = relationship("BugReport", back_populates="audit_logs")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), nullable=False, unique=True)
    trained_at = Column(DateTime, default=utcnow)
    training_samples = Column(Integer, default=0)
    accuracy = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    model_path = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    role = Column(String(20), default="viewer")  # admin, reviewer, viewer
    created_at = Column(DateTime, default=utcnow)
