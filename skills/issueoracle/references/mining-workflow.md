# Mining Workflow

## Overview

DetectorOracle mines bug patterns from real GitHub issues. Given one or more repositories (`owner/repo`), it searches for closed bug-labeled issues, filters for real bugs, links them to fixing PRs, and extracts candidate bug patterns for human review.

## Flow

```text
mine owner/repo
  ↓
1. Search closed issues with label:bug
  ↓
2. Filter non-bug issues (questions, docs, features, etc.)
  ↓
3. For each bug issue:
   a. Find linked PRs via timeline cross-references
   b. Build evidence chain (issue → PR → commit)
   c. Extract candidate pattern (root cause, signals, fix)
  ↓
4. Write candidates to ~/.detectoracle/bugplay/candidates/
  ↓
5. Human reviews candidates and approves/rejects them
  ↓
6. Approved experiences can be exported or moved into packs/<language>/<framework>/
```

## Human Review Process

After mining, the candidate patterns are written to `~/.detectoracle/bugplay/`. Existing `~/.issueoracle/bugplay/` data is accepted as a legacy fallback during the rename migration.

The human reviewer should:

1. Inspect each candidate experience.
2. Verify the issue is a real bug, not a misunderstanding or support request.
3. Verify the linked PR actually fixes the issue.
4. Verify the extracted signals and triggers make sense.
5. Adjust confidence score when needed.
6. Add or fix `false_positive_boundary` documentation.
7. Approve strong candidates before using them in default review.

## Safety

- Issue bodies are truncated.
- Prompt injection patterns are redacted.
- Shell code blocks are redacted.
- Only evidence URLs and metadata are stored, not full issue bodies.
- Candidate experiences are not trusted by default.

## API Rate Limits

- Without `GITHUB_TOKEN`: 60 requests/hour, enough for small repos.
- With `GITHUB_TOKEN`: 5000 requests/hour, recommended for production use.
