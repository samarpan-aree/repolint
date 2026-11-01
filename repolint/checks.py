"""Individual repository checks.

Each check inspects a repository directory and returns a CheckResult.
Checks are pure functions of the filesystem so they are trivially testable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

# Directories that never contain project source worth scanning.
IGNORED_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "target",
    "vendor",
}

LICENSE_NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING")
README_NAMES = ("README.md", "README.rst", "README.txt", "README")
CI_PATHS = (
    ".github/workflows",
    ".gitlab-ci.yml",
    ".circleci/config.yml",
    "azure-pipelines.yml",
    ".travis.yml",
)

# A README shorter than this is almost certainly a placeholder.
MIN_README_CHARS = 400


@dataclass(frozen=True)
class CheckResult:
    """Outcome of a single check."""

    key: str
    title: str
    passed: bool
    weight: int
    detail: str
    fix: str = ""

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "title": self.title,
            "passed": self.passed,
            "weight": self.weight,
            "detail": self.detail,
            "fix": self.fix,
        }


def _iter_files(root: Path) -> Iterable[Path]:
    """Yield every file under root, skipping ignored directories."""
    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.is_file():
            yield path


def _find_first(root: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        candidate = root / name
        if candidate.is_file():
            return candidate
    return None


def check_readme(root: Path) -> CheckResult:
    readme = _find_first(root, README_NAMES)
    if readme is None:
        return CheckResult(
            key="readme",
            title="README present",
            passed=False,
            weight=20,
            detail="No README file found at the repository root.",
            fix="Add a README.md with what the project does, install steps and usage.",
        )
    text = readme.read_text(encoding="utf-8", errors="ignore")
    if len(text) < MIN_README_CHARS:
        return CheckResult(
            key="readme",
            title="README present",
            passed=False,
            weight=20,
            detail=f"{readme.name} is only {len(text)} characters — a placeholder.",
            fix="Expand the README: purpose, install, usage, architecture, roadmap.",
        )
    return CheckResult(
        key="readme",
        title="README present",
        passed=True,
        weight=20,
        detail=f"{readme.name} found ({len(text)} characters).",
    )


def check_license(root: Path) -> CheckResult:
    license_file = _find_first(root, LICENSE_NAMES)
    if license_file is None:
        return CheckResult(
            key="license",
            title="License file",
            passed=False,
            weight=15,
            detail="No LICENSE file found.",
            fix="Add an OSI license (MIT or Apache-2.0) so others can legally use the code.",
        )
    return CheckResult(
        key="license",
        title="License file",
        passed=True,
        weight=15,
        detail=f"{license_file.name} found.",
    )


def check_gitignore(root: Path) -> CheckResult:
    gitignore = root / ".gitignore"
    if not gitignore.is_file():
        return CheckResult(
            key="gitignore",
            title=".gitignore",
            passed=False,
            weight=10,
            detail="No .gitignore found — build artifacts and secrets may be committed.",
            fix="Add a .gitignore for your language (Python, Node, etc.).",
        )
    lines = [
        line.strip()
        for line in gitignore.read_text(encoding="utf-8", errors="ignore").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if len(lines) < 3:
        return CheckResult(
            key="gitignore",
            title=".gitignore",
            passed=False,
            weight=10,
            detail=f".gitignore has only {len(lines)} rule(s) — too thin to be useful.",
            fix="Add rules for virtualenvs, caches, build output and local env files.",
        )
    return CheckResult(
        key="gitignore",
        title=".gitignore",
        passed=True,
        weight=10,
        detail=f".gitignore has {len(lines)} rules.",
    )


def check_ci(root: Path) -> CheckResult:
    for rel in CI_PATHS:
        candidate = root / rel
        if candidate.is_dir() and any(candidate.iterdir()):
            return CheckResult(
                key="ci",
                title="CI configuration",
                passed=True,
                weight=15,
                detail=f"CI config found at {rel}/.",
            )
        if candidate.is_file():
            return CheckResult(
                key="ci",
                title="CI configuration",
                passed=True,
                weight=15,
                detail=f"CI config found at {rel}.",
            )
    return CheckResult(
        key="ci",
        title="CI configuration",
        passed=False,
        weight=15,
        detail="No CI configuration found.",
        fix="Add .github/workflows/ci.yml that installs deps and runs the test suite.",
    )


def check_tests(root: Path) -> CheckResult:
    test_files = [
        path
        for path in _iter_files(root)
        if re.search(
            r"(^test_.*\.py$|.*_test\.py$|.*\.test\.(js|ts|tsx)$|.*\.spec\.(js|ts|tsx)$)",
            path.name,
        )
    ]
    if not test_files:
        return CheckResult(
            key="tests",
            title="Test suite",
            passed=False,
            weight=20,
            detail="No test files detected.",
            fix="Add tests (pytest, vitest or jest) covering the core logic.",
        )
    return CheckResult(
        key="tests",
        title="Test suite",
        passed=True,
        weight=20,
        detail=f"{len(test_files)} test file(s) detected.",
    )


def check_description(root: Path) -> CheckResult:
    """A repo description lives in package metadata or a manifest."""
    candidates = [
        root / "pyproject.toml",
        root / "package.json",
        root / "Cargo.toml",
        root / "setup.py",
    ]
    for candidate in candidates:
        if not candidate.is_file():
            continue
        text = candidate.read_text(encoding="utf-8", errors="ignore")
        if re.search(r'^\s*description\s*=\s*["\'][^"\']{10,}', text, re.MULTILINE):
            return CheckResult(
                key="description",
                title="Project description",
                passed=True,
                weight=10,
                detail=f"Description declared in {candidate.name}.",
            )
        if re.search(r'"description"\s*:\s*"[^"]{10,}"', text):
            return CheckResult(
                key="description",
                title="Project description",
                passed=True,
                weight=10,
                detail=f"Description declared in {candidate.name}.",
            )
    return CheckResult(
        key="description",
        title="Project description",
        passed=False,
        weight=10,
        detail="No meaningful project description in package metadata.",
        fix="Add a one-line description to pyproject.toml or package.json.",
    )


def check_structure(root: Path) -> CheckResult:
    """A flat dump of loose files at the root is a smell."""
    loose = [
        path
        for path in root.iterdir()
        if path.is_file() and not path.name.startswith(".")
    ]
    if len(loose) > 12:
        return CheckResult(
            key="structure",
            title="Directory structure",
            passed=False,
            weight=10,
            detail=f"{len(loose)} loose files at the repository root.",
            fix="Move source into a package directory and docs into docs/.",
        )
    return CheckResult(
        key="structure",
        title="Directory structure",
        passed=True,
        weight=10,
        detail=f"{len(loose)} loose file(s) at the root — acceptable.",
    )


ALL_CHECKS: tuple[Callable[[Path], CheckResult], ...] = (
    check_readme,
    check_license,
    check_gitignore,
    check_ci,
    check_tests,
    check_description,
    check_structure,
)


def run_checks(root: Path) -> list[CheckResult]:
    """Run every check against root and return the results in order."""
    root = Path(root)
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")
    return [check(root) for check in ALL_CHECKS]
