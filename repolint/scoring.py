"""Score aggregation and grading for repolint."""

from __future__ import annotations

from dataclasses import dataclass

from .checks import CheckResult

# Grade boundaries, highest first.
GRADE_BANDS: tuple[tuple[int, str], ...] = (
    (90, "A"),
    (80, "B"),
    (70, "C"),
    (60, "D"),
    (0, "F"),
)


@dataclass
class ScoreReport:
    """Aggregated result of a full audit."""

    results: list[CheckResult]
    score: int
    grade: str
    max_score: int
    earned: int

    @property
    def failures(self) -> list[CheckResult]:
        return [r for r in self.results if not r.passed]

    @property
    def passes(self) -> list[CheckResult]:
        return [r for r in self.results if r.passed]

    def as_dict(self) -> dict:
        return {
            "score": self.score,
            "grade": self.grade,
            "earned": self.earned,
            "max_score": self.max_score,
            "passed": len(self.passes),
            "failed": len(self.failures),
            "checks": [r.as_dict() for r in self.results],
        }


def grade_for(score: int) -> str:
    """Map a 0-100 score to a letter grade."""
    for threshold, letter in GRADE_BANDS:
        if score >= threshold:
            return letter
    return "F"


def score(results: list[CheckResult]) -> ScoreReport:
    """Aggregate check results into a weighted 0-100 score."""
    if not results:
        raise ValueError("Cannot score an empty result set")

    max_score = sum(r.weight for r in results)
    earned = sum(r.weight for r in results if r.passed)
    # Round half-up so a 89.5 does not silently become 89.
    pct = int(earned * 100 / max_score + 0.5) if max_score else 0

    return ScoreReport(
        results=results,
        score=pct,
        grade=grade_for(pct),
        max_score=max_score,
        earned=earned,
    )
