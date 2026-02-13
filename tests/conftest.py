"""Shared test fixtures."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.database import Base
from src.db.models import (  # noqa: F401
    Project, RegressionCycle, BugReport,
    ClassificationAuditLog, ModelVersion, User,
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_project(db_session):
    from src.db import crud
    return crud.create_project(db_session, "Test Project", "A test project")


@pytest.fixture
def sample_cycle(db_session, sample_project):
    from src.db import crud
    return crud.create_cycle(db_session, sample_project.id, "Cycle 1", "generic", "test.csv")


@pytest.fixture
def sample_bugs(db_session, sample_cycle):
    from src.db import crud
    bugs_data = [
        {"cycle_id": sample_cycle.id, "summary": "Login fails with valid credentials", "description": "Steps to reproduce: 1. Enter valid creds 2. Click login", "component": "Auth", "reporter": "alice", "priority": "Major", "severity": "Major"},
        {"cycle_id": sample_cycle.id, "summary": "Button color should be darker", "description": "I think the button color is too light", "component": "UI", "reporter": "bob", "priority": "Minor", "severity": "Minor"},
        {"cycle_id": sample_cycle.id, "summary": "Payment timeout after 30 seconds", "description": "Payment processing hangs", "component": "Payment", "reporter": "alice", "priority": "Critical", "severity": "Critical"},
        {"cycle_id": sample_cycle.id, "summary": "Login is broken with valid credentials", "description": "Cannot login even with correct password", "component": "Auth", "reporter": "carol", "priority": "Major", "severity": "Major"},
        {"cycle_id": sample_cycle.id, "summary": "Would be nice to have keyboard shortcuts", "description": "Feature request for shortcuts", "component": "UI", "reporter": "bob", "priority": "Trivial", "severity": "Trivial"},
    ]
    return crud.bulk_create_bugs(db_session, bugs_data)


@pytest.fixture
def sample_csv_path(tmp_path):
    import csv
    csv_file = tmp_path / "test_bugs.csv"
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Issue key", "Summary", "Description", "Status", "Priority", "Severity", "Component/s", "Reporter", "Issue Type"])
        writer.writerow(["TEST-1", "Login fails", "Cannot login", "Open", "Major", "Major", "Auth", "alice", "Bug"])
        writer.writerow(["TEST-2", "UI color issue", "Color is wrong", "Open", "Minor", "Minor", "UI", "bob", "Bug"])
        writer.writerow(["TEST-3", "Payment error", "Payment broken", "Open", "Critical", "Critical", "Payment", "carol", "Bug"])
    return csv_file
