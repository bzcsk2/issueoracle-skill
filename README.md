# IssueOracle Skill

Mine bug patterns from fixed GitHub issues, then review local code with concrete evidence.

## Quick Start

```bash
# Install
npx skills add bzcsk2/issueoracle-skill -g

# Review current repo
/issueoracle review .

# Mine bug patterns from a GitHub repo
/issueoracle mine fastapi/fastapi

# Validate pattern packs
/issueoracle validate packs
```

## Usage

### Review local code

```bash
/issueoracle review .
/issueoracle review src/ --emit json
/issueoracle review . --changed --base main
```

### Mine bug patterns from GitHub

```bash
/issueoracle mine fastapi/fastapi
/issueoracle mine tiangolo/fastapi --max-issues 30 --emit json
```

Mined candidate patterns are saved to `~/.issueoracle/mining/` for human review.
Move approved candidates to `packs/` after reviewing.

### Validate packs

```bash
/issueoracle validate packs
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
```

## How it works

1. **Mine**: Search closed bug issues on GitHub, filter for real bugs, link to fixing PRs, and extract candidate bug patterns.
2. **Review**: Load pattern packs, index local code, match signals, and generate findings with evidence.
3. **Validate**: Verify pattern pack structure and schema compliance.

## Requirements

- Python 3.12+
- `GITHUB_TOKEN` (optional, for higher API rate limits)

## License

MIT
