"""Tests for the command-line interface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from repolint.checks import run_checks
from repolint.cli import build_parser, main, render_text
from repolint.scoring import score

LONG_README = "# Project\n\n" + ("This project does a useful thing. " * 30)


@pytest.fixture
def good_repo(tmp_path: Path) -> Path:
    (tmp_path / "README.md").write_text(LONG_README, encoding="utf-8")
    (tmp_path / "LICENSE").write_text("MIT License", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("__pycache__/\n*.pyc\n.venv/\n", encoding="utf-8")
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("on: push\n", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_core.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\ndescription = "A genuinely useful demo project"\n',
        encoding="utf-8",
    )
    return tmp_path


class TestParser:
    def test_defaults(self) -> None:
        args = build_parser().parse_args([])
        assert args.path == "."
        assert args.json is False
        assert args.min_score is None

    def test_flags(self) -> None:
        args = build_parser().parse_args(["/tmp/x", "--json", "--min-score", "80"])
        assert args.path == "/tmp/x"
        assert args.json is True
        assert args.min_score == 80


class TestMain:
    def test_good_repo_exits_zero(self, good_repo: Path, capsys) -> None:
        assert main([str(good_repo), "--no-colour"]) == 0
        out = capsys.readouterr().out
        assert "100/100" in out
        assert "grade A" in out

    def test_empty_repo_exits_zero_without_threshold(self, tmp_path: Path, capsys) -> None:
        assert main([str(tmp_path), "--no-colour"]) == 0
        assert "0/100" in capsys.readouterr().out

    def test_min_score_failure_exits_one(self, tmp_path: Path, capsys) -> None:
        assert main([str(tmp_path), "--min-score", "50", "--no-colour"]) == 1
        assert "below the required minimum" in capsys.readouterr().err

    def test_min_score_pass_exits_zero(self, good_repo: Path) -> None:
        assert main([str(good_repo), "--min-score", "90", "--no-colour"]) == 0

    def test_json_output_is_valid(self, good_repo: Path, capsys) -> None:
        assert main([str(good_repo), "--json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["score"] == 100
        assert payload["grade"] == "A"
        assert len(payload["checks"]) == 7

    def test_missing_path_exits_two(self, tmp_path: Path, capsys) -> None:
        assert main([str(tmp_path / "nope")]) == 2
        assert "not a directory" in capsys.readouterr().err


class TestRender:
    def test_plain_text_has_no_ansi(self, good_repo: Path) -> None:
        report = score(run_checks(good_repo))
        text = render_text(report, colour=False)
        assert "\033[" not in text
        assert "PASS" in text

    def test_colour_adds_ansi(self, good_repo: Path) -> None:
        report = score(run_checks(good_repo))
        assert "\033[" in render_text(report, colour=True)

    def test_failures_show_fix_hint(self, tmp_path: Path) -> None:
        report = score(run_checks(tmp_path))
        text = render_text(report, colour=False)
        assert "fix:" in text
