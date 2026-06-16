# Review Report Format

IssueOracle outputs findings grouped by severity. Each finding includes:

## Per-finding Fields

| Field | Description | Always Present |
|-------|-------------|----------------|
| `id` | Unique finding ID | ✅ |
| `severity` | low/medium/high/critical | ✅ |
| `confidence` | 0.0–1.0 | ✅ |
| `file` | Absolute or relative file path | ✅ |
| `start_line` | Line number (1-indexed) | ✅ |
| `end_line` | End line number | ✅ |
| `title` | Finding title | ✅ |
| `matched_pattern` | Pattern ID that matched | ✅ |
| `trigger_condition` | What triggered the match | ✅ |
| `local_evidence` | List of {line, description} | ✅ |
| `oss_evidence` | List of {repo, issue, pr, commit, url, strength} | If pattern from OSS |
| `suggested_fix` | Recommended fix description | ✅ |
| `validation` | How to validate the fix | ✅ |
| `false_positive_boundary` | When this finding may be wrong | ✅ |

## Output Formats

### Markdown (default)

Human-readable with headings, bullet lists, and evidence links.

### JSON

Machine-readable structured output with the full `ReviewReport` schema.

### Compact

One-line-per-finding for quick scanning: `[severity] file:line (confidence) title`
