[English](README.md) | [中文](README.zh.md)

# IssueOracle Skill

![CI](https://github.com/bzcsk2/issueoracle-skill/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Agent Skill](https://img.shields.io/badge/agent-skill-purple)

Agent Skill that turns fixed OSS issues into reusable bug patterns, then reviews local code with concrete file/line evidence.

IssueOracle is not a generic linter and not a general AI reviewer. It is a local-first bug-pattern review toolchain built around **scan → mine → review**.

## Install

### Recommended: Agent Skills CLI

Global install:

```bash
npx skills add bzcsk2/issueoracle-skill -g
```

Project-scoped install:

```bash
npx skills add bzcsk2/issueoracle-skill
```

Update:

```bash
npx skills update issueoracle
```

### Claude Code marketplace

Planned. Until IssueOracle is accepted into marketplace, use `npx skills add`.

### Manual install for Claude Code

```bash
git clone https://github.com/bzcsk2/issueoracle-skill.git
mkdir -p ~/.claude/skills
ln -s "$(pwd)/issueoracle-skill/skills/issueoracle" ~/.claude/skills/issueoracle
```

### Manual install for Codex-style skill directories

```bash
git clone https://github.com/bzcsk2/issueoracle-skill.git
mkdir -p ~/.codex/skills
ln -s "$(pwd)/issueoracle-skill/skills/issueoracle" ~/.codex/skills/issueoracle
```

### Build local `.skill` bundle

```bash
uv sync --all-groups
uv run python skills/issueoracle/scripts/build_skill.py
```

Generated artifact:

```text
dist/issueoracle.skill
```

## Quick Start

```bash
# Scan a project → get profile + similar OSS recommendations
/issueoracle scan .

# Review current repo with built-in seed patterns
/issueoracle review .

# Mine bug patterns from GitHub repos (comma-separated)
/issueoracle mine fastapi/fastapi,encode/starlette

# Review with the generated experience JSON
/issueoracle review . --experience ~/.issueoracle/bugplay/experience.json

# Validate pattern packs
/issueoracle validate packs
```

## 30-second local demo

```bash
git clone https://github.com/bzcsk2/issueoracle-skill
cd issueoracle-skill
uv sync --all-groups
uv run python skills/issueoracle/scripts/issueoracle.py review skills/issueoracle/evals/fixtures/py-fastapi-cors-wildcard/bad --emit markdown
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
mine owner1/repo1,owner2/repo2,...    → ~/.issueoracle/bugplay/experience.json + bug-experience.md
review ./my-project --experience ...  → findings driven by seed patterns + mined experience
```

## Usage

### Scan a project

```bash
/issueoracle scan . --emit markdown
/issueoracle scan src/ --emit json --max-repos 3
```

Output includes language/framework detection, risk surface analysis, project type classification (`web_api` / `cli` / `library` / `frontend`), and similar OSS projects ranked by stars.

### Review local code

```bash
# Full review
/issueoracle review .

# Diff review (changed vs base)
/issueoracle review . --changed --base main

# JSON output
/issueoracle review src/ --emit json

# Experience-driven review. Prefer JSON as the machine-readable contract.
/issueoracle review . --experience ~/.issueoracle/bugplay/experience.json
```

A finding is only reported when IssueOracle has a matched bug pattern, concrete local file/line evidence, a trigger condition, a confidence score, and a false-positive boundary.

### Mine bug patterns from GitHub

```bash
# Single repo
/issueoracle mine fastapi/fastapi

# Batch mine
/issueoracle mine fastapi/fastapi,encode/starlette,sqlalchemy/sqlalchemy --max-issues 30
```

Mined experiences are saved to `~/.issueoracle/bugplay/experience.json` for the review engine and `~/.issueoracle/bugplay/bug-experience.md` as a narrative document organized by bug type.

Resume an interrupted mining session:

```bash
/issueoracle mine fastapi/fastapi,encode/starlette --resume --max-issues 30
```

### Manage bug experiences

```bash
# List all bug experiences (candidate + approved + rejected)
/issueoracle experience list

# Show details of a specific experience
/issueoracle experience show exp-missing-finally-1

# Approve a candidate experience for use in review
/issueoracle experience approve exp-missing-finally-1

# Reject a false-positive experience
/issueoracle experience reject exp-missing-finally-1

# Export only approved experiences for shared use
/issueoracle experience export-approved
```

### Validate packs

```bash
/issueoracle validate packs
/issueoracle validate packs --emit json
```

### Diagnose

```bash
/issueoracle diagnose
```

### Doctor

```bash
/issueoracle doctor
```

## Development

```bash
uv sync --all-groups
uv run ruff format --check .
uv run ruff check .
uv run pytest tests/ -q
uv run python skills/issueoracle/scripts/issueoracle.py diagnose
uv run python skills/issueoracle/evals/run_eval.py
uv run python skills/issueoracle/scripts/issueoracle.py validate skills/issueoracle/packs
uv run python skills/issueoracle/scripts/build_skill.py
```

## How it works

1. **Scan**: Profile local project, classify project type, infer GitHub search topics, and recommend similar OSS projects.
2. **Mine**: Batch-search closed bug issues on GitHub, filter for real bugs, link to fixing PRs, extract candidate bug patterns, and aggregate into a bug-experience report.
3. **Review**: Load seed patterns plus optional experience JSON, index local code, match signals, and generate findings with evidence.

## Safety model

- Local code stays local by default.
- GitHub issue and PR text is treated as untrusted input.
- IssueOracle does not auto-fix code, create commits, or open PRs.
- Pattern packs store structured evidence links and summaries, not bulk source material.

## Requirements

- Python 3.12+
- `GITHUB_TOKEN` optional, for higher GitHub API rate limits

## License

MIT
