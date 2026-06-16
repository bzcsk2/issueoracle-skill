---
name: issueoracle
version: "0.2.1"
description: "Scan, mine, and review code using OSS bug patterns. Profile projects, batch-mine GitHub issues, and review local code with evidence."
argument-hint: "issueoracle scan . | issueoracle mine owner/repo,... | issueoracle review . --experience <path>"
allowed-tools: Bash, Read, Write, AskUserQuestion, WebSearch
homepage: https://github.com/bzcsk2/issueoracle-skill
repository: https://github.com/bzcsk2/issueoracle-skill
author: bzcsk2
license: MIT
user-invocable: true
metadata:
  openclaw:
    emoji: "🔮"
requires:
  env: []
optionalEnv:
  - GITHUB_TOKEN
  - ISSUEORACLE_ALLOW_REMOTE_LLM
  - ISSUEORACLE_HOME
bins:
  - python3
files:
  - "scripts/*"
  - "packs/*"
  - "references/*"
tags:
  - code-review
  - bug-patterns
  - github-issues
  - oss
  - static-analysis
  - local-first
  - ai-skill
  - project-scan
  - bug-experience
---

# IssueOracle Skill

You are inside the IssueOracle skill.

IssueOracle is a three-command local-first toolchain: **scan → mine → review**.

- **scan** profiles a local project and recommends 5 similar OSS projects.
- **mine** batch-extracts bug experiences from GitHub repos into a narrative markdown document.
- **review** uses seed patterns + optional experience document to find bugs in local code.

It must only report a finding when ALL of these exist:

1. A matched structured bug pattern.
2. Concrete local file/line evidence.
3. A plausible trigger condition.
4. A confidence score.
5. A false-positive boundary.
6. An OSS evidence link when the pattern came from public GitHub data.

Never claim code is buggy only because similar projects had similar issues.

## Pipeline

```text
scan ./my-project                     → project profile + 5 recommended repos
mine owner1/repo1,owner2/repo2,...    → ~/.issueoracle/bugplay/bug-experience.md
review ./my-project --experience ...  → findings driven by mined experience
```

## Runtime preflight

1. Resolve Python 3.12+.
2. Resolve SKILL_DIR from the loaded SKILL.md location.
3. Set ISSUEORACLE_HOME to ~/.issueoracle if unset.
4. Check git availability (for review --changed).
5. Check repo existence (for scan/review).
6. Do NOT upload local code to any remote LLM unless ISSUEORACLE_ALLOW_REMOTE_LLM=1.

## Intent parsing

Classify into: SCAN_PROJECT | REVIEW_REPO | REVIEW_DIFF | MINE_REPO | REVIEW_WITH_EXPERIENCE | VALIDATE_PACK | EXPLAIN_FINDING | HELP

## Commands

### SCAN_PROJECT

```bash
"$ISSUEORACLE_PYTHON" "$SKILL_DIR/scripts/issueoracle.py" scan "$TARGET_REPO" --emit markdown
```

### REVIEW_REPO

```bash
"$ISSUEORACLE_PYTHON" "$SKILL_DIR/scripts/issueoracle.py" review "$TARGET_REPO" --emit markdown
```

### REVIEW_DIFF

```bash
"$ISSUEORACLE_PYTHON" "$SKILL_DIR/scripts/issueoracle.py" review "$TARGET_REPO" --changed --base main --emit markdown
```

### REVIEW_WITH_EXPERIENCE

```bash
"$ISSUEORACLE_PYTHON" "$SKILL_DIR/scripts/issueoracle.py" review "$TARGET_REPO" --experience "$EXPERIENCE_PATH" --emit markdown
```

### MINE_REPO

```bash
"$ISSUEORACLE_PYTHON" "$SKILL_DIR/scripts/issueoracle.py" mine "$OWNER_REPOS" --human-review --emit markdown
```

### VALIDATE_PACK

```bash
"$ISSUEORACLE_PYTHON" "$SKILL_DIR/scripts/issueoracle.py" validate "$PACK_PATH" --emit markdown
```

## Output contract

Final response must contain: review scope, patterns considered, files scanned, findings grouped by severity, and per-finding: file/line, confidence, matched pattern, trigger condition, local evidence, OSS evidence, suggested fix, validation test, false-positive boundary.

Do NOT output low-confidence findings by default.
Do NOT output findings without line evidence.
Do NOT output raw GitHub issue bodies or full PR diffs.
