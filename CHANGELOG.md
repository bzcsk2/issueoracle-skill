# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Renamed public project identity from IssueOracle to DetectorOracle.
- Updated install commands, README files, skill metadata, security policy, and contribution guide to use `detectoracle-skill` and `/detectoracle`.
- Renamed the generated bundle from `issueoracle.skill` to `detectoracle.skill`.
- Added `DETECTORACLE_*` configuration aliases while retaining `ISSUEORACLE_*` compatibility for existing users.
- Documented the rename migration policy in `docs/RENAME_MIGRATION.md`.

### Added
- Initial project skeleton with SKILL.md runtime contract.
- Python engine CLI (`issueoracle.py`) with `review`, `validate`, `diagnose`, and `mine` commands.
- Pydantic-validated bug pattern schema with Pattern/CandidatePattern/MiningResult models.
- Local pattern pack review pipeline (code_index, pattern_match, review, profile, pack_loader).
- GitHub Mining pipeline (github_search, github_fetch, issue_filter, evidence_linker, pattern_extract, safety).
- Built-in bug patterns with example code and eval fixtures.
- Eval runner and pattern evaluation tool.
- Comprehensive test suite including integration tests.
- References: pattern schema, review report format, threat model, mining workflow.
- First-run wizard (nux-wizard.md).
- Windows compatibility (UTF-8 reconfigure).
