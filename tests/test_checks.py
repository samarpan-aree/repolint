"""Tests for the individual repository checks."""

from __future__ import annotations

from pathlib import Path

import pytest

from repolint.checks import (
    check_ci,
    check_description,
    check_gitignore,
    check_license,
    check_readme,
    check_structure,
    check_tests,
    run_checks,
)

LONG_README = "# Project\n\n" + ("This project does a useful thing. " * 30)


@pytest.fixture
def empty_repo(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def good_repo(tmp_path: Path) -> Path:
    (tmp_path / "README.md").write_text(LONG_README, encoding="utf-8")
    (tmp_path / "LICENSE").write_text("MIT License", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(
        "__pycache__/\n*.pyc\n.venv/\n.env\n", encoding="utf-8"
    )
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


class TestReadme:
    def test_missing_readme_fails(self, empty_repo: Path) -> None:
        result = check_readme(empty_repo)
        assert result.passed is False
        assert result.weight == 20
        assert result.fix

    def test_placeholder_readme_fails(self, tmp_path: Path) -> None:
        (tmp_path / "README.md").write_text("# hi", encoding="utf-8")
        result = check_readme(tmp_path)
        assert result.passed is False
        assert "placeholder" in result.detail

    def test_substantial_readme_passes(self, good_repo: Path) -> None:
        assert check_readme(good_repo).passed is True

    def test_alternate_readme_names(self, tmp_path: Path) -> None:
        (tmp_path / "README.rst").write_text(LONG_README, encoding="utf-8")
        assert check_readme(tmp_path).passed is True


class TestLicense:
    def test_missing_license_fails(self, empty_repo: Path) -> None:
        assert check_license(empty_repo).passed is False

    def test_license_passes(self, good_repo: Path) -> None:
        assert check_license(good_repo).passed is True

    def test_license_variants(self, tmp_path: Path) -> None:
        (tmp_path / "LICENSE.txt").write_text("Apache", encoding="utf-8")
        assert check_license(tmp_path).passed is True


class TestGitignore:
    def test_missing_gitignore_fails(self, empty_repo: Path) -> None:
        assert check_gitignore(empty_repo).passed is False

    def test_thin_gitignore_fails(self, tmp_path: Path) -> None:
        (tmp_path / ".gitignore").write_text("*.pyc\n", encoding="utf-8")
        result = check_gitignore(tmp_path)
        assert result.passed is False
        assert "too thin" in result.detail

    def test_comments_do_not_count(self, tmp_path: Path) -> None:
        (tmp_path / ".gitignore").write_text("# a\n# b\n# c\n# d\n", encoding="utf-8")
        assert check_gitignore(tmp_path).passed is False

    def test_good_gitignore_passes(self, good_repo: Path) -> None:
        assert check_gitignore(good_repo).passed is True


class TestCI:
    def test_missing_ci_fails(self, empty_repo: Path) -> None:
        assert check_ci(empty_repo).passed is False

    def test_github_workflows_pass(self, good_repo: Path) -> None:
        assert check_ci(good_repo).passed is True

    def test_empty_workflows_dir_fails(self, tmp_path: Path) -> None:
        (tmp_path / ".github" / "workflows").mkdir(parents=True)
        assert check_ci(tmp_path).passed is False

    def test_gitlab_ci_passes(self, tmp_path: Path) -> None:
        (tmp_path / ".gitlab-ci.yml").write_text("stages: [test]\n", encoding="utf-8")
        assert check_ci(tmp_path).passed is True


class TestTests:
    def test_no_tests_fails(self, empty_repo: Path) -> None:
        assert check_tests(empty_repo).passed is False

    def test_python_tests_pass(self, good_repo: Path) -> None:
        assert check_tests(good_repo).passed is True

    def test_js_spec_files_pass(self, tmp_path: Path) -> None:
        (tmp_path / "app.spec.ts").write_text("it('works', () => {})", encoding="utf-8")
        assert check_tests(tmp_path).passed is True

    def test_ignored_dirs_are_skipped(self, tmp_path: Path) -> None:
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "test_thing.py").write_text("x = 1", encoding="utf-8")
        assert check_tests(tmp_path).passed is False


class TestDescription:
    def test_missing_description_fails(self, empty_repo: Path) -> None:
        assert check_description(empty_repo).passed is False

    def test_pyproject_description_passes(self, good_repo: Path) -> None:
        assert check_description(good_repo).passed is True

    def test_package_json_description_passes(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            '{"name": "x", "description": "A useful node package"}', encoding="utf-8"
        )
        assert check_description(tmp_path).passed is True

    def test_short_description_fails(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text('{"description": "hi"}', encoding="utf-8")
        assert check_description(tmp_path).passed is False


class TestStructure:
    def test_clean_structure_passes(self, good_repo: Path) -> None:
        assert check_structure(good_repo).passed is True

    def test_file_dump_fails(self, tmp_path: Path) -> None:
        for i in range(15):
            (tmp_path / f"file_{i}.txt").write_text("x", encoding="utf-8")
        result = check_structure(tmp_path)
        assert result.passed is False
        assert "loose files" in result.detail

    def test_dotfiles_are_not_counted(self, tmp_path: Path) -> None:
        for i in range(15):
            (tmp_path / f".hidden_{i}").write_text("x", encoding="utf-8")
        assert check_structure(tmp_path).passed is True


class TestRunChecks:
    def test_returns_all_checks(self, good_repo: Path) -> None:
        results = run_checks(good_repo)
        assert len(results) == 7
        assert all(r.passed for r in results)

    def test_empty_repo_fails_substantive_checks(self, empty_repo: Path) -> None:
        results = run_checks(empty_repo)
        failed = {r.key for r in results if not r.passed}
        # An empty directory has no loose files, so "structure" legitimately passes.
        assert failed == {"readme", "license", "gitignore", "ci", "tests", "description"}

    def test_missing_directory_raises(self, tmp_path: Path) -> None:
        with pytest.raises(NotADirectoryError):
            run_checks(tmp_path / "does-not-exist")
