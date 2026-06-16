# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project skeleton with SKILL.md runtime contract.
- Python engine CLI (`issueoracle.py`) with `review`, `validate`, `diagnose`, and `mine` commands.
- Pydantic-validated bug pattern schema with Pattern/CandidatePattern/MiningResult models.
- Local pattern pack review pipeline (code_index, pattern_match, review, profile, pack_loader).
- GitHub Mining pipeline (github_search, github_fetch, issue_filter, evidence_linker, pattern_extract, safety).
- 7 built-in bug patterns (5 Python FastAPI + 2 TypeScript Express) with example code.
- Eval fixtures (10 bad/good pairs) and golden expected outputs.
- Eval runner and pattern evaluation tool.
- Comprehensive test suite (93+ tests) including integration tests.
- References: pattern schema, review report format, threat model, mining workflow.
- First-run wizard (nux-wizard.md).
- Windows compatibility (UTF-8 reconfigure).
