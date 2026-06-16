# Mining Workflow

## Overview

IssueOracle mines bug patterns from real GitHub issues. Given a repository (`owner/repo`),
it searches for closed bug-labeled issues, filters for real bugs, links them to fixing PRs,
and extracts candidate bug patterns for human review.

## Flow

```
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
4. Write candidates to ~/.issueoracle/mining/<repo_date>/
  ↓
5. Human reviews review.md, approves/rejects candidates
  ↓
6. Approved candidates moved to packs/<language>/<framework>/
```

## Human Review Process

After mining, the candidate patterns are written to `~/.issueoracle/mining/`.
Each candidate is a structured YAML file. The human reviewer should:

1. Open `review.md` for a summary of all candidates
2. For each candidate:
   - Verify the issue is a real bug (not a misunderstanding)
   - Verify the linked PR actually fixes the issue
   - Verify the extracted signals and triggers make sense
   - Adjust confidence score (default 0.5)
   - Add/fix false_positive_boundary documentation
3. Move approved candidate to the appropriate `packs/` directory
4. Merge with existing patterns if the pack already has related patterns

## Safety

- Issue bodies are truncated to 2000 characters
- Prompt injection patterns are redacted
- Shell code blocks are redacted
- Only evidence URLs and metadata are stored (not full issue bodies)

## API Rate Limits

- Without `GITHUB_TOKEN`: 60 requests/hour (enough for small repos)
- With `GITHUB_TOKEN`: 5000 requests/hour (recommended)
