# DetectorOracle First-Run Setup

Welcome to DetectorOracle. This wizard runs once to configure your environment.

## Prerequisites

- **Python 3.12+** — verify with `python3 --version`
- **uv** — verify with `uv --version`; install with `pip install uv` if missing

## Steps

### 1. GitHub Token (Optional)

DetectorOracle uses the public GitHub API by default (60 req/hr). For production use, set a token:

```bash
# Personal Access Token; no scopes are needed for public repos
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

Add it to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) or `.env`.

### 2. Local-First Strategy

DetectorOracle stores mined patterns, experience data, and review history locally:

```text
~/.detectoracle/
  reports/
  cache/
  mining/
  bugplay/
```

Existing `~/.issueoracle` data is accepted as a legacy fallback during the rename migration.

No local source code leaves your machine unless you explicitly enable a remote workflow. GitHub metadata requests are made when you run `scan` or `mine`.

### 3. Verify Installation

```bash
detectoracle doctor
```

Expected output: all checks pass (Python, skill dir, packs, git, etc.).

## Configuration

Edit `~/.config/detectoracle/.env`:

```env
SETUP_COMPLETE=true
DETECTORACLE_HOME=~/.detectoracle
DETECTORACLE_ALLOW_REMOTE_LLM=0
```

Legacy `ISSUEORACLE_HOME` and `ISSUEORACLE_ALLOW_REMOTE_LLM` are still accepted for migrated installations.

## Next Steps

- `detectoracle review <repo-path>` — review a repository
- `detectoracle scan <repo-path>` — profile a local project and recommend similar OSS repos
- `detectoracle mine <owner/repo>` — mine bug patterns from GitHub
- `detectoracle diagnose` — system diagnostics
