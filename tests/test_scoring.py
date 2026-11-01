"""Tests for score aggregation and grading."""

from __future__ import annotations

import pytest

from repolint.checks import CheckResult
from repolint.scoring import grade_for, score


def make(key: str, passed: bool, weight: int = 10) -> CheckResult:
    return CheckResult(
        key=key,
        title=key.title(),
        passed=passed,
        weight=weight,
        detail="test",
    )


class TestGradeFor:
    @pytest.mark.parametrize(
        "value,expected",
        [
            (100, "A"),
            (90, "A"),
            (89, "B"),
            (80, "B"),
            (79, "C"),
            (70, "C"),
            (69, "D"),
            (60, "D"),
            (59, "F"),
            (0, "F"),
        ],
    )
    def test_bands(self, value: int, expected: str) -> None:
        assert grade_for(value) == expected


class TestScore:
    def test_all_passing_is_100(self) -> None:
        report = score([make("a", True), make("b", True)])
        assert report.score == 100
        assert report.grade == "A"
        assert report.failures == []

    def test_all_failing_is_zero(self) -> None:
        report = score([make("a", False), make("b", False)])
        assert report.score == 0
        assert report.grade == "F"
        assert len(report.failures) == 2

    def test_weighting_is_respected(self) -> None:
        # 20 of 30 points earned -> 66.67 -> 67
        report = score([make("big", True, 20), make("small", False, 10)])
        assert report.score == 67
        assert report.grade == "D"

    def test_rounds_half_up(self) -> None:
        # 1 of 8 -> 12.5 -> 13
        report = score([make("a", True, 1), make("b", False, 7)])
        assert report.score == 13

    def test_empty_results_raise(self) -> None:
        with pytest.raises(ValueError):
            score([])

    def test_as_dict_shape(self) -> None:
        payload = score([make("a", True), make("b", False)]).as_dict()
        assert payload["score"] == 50
        assert payload["passed"] == 1
        assert payload["failed"] == 1
        assert len(payload["checks"]) == 2
        assert payload["checks"][0]["key"] == "a"
