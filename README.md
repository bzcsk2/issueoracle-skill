[English](README.md) | [中文](README.zh.md)

# IssueOracle Skill

Mine bug patterns from fixed GitHub issues, then review local code with concrete evidence.

## Install

### Recommended: Agent Skills CLI

Global user install:

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

### Manual install for Codex

```bash
git clone https://github.com/bzcsk2/issueoracle-skill.git
mkdir -p ~/.codex/skills
ln -s "$(pwd)/issueoracle-skill/skills/issueoracle" ~/.codex/skills/issueoracle
```

### Build local .skill

```bash
uv sync --all-groups
uv run python skills/issueoracle/scripts/build_skill.py
```

Generated: `dist/issueoracle.skill`

## Quick Start

```bash
# Scan a project → get profile + similar OSS recommendations
/issueoracle scan .

# Review current repo
/issueoracle review .

# Review with bug experience doc
/issueoracle review . --experience ~/.issueoracle/bugplay/bug-experience.md

# Mine bug patterns from GitHub repos (comma-separated)
/issueoracle mine fastapi/fastapi,encode/starlette

# Validate pattern packs
/issueoracle validate packs
```

## Pipeline

```text
scan ./my-project                     → project profile + 5 recommended repos
mine owner1/repo1,owner2/repo2,...    → ~/.issueoracle/bugplay/bug-experience.md
review ./my-project --experience ...  → findings driven by mined experience
```

## Usage

### Scan a project

```bash
/issueoracle scan . --emit markdown
/issueoracle scan src/ --emit json --max-repos 3
```

Output includes: language/framework detection, risk surface analysis, project type classification (`web_api` / `cli` / `library` / `frontend`), and 5 similar OSS projects ranked by stars.

### Review local code

```bash
# Full review
/issueoracle review .
# Diff review (changed vs base)
/issueoracle review . --changed --base main
# JSON output
/issueoracle review src/ --emit json
# Experience-driven review
/issueoracle review . --experience ~/.issueoracle/bugplay/bug-experience.md
```

### Mine bug patterns from GitHub

```bash
# Single repo
/issueoracle mine fastapi/fastapi
# Batch mine
/issueoracle mine fastapi/fastapi,encode/starlette,sqlalchemy/sqlalchemy --max-issues 30
```

Mined experiences are saved to `~/.issueoracle/bugplay/bug-experience.md`.

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
uv sync
uv run pytest tests/ -q
uv run python skills/issueoracle/scripts/issueoracle.py diagnose
uv run python skills/issueoracle/evals/run_eval.py
```

## How it works

1. **Scan**: Profile local project, classify project type, infer GitHub search topics, and recommend 5 similar OSS projects.
2. **Mine**: Batch-search closed bug issues on GitHub, filter for real bugs, link to fixing PRs, extract candidate bug patterns, and aggregate into a narrative bug-experience document.
3. **Review**: Load seed patterns + optional experience document, index local code, match signals, and generate findings with evidence.

## Requirements

- Python 3.12+
- `GITHUB_TOKEN` (optional, for higher API rate limits)

## License

MIT
