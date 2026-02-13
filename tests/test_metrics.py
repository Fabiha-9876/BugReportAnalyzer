"""Tests for metrics calculator."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.metrics.calculator import (
    testing_accuracy as calc_testing_accuracy,
    duplicate_rate as calc_duplicate_rate,
    invalid_rate as calc_invalid_rate,
    misclassification_rate as calc_misclassification_rate,
    defect_detection_effectiveness as calc_dde,
    per_tester_accuracy as calc_per_tester_accuracy,
    classification_distribution as calc_classification_dist,
    component_breakdown as calc_component_breakdown,
)
from dataclasses import dataclass
from typing import Optional


@dataclass
class FakeBug:
    final_classification: str = "valid"
    ml_classification: Optional[str] = None
    reporter: str = "alice"
    component: str = "Auth"
    reviewed: bool = False

    def __post_init__(self):
        if self.ml_classification is None:
            self.ml_classification = self.final_classification


def _make_bug(final_cls="valid", ml_cls=None, reporter="alice", component="Auth", reviewed=False):
    return FakeBug(
        final_classification=final_cls,
        ml_classification=ml_cls,
        reporter=reporter,
        component=component,
        reviewed=reviewed,
    )


class TestMetrics:
    def test_accuracy(self):
        bugs = [_make_bug("valid"), _make_bug("valid"), _make_bug("invalid"), _make_bug("duplicate")]
        assert calc_testing_accuracy(bugs) == 0.5

    def test_accuracy_empty(self):
        assert calc_testing_accuracy([]) == 0.0

    def test_dup_rate(self):
        bugs = [_make_bug("valid"), _make_bug("duplicate"), _make_bug("duplicate")]
        assert abs(calc_duplicate_rate(bugs) - 2/3) < 0.01

    def test_inv_rate(self):
        bugs = [_make_bug("valid"), _make_bug("invalid")]
        assert calc_invalid_rate(bugs) == 0.5

    def test_misclass_rate(self):
        bugs = [
            _make_bug("valid", ml_cls="invalid", reviewed=True),
            _make_bug("valid", ml_cls="valid", reviewed=True),
            _make_bug("invalid"),  # not reviewed
        ]
        assert calc_misclassification_rate(bugs) == 0.5

    def test_misclass_no_reviewed(self):
        bugs = [_make_bug("valid")]
        assert calc_misclassification_rate(bugs) == 0.0

    def test_dde(self):
        bugs = [
            _make_bug("valid"), _make_bug("valid"),
            _make_bug("invalid"),
            _make_bug("duplicate"),
        ]
        assert abs(calc_dde(bugs) - 2/3) < 0.01

    def test_per_tester(self):
        bugs = [
            _make_bug("valid", reporter="alice"),
            _make_bug("invalid", reporter="alice"),
            _make_bug("valid", reporter="bob"),
        ]
        result = calc_per_tester_accuracy(bugs)
        assert result["alice"]["accuracy"] == 0.5
        assert result["bob"]["accuracy"] == 1.0

    def test_class_distribution(self):
        bugs = [_make_bug("valid"), _make_bug("valid"), _make_bug("invalid")]
        dist = calc_classification_dist(bugs)
        assert dist["valid"] == 2
        assert dist["invalid"] == 1

    def test_comp_breakdown(self):
        bugs = [
            _make_bug("valid", component="Auth"),
            _make_bug("invalid", component="Auth"),
            _make_bug("valid", component="UI"),
        ]
        result = calc_component_breakdown(bugs)
        assert result["Auth"]["total"] == 2
        assert result["Auth"]["accuracy"] == 0.5
        assert result["UI"]["accuracy"] == 1.0
