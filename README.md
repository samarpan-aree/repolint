# repolint

**Audit any repository against a professional-repo checklist and get a weighted score.**

[![CI](https://github.com/ROYAL-SMP/repolint/actions/workflows/ci.yml/badge.svg)](https://github.com/ROYAL-SMP/repolint/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-60%20passing-brightgreen)](tests/)
[![Dependencies](https://img.shields.io/badge/dependencies-zero-success)](pyproject.toml)

Most repositories fail for boring, fixable reasons: no license, a two-line README, no CI, no tests. `repolint` turns that into a number you can act on — and a CI gate you can enforce.

```
$ repolint .

repolint — repository audit

  [PASS] README present (20 pts)
         README.md found (4821 characters).

  [FAIL] License file (15 pts)
         No LICENSE file found.
         fix: Add an OSI license (MIT or Apache-2.0) so others can legally use the code.

  [PASS] .gitignore (10 pts)
         .gitignore has 24 rules.

  [FAIL] CI configuration (15 pts)
         No CI configuration found.
         fix: Add .github/workflows/ci.yml that installs deps and runs the test suite.

  [PASS] Test suite (20 pts)
         3 test file(s) detected.

  [PASS] Project description (10 pts)
         Description declared in pyproject.toml.

  [PASS] Directory structure (10 pts)
         2 loose file(s) at the root — acceptable.

Score: 70/100  grade C
5 passed, 2 failed (70/100 weighted points)
```

---

## Why this exists

A repository is a portfolio artifact. Recruiters and reviewers open it for about fifteen seconds and decide whether you are careful. The signals they look for are consistent and cheap to produce — but they are also easy to forget. `repolint` encodes that checklist so it stops being a matter of memory.

It is deliberately **dependency-free** and **offline**: it reads the filesystem, never the network, so it runs in any CI job in under a second.

## Install

```bash
pip install -e .
```

Or run it without installing:

```bash
python -m repolint .
```

## Usage

```bash
repolint [path] [options]
```

| Option | Description |
| --- | --- |
| `path` | Repository to audit. Defaults to the current directory. |
| `--json` | Emit machine-readable JSON instead of a text report. |
| `--min-score N` | Exit with status `1` if the score is below `N`. |
| `--no-colour` | Disable ANSI colours (auto-disabled when not a TTY). |
| `--version` | Print the version and exit. |

### In CI

Fail the build when a repository drops below your standard:

```yaml
- name: Enforce repository quality
  run: |
    pip install -e .
    repolint . --min-score 80
```

### As a JSON feed

```bash
repolint . --json | jq '.score, .grade, [.checks[] | select(.passed == false) | .key]'
```
