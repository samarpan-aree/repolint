"""repolint — audit a repository against a professional-repo checklist."""

__version__ = "1.0.0"

from .checks import CheckResult, run_checks
from .scoring import ScoreReport, score

__all__ = ["CheckResult", "run_checks", "ScoreReport", "score", "__version__"]
