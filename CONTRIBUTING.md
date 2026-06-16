# Contributing to IssueOracle

Thank you for contributing! IssueOracle is a community-driven bug pattern library. Every pattern makes code review better for everyone.

## Quick Start

```bash
git clone https://github.com/bzcsk2/issueoracle-skill.git
cd issueoracle-skill
uv sync
python3 -m pytest tests/ -q
```

## How to Contribute

### Adding a Bug Pattern

This is the most valuable contribution. A good pattern is one that:

1. **Comes from a real OSS bug** — Link to the GitHub issue, PR, or commit where the bug was reported and fixed.
2. **Has structured evidence** — Include the OSS evidence link with repo, issue number, and URL.
3. **Has code examples** — Provide both a `bad` example (showing the bug) and a `good` example (showing the fix).
4. **Passes validation** — Your pattern must pass `issueoracle validate`.
5. **Passes eval** — Your examples must pass the eval suite (bad triggers the pattern, good does not).

#### Pattern Requirements

Every pattern PR must include:

- **1 pattern YAML** following the schema in [`references/pattern-schema.md`](skills/issueoracle/references/pattern-schema.md)
- **1 bad example** in `examples/<pattern-id>.bad.<ext>`
- **1 good example** in `examples/<pattern-id>.good.<ext>`
- **1 OSS evidence link** with a real GitHub issue/PR URL
- **validate pass**: `python3 skills/issueoracle/scripts/issueoracle.py validate skills/issueoracle/packs`
- **eval pass**: `python3 skills/issueoracle/evals/run_eval.py`

#### Pattern Quality Bar

| Criteria | Required |
|----------|----------|
| Pattern YAML passes schema validation | ✅ |
| Has `evidence` with at least one real GitHub URL | ✅ |
| `confidence` is between 0.0 and 1.0 | ✅ |
| `trigger_conditions` is non-empty | ✅ |
| `bad_code_signals` is non-empty | ✅ |
| `fix_patterns` is non-empty | ✅ |
| `false_positive_boundary` is documented | ✅ |
| Bad example triggers the pattern | ✅ |
| Good example does not trigger the pattern | ✅ |

### Submitting a PR

1. Fork the repo and create a feature branch.
2. Add your pattern YAML + examples to the appropriate `packs/<language>/<framework>/` directory.
3. Add eval fixtures to `evals/fixtures/<pattern-id>/bad/` and `evals/fixtures/<pattern-id>/good/`.
4. Add a golden expected file to `evals/golden/<pattern-id>.expected.json`.
5. Run `python3 -m pytest tests/ -q` and ensure all tests pass.
6. Run `python3 skills/issueoracle/scripts/issueoracle.py validate skills/issueoracle/packs`.
7. Open a PR with a clear title describing the pattern (e.g., "Add py-django-raw-sql-injection pattern").

### Merge Criteria

A pattern PR is merged when all of these are true:

- [ ] 1 pattern YAML with all required fields
- [ ] 1 bad example that triggers the pattern
- [ ] 1 good example that does not trigger the pattern
- [ ] 1 OSS evidence link (real GitHub issue/PR URL)
- [ ] `validate` pass
- [ ] `eval` pass (both bad and good fixtures)
- [ ] No decrease in overall eval metrics

## Development Setup

```bash
# Install dependencies
uv sync

# Run tests
python3 -m pytest tests/ -q

# Run a single test
python3 -m pytest tests/test_schema.py::PatternTests::test_roundtrip -q

# Validate all packs
python3 skills/issueoracle/scripts/issueoracle.py validate skills/issueoracle/packs

# Run evals
python3 skills/issueoracle/evals/run_eval.py

# Run with debug logging
ISSUEORACLE_DEBUG=1 python3 skills/issueoracle/scripts/issueoracle.py review . --emit markdown
```

## Code Style

- Python 3.12+ features are allowed (type parameter syntax, etc.).
- Use `pydantic` for all structured data models.
- Use `from __future__ import annotations` in all modules.
- All logs go to stderr. Only final report goes to stdout.
- `lib/__init__.py` must remain empty.

## Questions?

Open a [GitHub Discussion](https://github.com/bzcsk2/issueoracle-skill/discussions) for questions about pattern design, scope, or contribution process.
