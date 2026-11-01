"""Command-line interface for repolint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .checks import run_checks
from .scoring import ScoreReport, score

# ANSI colours, disabled when not writing to a terminal.
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def _supports_colour(stream) -> bool:
    return hasattr(stream, "isatty") and stream.isatty()


def _paint(text: str, colour: str, enabled: bool) -> str:
    return f"{colour}{text}{RESET}" if enabled else text


def render_text(report: ScoreReport, colour: bool = True) -> str:
    """Render a human-readable report."""
    lines: list[str] = []
    lines.append(_paint("repolint — repository audit", BOLD, colour))
    lines.append("")

    for result in report.results:
        if result.passed:
            mark = _paint("PASS", GREEN, colour)
        else:
            mark = _paint("FAIL", RED, colour)
        lines.append(
            f"  [{mark}] {result.title} {_paint(f'({result.weight} pts)', DIM, colour)}"
        )
        lines.append(f"         {result.detail}")
        if not result.passed and result.fix:
            lines.append(f"         {_paint('fix:', YELLOW, colour)} {result.fix}")
        lines.append("")

    grade_colour = GREEN if report.score >= 80 else YELLOW if report.score >= 60 else RED
    summary = f"{report.score}/100  grade {report.grade}"
    lines.append(_paint(f"Score: {summary}", grade_colour + BOLD, colour))
    lines.append(
        f"{len(report.passes)} passed, {len(report.failures)} failed "
        f"({report.earned}/{report.max_score} weighted points)"
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repolint",
        description="Audit a repository against a professional-repo checklist.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the repository to audit (default: current directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text report.",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=None,
        metavar="N",
        help="Exit with status 1 if the score is below N (useful in CI).",
    )
    parser.add_argument(
        "--no-colour",
        "--no-color",
        dest="no_colour",
        action="store_true",
        help="Disable ANSI colours.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"repolint {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    root = Path(args.path)
    if not root.is_dir():
        print(f"repolint: not a directory: {root}", file=sys.stderr)
        return 2

    try:
        results = run_checks(root)
    except OSError as exc:
        print(f"repolint: {exc}", file=sys.stderr)
        return 2

    report = score(results)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        colour = not args.no_colour and _supports_colour(sys.stdout)
        print(render_text(report, colour=colour))

    if args.min_score is not None and report.score < args.min_score:
        if not args.json:
            print(
                f"\nrepolint: score {report.score} is below the required minimum "
                f"of {args.min_score}.",
                file=sys.stderr,
            )
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
