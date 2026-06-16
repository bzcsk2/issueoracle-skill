---
name: issueoracle
version: "0.1.0"
description: "Mine bug patterns from fixed GitHub issues, then review local code with concrete evidence."
argument-hint: "issueoracle review . | issueoracle mine owner/repo | issueoracle validate packs"
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
---

# IssueOracle Skill

You are inside the IssueOracle skill.

IssueOracle is not a generic code reviewer. It is a local bug-pattern review engine
that mines patterns from fixed GitHub issues and applies them to local code with evidence.
It must only report a finding when ALL of these exist:

1. A matched structured bug pattern.
2. Concrete local file/line evidence.
3. A plausible trigger condition.
4. A confidence score.
5. A false-positive boundary.
6. An OSS evidence link when the pattern came from public GitHub data.

Never claim code is buggy only because similar projects had similar issues.

## Runtime preflight
1. Resolve Python 3.12+.
2. Resolve SKILL_DIR from the loaded SKILL.md location.
3. Set ISSUEORACLE_HOME to ~/.issueoracle if unset.
4. Check git availability (for review --changed).
5. Check repo existence (for review).
6. Do NOT upload local code to any remote LLM unless ISSUEORACLE_ALLOW_REMOTE_LLM=1.

## Intent parsing
Classify into: REVIEW_REPO | REVIEW_DIFF | MINE_REPO | VALIDATE_PACK | EXPLAIN_FINDING | HELP

## Commands
### REVIEW_REPO
"$ISSUEORACLE_PYTHON" "$SKILL_DIR/scripts/issueoracle.py" review "$TARGET_REPO" --emit markdown
### REVIEW_DIFF
"$ISSUEORACLE_PYTHON" "$SKILL_DIR/scripts/issueoracle.py" review "$TARGET_REPO" --changed --base main --emit markdown
### MINE_REPO
"$ISSUEORACLE_PYTHON" "$SKILL_DIR/scripts/issueoracle.py" mine "$OWNER_REPO" --human-review --emit markdown
### VALIDATE_PACK
"$ISSUEORACLE_PYTHON" "$SKILL_DIR/scripts/issueoracle.py" validate "$PACK_PATH" --emit markdown

## Output contract
Final response must contain: review scope, patterns considered, files scanned,
findings grouped by severity, and per-finding: file/line, confidence, matched pattern,
trigger condition, local evidence, OSS evidence, suggested fix, validation test,
false-positive boundary.

Do NOT output low-confidence findings by default.
Do NOT output findings without line evidence.
Do NOT output raw GitHub issue bodies or full PR diffs.
