# IssueOracle First-Run Setup

Welcome to IssueOracle! This wizard runs once to configure your environment.

## Prerequisites

- **Python 3.12+** — verify with `python3 --version`
- **uv** — verify with `uv --version`; install with `pip install uv` if missing

## Steps

### 1. GitHub Token (Optional)

IssueOracle uses the public GitHub API by default (60 req/hr). For production use, set a token:

```bash
# Personal Access Token (no scopes needed for public repos)
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

Add it to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) or `.env`.

### 2. Local-First Strategy

IssueOracle stores mined patterns, experience data, and review history locally:

```
~/.issueoracle/
  store/
  experience/
```

No data leaves your machine unless you explicitly run `scan` (GitHub API calls).

### 3. Verify Installation

```bash
issueoracle doctor
```

Expected output: all checks pass (Python, skill dir, packs, git, etc.)

## Configuration

Edit `~/.config/issueoracle/.env`:

```env
SETUP_COMPLETE=true
ISSUEORACLE_HOME=~/.issueoracle
ISSUEORACLE_ALLOW_REMOTE_LLM=0
```

## Next Steps

- `issueoracle review <repo-path>` — review a repository
- `issueoracle scan <owner/repo>` — find similar issues on GitHub
- `issueoracle diagnose` — system diagnostics
