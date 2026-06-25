[English](README.md) | [中文](README.zh.md)

# DetectorOracle Skill

![CI](https://github.com/bzcsk2/detectoracle-skill/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Agent Skill](https://img.shields.io/badge/agent-skill-purple)

DetectorOracle is an agent skill that turns fixed OSS issues into reusable bug-detection patterns, then reviews local code with concrete file/line evidence.

DetectorOracle is not a generic linter and not a generic AI reviewer. It is a local-first bug-pattern review toolchain built around **scan → mine → review**.

## Rename status

This repository was renamed from IssueOracle to DetectorOracle. Public documentation, install commands, the skill name, and generated bundle now use **DetectorOracle**. The internal Python entrypoint currently remains `skills/detectoracle/scripts/issueoracle.py` for compatibility while the migration settles.

## Install

### Recommended: Agent Skills CLI

Global install:

```bash
npx skills add bzcsk2/detectoracle-skill -g
```

Project-scoped install:

```bash
npx skills add bzcsk2/detectoracle-skill
```

Update:

```bash
npx skills update detectoracle
```

### Claude Code marketplace

Planned. Until DetectorOracle is accepted into a marketplace, use `npx skills add`.

### Manual install for Claude Code

```bash
git clone https://github.com/bzcsk2/detectoracle-skill.git
mkdir -p ~/.claude/skills
ln -s "$(pwd)/detectoracle-skill/skills/detectoracle" ~/.claude/skills/detectoracle
```

### Manual install for Codex-style skill directories

```bash
git clone https://github.com/bzcsk2/detectoracle-skill.git
mkdir -p ~/.codex/skills
ln -s "$(pwd)/detectoracle-skill/skills/detectoracle" ~/.codex/skills/detectoracle
```

### Build local `.skill` bundle

```bash
uv sync --all-groups
uv run python skills/detectoracle/scripts/build_skill.py
```

Generated artifact:

```text
dist/detectoracle.skill
```

## Quick Start

```bash
# Scan a project → get profile + similar OSS recommendations
/detectoracle scan .

# Review current repo with built-in seed patterns
/detectoracle review .

# Mine bug patterns from GitHub repos (comma-separated)
/detectoracle mine fastapi/fastapi,encode/starlette

# Review with the generated experience JSON
/detectoracle review . --experience ~/.detectoracle/bugplay/experience.json

# Validate pattern packs
/detectoracle validate packs
```

## 30-second local demo

```bash
git clone https://github.com/bzcsk2/detectoracle-skill
cd detectoracle-skill
uv sync --all-groups
uv run python skills/detectoracle/scripts/issueoracle.py review skills/detectoracle/evals/fixtures/py-fastapi-cors-wildcard/bad --emit markdown
```

Expected output includes a finding with:

```text
- file/line evidence
- matched pattern id
- confidence score
- local trigger condition
- suggested fix
- false-positive boundary
```

## Pipeline

```text
scan ./my-project                     → project profile + recommended repos
mine owner1/repo1,owner2/repo2,...    → ~/.detectoracle/bugplay/experience.json + bug-experience.md
review ./my-project --experience ...  → findings driven by seed patterns + mined experience
```

## Usage

### Scan a project

```bash
/detectoracle scan . --emit markdown
/detectoracle scan src/ --emit json --max-repos 3
```

Output includes language/framework detection, risk surface analysis, project type classification (`web_api` / `cli` / `library` / `frontend`), and similar OSS projects ranked by stars.

### Review local code

```bash
# Full review
/detectoracle review .

# Diff review (changed vs base)
/detectoracle review . --changed --base main

# JSON output
/detectoracle review src/ --emit json

# Experience-driven review. Prefer JSON as the machine-readable contract.
/detectoracle review . --experience ~/.detectoracle/bugplay/experience.json
```

A finding is only reported when DetectorOracle has a matched bug pattern, concrete local file/line evidence, a trigger condition, a confidence score, and a false-positive boundary.

### Mine bug patterns from GitHub

```bash
# Single repo
/detectoracle mine fastapi/fastapi

# Batch mine
/detectoracle mine fastapi/fastapi,encode/starlette,sqlalchemy/sqlalchemy --max-issues 30
```

Mined experiences are saved to `~/.detectoracle/bugplay/experience.json` for the review engine and `~/.detectoracle/bugplay/bug-experience.md` as a narrative document organized by bug type.

Resume an interrupted mining session:

```bash
/detectoracle mine fastapi/fastapi,encode/starlette --resume --max-issues 30
```

### Manage bug experiences

```bash
# List all bug experiences (candidate + approved + rejected)
/detectoracle experience list

# Show details of a specific experience
/detectoracle experience show exp-missing-finally-1

# Approve a candidate experience for use in review
/detectoracle experience approve exp-missing-finally-1

# Reject a false-positive experience
/detectoracle experience reject exp-missing-finally-1

# Export only approved experiences for shared use
/detectoracle experience export-approved
```

### Validate packs

```bash
/detectoracle validate packs
/detectoracle validate packs --emit json
```

### Diagnose

```bash
/detectoracle diagnose
```

### Doctor

```bash
/detectoracle doctor
```

## Development

```bash
uv sync --all-groups
uv run ruff format --check .
uv run ruff check .
uv run pytest tests/ -q
uv run python skills/detectoracle/scripts/issueoracle.py diagnose
uv run python skills/detectoracle/evals/run_eval.py
uv run python skills/detectoracle/scripts/issueoracle.py validate skills/detectoracle/packs
uv run python skills/detectoracle/scripts/build_skill.py
```

## How it works

1. **Scan**: Profile local project, classify project type, infer GitHub search topics, and recommend similar OSS projects.
2. **Mine**: Batch-search closed bug issues on GitHub, filter for real bugs, link to fixing PRs, extract candidate bug patterns, and aggregate into a bug-experience report.
3. **Review**: Load seed patterns plus optional experience JSON, index local code, match signals, and generate findings with evidence.

## Safety model

- Local code stays local by default.
- GitHub issue and PR text is treated as untrusted input.
- DetectorOracle does not auto-fix code, create commits, or open PRs.
- Pattern packs store structured evidence links and summaries, not bulk source material.
- `DETECTORACLE_ALLOW_REMOTE_LLM=1` is required before any remote LLM usage is permitted.

## Requirements

- Python 3.12+
- `GITHUB_TOKEN` optional, for higher GitHub API rate limits

## License

MIT
