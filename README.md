# IssueOracle Skill

Mine bug patterns from fixed GitHub issues, then review local code with concrete evidence.
v0.2 adds three-command pipeline: **scan → mine → review**.

## Quick Start

```bash
# Install
npx skills add bzcsk2/issueoracle-skill -g

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

Mined experiences are saved to `~/.issueoracle/bugplay/bug-experience.md` as a narrative document organized by bug type. Each entry includes: symptom → root cause → trigger condition → bad code signals → fix → evidence.

### Validate packs

```bash
/issueoracle validate packs
/issueoracle validate packs --emit json
```

### Diagnose

```bash
/issueoracle diagnose
```

## Development

```bash
uv sync
python3 -m pytest tests/ -q
python3 skills/issueoracle/scripts/issueoracle.py diagnose
python3 skills/issueoracle/evals/run_eval.py
```

## How it works

1. **Scan**: Profile local project (languages, frameworks, dependencies, risk surfaces), classify project type, infer GitHub search topics, and recommend 5 similar OSS projects.
2. **Mine**: Batch-search closed bug issues on GitHub, filter for real bugs, link to fixing PRs, extract candidate bug patterns, and aggregate into a narrative bug-experience markdown document.
3. **Review**: Load seed patterns + optional experience document, index local code, match signals, and generate findings with evidence.

## Requirements

- Python 3.12+
- `GITHUB_TOKEN` (optional, for higher API rate limits)

## License

MIT
