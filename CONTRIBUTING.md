# Contributing to DetectorOracle

DetectorOracle is a community-driven bug-pattern library and local-first review skill. Every high-quality pattern improves evidence-based code review for everyone.

## Quick Start

```bash
git clone https://github.com/bzcsk2/detectoracle-skill.git
cd detectoracle-skill
uv sync --all-groups
uv run pytest tests/ -q
```

## How to Contribute

### Adding a Bug Pattern

This is the most valuable contribution. A good pattern is one that:

1. **Comes from a real OSS bug** — link to the GitHub issue, PR, or commit where the bug was reported and fixed.
2. **Has structured evidence** — include repo, issue/PR number when available, and a durable GitHub URL.
3. **Has code examples** — provide both a `bad` example that triggers the pattern and a `good` example that should not.
4. **Passes validation** — your pattern must pass the built-in validator.
5. **Passes eval** — the bad fixture should trigger the pattern and the good fixture should remain clean.

#### Pattern Requirements

Every pattern PR must include:

- **1 pattern YAML** following the schema in [`skills/issueoracle/references/pattern-schema.md`](skills/issueoracle/references/pattern-schema.md)
- **1 bad fixture** in `skills/issueoracle/evals/fixtures/<pattern-id>/bad/`
- **1 good fixture** in `skills/issueoracle/evals/fixtures/<pattern-id>/good/`
- **1 OSS evidence link** with a real GitHub issue/PR/commit URL
- **validate pass**: `uv run python skills/issueoracle/scripts/issueoracle.py validate skills/issueoracle/packs`
- **eval pass**: `uv run python skills/issueoracle/evals/run_eval.py`

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
| Bad fixture triggers the pattern | ✅ |
| Good fixture does not trigger the pattern | ✅ |

### Submitting a PR

1. Fork the repo and create a feature branch.
2. Add your pattern YAML to the appropriate `skills/issueoracle/packs/<language>/<framework>/` directory.
3. Add eval fixtures to `skills/issueoracle/evals/fixtures/<pattern-id>/bad/` and `skills/issueoracle/evals/fixtures/<pattern-id>/good/`.
4. Add or update a golden expected file when the eval harness requires it.
5. Run `uv run pytest tests/ -q` and ensure all tests pass.
6. Run `uv run python skills/issueoracle/scripts/issueoracle.py validate skills/issueoracle/packs`.
7. Open a PR with a clear title describing the pattern, for example `Add py-django-raw-sql-injection pattern`.

### Merge Criteria

A pattern PR is merged when all of these are true:

- [ ] 1 pattern YAML with all required fields
- [ ] 1 bad fixture that triggers the pattern
- [ ] 1 good fixture that does not trigger the pattern
- [ ] 1 OSS evidence link from a real GitHub issue, PR, or commit
- [ ] `validate` passes
- [ ] eval passes for both bad and good fixtures
- [ ] no decrease in overall eval quality

## Development Setup

```bash
# Install dependencies
uv sync --all-groups

# Run tests
uv run pytest tests/ -q

# Validate all packs
uv run python skills/issueoracle/scripts/issueoracle.py validate skills/issueoracle/packs

# Run evals
uv run python skills/issueoracle/evals/run_eval.py

# Run with debug logging
DETECTORACLE_DEBUG=1 uv run python skills/issueoracle/scripts/issueoracle.py review . --emit markdown
```

## Rename Compatibility

The public name is DetectorOracle, but some internal paths still contain `issueoracle` during the migration window. Do not rename directories piecemeal. A full path migration should happen in one dedicated PR with compatibility tests and release notes.

## Code Style

- Python 3.12+ features are allowed.
- Use `pydantic` for all structured data models.
- Use `from __future__ import annotations` in all modules.
- All logs go to stderr. Only final reports go to stdout.
- `lib/__init__.py` must remain empty.

## Questions

Open a GitHub issue or discussion in `bzcsk2/detectoracle-skill` for questions about pattern design, scope, or contribution process.
