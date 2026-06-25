## Summary

<!-- Explain what this PR changes and why. -->

## Type of change

- [ ] Bug fix
- [ ] New bug pattern
- [ ] Documentation
- [ ] Refactor / maintenance
- [ ] Release / packaging

## Validation

- [ ] `uv run ruff format --check .`
- [ ] `uv run ruff check .`
- [ ] `uv run pytest tests/ -q`
- [ ] `uv run python skills/detectoracle/scripts/issueoracle.py validate skills/detectoracle/packs`
- [ ] `uv run python skills/detectoracle/evals/run_eval.py`
- [ ] `uv run python skills/detectoracle/scripts/build_skill.py`

## Pattern PR checklist

Complete this section only for new or changed bug patterns.

- [ ] Pattern YAML follows `skills/detectoracle/references/pattern-schema.md`
- [ ] Bad fixture added or updated
- [ ] Good fixture added or updated
- [ ] OSS evidence link included
- [ ] False-positive boundary documented
- [ ] Eval expectation added or updated

## Safety notes

- [ ] No secrets, tokens, private source code, or full private diffs are included
- [ ] GitHub issue / PR content is treated as untrusted input
- [ ] User-facing docs prefer DetectorOracle names, with IssueOracle only as a compatibility alias
