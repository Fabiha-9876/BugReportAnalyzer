"""Tests for CRUD operations."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import crud


class TestCRUD:
    def test_create_and_get_project(self, db_session):
        project = crud.create_project(db_session, "My Project", "Description")
        assert project.id is not None
        assert project.name == "My Project"

        fetched = crud.get_project(db_session, project.id)
        assert fetched.name == "My Project"

    def test_get_project_by_name(self, db_session):
        crud.create_project(db_session, "UniqueProject")
        result = crud.get_project_by_name(db_session, "UniqueProject")
        assert result is not None
        assert crud.get_project_by_name(db_session, "Nonexistent") is None

    def test_list_projects(self, db_session):
        crud.create_project(db_session, "P1")
        crud.create_project(db_session, "P2")
        projects = crud.get_projects(db_session)
        assert len(projects) == 2

    def test_create_cycle(self, db_session, sample_project):
        cycle = crud.create_cycle(db_session, sample_project.id, "Sprint 1", "jira", "bugs.csv")
        assert cycle.id is not None
        assert cycle.project_id == sample_project.id

    def test_create_and_get_bugs(self, db_session, sample_cycle):
        bug = crud.create_bug(db_session, cycle_id=sample_cycle.id, summary="Test bug")
        assert bug.id is not None
        fetched = crud.get_bug(db_session, bug.id)
        assert fetched.summary == "Test bug"

    def test_bulk_create_bugs(self, db_session, sample_cycle):
        data = [
            {"cycle_id": sample_cycle.id, "summary": "Bug 1"},
            {"cycle_id": sample_cycle.id, "summary": "Bug 2"},
        ]
        bugs = crud.bulk_create_bugs(db_session, data)
        assert len(bugs) == 2

    def test_override_classification(self, db_session, sample_bugs):
        bug = sample_bugs[0]
        bug.ml_classification = "invalid"
        bug.final_classification = "invalid"
        db_session.commit()

        updated = crud.override_bug_classification(
            db_session, bug.id, "valid", "reviewer1", "Actually a real bug"
        )
        assert updated.final_classification == "valid"
        assert updated.reviewed is True
        assert updated.classification_source == "human"

        logs = crud.get_audit_logs_for_bug(db_session, bug.id)
        assert len(logs) == 1
        assert logs[0].previous_classification == "invalid"
        assert logs[0].new_classification == "valid"

    def test_set_duplicate(self, db_session, sample_bugs):
        crud.set_duplicate(db_session, sample_bugs[3].id, sample_bugs[0].id, 0.85)
        bug = crud.get_bug(db_session, sample_bugs[3].id)
        assert bug.duplicate_of_id == sample_bugs[0].id
        assert bug.final_classification == "duplicate"

    def test_model_version(self, db_session):
        mv = crud.create_model_version(db_session, "v1", 100, 0.85, 0.83, "/path/model.joblib")
        assert mv.is_active is True

        mv2 = crud.create_model_version(db_session, "v2", 200, 0.90, 0.88, "/path/model2.joblib")
        assert mv2.is_active is True
        # v1 should be deactivated
        active = crud.get_active_model(db_session)
        assert active.version == "v2"

    def test_create_user(self, db_session):
        user = crud.create_user(db_session, "testuser", "Test User", "reviewer")
        assert user.role == "reviewer"
        fetched = crud.get_user(db_session, "testuser")
        assert fetched.display_name == "Test User"

    def test_get_cycle_bug_counts(self, db_session, sample_cycle, sample_bugs):
        for bug in sample_bugs:
            bug.final_classification = "valid"
        sample_bugs[1].final_classification = "invalid"
        sample_bugs[4].final_classification = "invalid"
        db_session.commit()

        counts = crud.get_cycle_bug_counts(db_session, sample_cycle.id)
        assert counts["total"] == 5
        assert counts["valid"] == 3
        assert counts["invalid"] == 2
