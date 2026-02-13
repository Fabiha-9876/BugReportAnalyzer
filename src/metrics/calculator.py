"""Compute all bug report accuracy metrics."""
from sqlalchemy.orm import Session

from src.db import crud
from src.db.models import BugReport


def _classify(bug: BugReport) -> str:
    return bug.final_classification or bug.ml_classification or "valid"


def testing_accuracy(bugs: list[BugReport]) -> float:
    if not bugs:
        return 0.0
    valid = sum(1 for b in bugs if _classify(b) == "valid")
    return valid / len(bugs)


def duplicate_rate(bugs: list[BugReport]) -> float:
    if not bugs:
        return 0.0
    dups = sum(1 for b in bugs if _classify(b) == "duplicate")
    return dups / len(bugs)


def invalid_rate(bugs: list[BugReport]) -> float:
    if not bugs:
        return 0.0
    inv = sum(1 for b in bugs if _classify(b) == "invalid")
    return inv / len(bugs)


def misclassification_rate(bugs: list[BugReport]) -> float:
    reviewed = [b for b in bugs if b.reviewed and b.ml_classification]
    if not reviewed:
        return 0.0
    disagreements = sum(
        1 for b in reviewed if b.ml_classification != b.final_classification
    )
    return disagreements / len(reviewed)


def defect_detection_effectiveness(bugs: list[BugReport]) -> float:
    unique_bugs = [b for b in bugs if _classify(b) != "duplicate"]
    if not unique_bugs:
        return 0.0
    valid = sum(1 for b in unique_bugs if _classify(b) == "valid")
    valid_or_invalid = sum(1 for b in unique_bugs if _classify(b) in ("valid", "invalid"))
    if valid_or_invalid == 0:
        return 0.0
    return valid / valid_or_invalid


def per_tester_accuracy(bugs: list[BugReport]) -> dict[str, dict]:
    by_reporter: dict[str, list[BugReport]] = {}
    for b in bugs:
        reporter = b.reporter or "Unknown"
        by_reporter.setdefault(reporter, []).append(b)

    results = {}
    for reporter, reporter_bugs in by_reporter.items():
        total = len(reporter_bugs)
        valid = sum(1 for b in reporter_bugs if _classify(b) == "valid")
        invalid = sum(1 for b in reporter_bugs if _classify(b) == "invalid")
        duplicate = sum(1 for b in reporter_bugs if _classify(b) == "duplicate")
        results[reporter] = {
            "total": total,
            "valid": valid,
            "invalid": invalid,
            "duplicate": duplicate,
            "accuracy": valid / total if total > 0 else 0.0,
        }
    return results


def classification_distribution(bugs: list[BugReport]) -> dict[str, int]:
    dist: dict[str, int] = {}
    for b in bugs:
        cls = _classify(b)
        dist[cls] = dist.get(cls, 0) + 1
    return dist


def component_breakdown(bugs: list[BugReport]) -> dict[str, dict]:
    by_component: dict[str, list[BugReport]] = {}
    for b in bugs:
        comp = b.component or "Unassigned"
        by_component.setdefault(comp, []).append(b)

    results = {}
    for comp, comp_bugs in by_component.items():
        total = len(comp_bugs)
        valid = sum(1 for b in comp_bugs if _classify(b) == "valid")
        results[comp] = {
            "total": total,
            "valid": valid,
            "invalid": total - valid,
            "accuracy": valid / total if total > 0 else 0.0,
        }
    return results


def cycle_metrics(db: Session, cycle_id: int) -> dict:
    bugs = crud.get_bugs_for_cycle(db, cycle_id)
    return {
        "total_bugs": len(bugs),
        "testing_accuracy": testing_accuracy(bugs),
        "duplicate_rate": duplicate_rate(bugs),
        "invalid_rate": invalid_rate(bugs),
        "misclassification_rate": misclassification_rate(bugs),
        "dde": defect_detection_effectiveness(bugs),
        "classification_distribution": classification_distribution(bugs),
        "per_tester": per_tester_accuracy(bugs),
        "component_breakdown": component_breakdown(bugs),
    }


def project_trends(db: Session, project_id: int) -> list[dict]:
    cycles = crud.get_cycles_for_project(db, project_id)
    trends = []
    for cycle in sorted(cycles, key=lambda c: c.created_at):
        metrics = cycle_metrics(db, cycle.id)
        trends.append({
            "cycle_id": cycle.id,
            "cycle_name": cycle.name,
            "created_at": cycle.created_at.isoformat() if cycle.created_at else "",
            **metrics,
        })
    return trends
