# repolint

**Audit any repo against a professional-repo checklist. Weighted 0–100 score, CI-ready.**

[![CI](https://github.com/samarpan-aree/repolint/actions/workflows/ci.yml/badge.svg)](https://github.com/samarpan-aree/repolint/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%E2%80%93%203.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Dependencies](https://img.shields.io/badge/dependencies-zero-success)](pyproject.toml)

Most repositories fail for boring, fixable reasons: no license, a two-line README, no CI, no tests. `repolint` turns that into a number you can act on — and a gate you can enforce.

```
$ repolint .
  [PASS] README present (20 pts)      README.md found (4821 characters).
  [FAIL] License file (15 pts)        No LICENSE file found.
         fix: Add an OSI license (MIT or Apache-2.0).
  [FAIL] CI configuration (15 pts)    No CI configuration found.
         fix: Add .github/workflows/ci.yml.
  [PASS] Test suite (20 pts)          3 test file(s) detected.

Score: 70/100  grade C
```

Dependency-free and offline: reads the filesystem, never the network. Runs in any CI job in under a second.

## Install

```bash
pip install -e .        # or: python -m repolint .
```

## Usage

```bash
repolint [path] [--json] [--min-score N] [--no-colour] [--version]
```

| Option | Description |
| --- | --- |
| `path` | Repository to audit (default: cwd). |
| `--json` | Machine-readable output. |
| `--min-score N` | Exit `1` if score falls below `N`. |

```yaml
- name: Enforce repository quality
  run: pip install -e . && repolint . --min-score 80
```

## Checks

| Check | Weight | Fails when |
| --- | --- | --- |
| README present | 20 | Missing, or under 400 chars |
| Test suite | 20 | No `test_*.py` / `*.test.ts` / `*.spec.ts` |
| License file | 15 | No `LICENSE`, `LICENSE.md`, `COPYING` |
| CI configuration | 15 | No Actions, GitLab, Circle, Azure or Travis config |
| `.gitignore` | 10 | Missing, or under 3 real rules |
| Project description | 10 | No description in `pyproject.toml` / `package.json` |
| Directory structure | 10 | More than 12 loose files at root |

Grades: **A** ≥ 90, **B** ≥ 80, **C** ≥ 70, **D** ≥ 60, **F** below.

## Architecture

```
repolint/
├── repolint/
│   ├── __init__.py    # public API
│   ├── __main__.py    # python -m repolint
│   ├── checks.py      # 7 pure filesystem checks -> CheckResult
│   ├── scoring.py     # weighted aggregation -> ScoreReport
│   └── cli.py         # argparse, rendering, exit codes
└── tests/             # one class per check, tmp_path fixtures
```

- **`checks.py`** — every check is a pure `Path -> CheckResult`. No shared state, no ordering assumptions, so each is asserted in isolation against a fixture repo.
- **`scoring.py`** — filesystem-agnostic. Results in, weighted percentage and grade out. Rounding is half-up, so `89.5` becomes `90`.
- **`cli.py`** — presentation and process: arguments, ANSI colour, JSON, exit codes (`0` ok, `1` below threshold, `2` bad path).

Adding a check is one function appended to `ALL_CHECKS`; scoring and CLI pick it up automatically.

## Development

```bash
pip install -e ".[dev]"
pytest --cov=repolint --cov-report=term-missing
```

## Roadmap

- [ ] `--fix` mode scaffolding missing files
- [ ] Configurable weights via `.repolint.toml`
- [ ] Action wrapper commenting the score on PRs
- [ ] `--badge` emitting a shields.io endpoint payload

## License

MIT — see [LICENSE](LICENSE).
