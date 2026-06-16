# Pattern Schema

## Structure

A pattern pack is a YAML file (`.yaml` or `.yml`) containing a list of pattern definitions.

## Top-level

```yaml
patterns:
  - id: py-pattern-name
    title: "Human-readable title"
    language: Python | TypeScript | Go | Rust
    frameworks:
      - fastapi
      - sqlalchemy
    bug_type: resource_leak | sql_injection | auth_bypass | misconfiguration | ...
    severity_hint: low | medium | high | critical
    symptoms:
      - "Observable symptom 1"
    root_cause: "Description of the underlying cause"
    trigger_conditions:
      - description: "When this condition exists"
        code_signals:
          - "keyword"
          - "pattern"
    bad_code_signals:
      - "signal1"
      - "signal2"
    fix_patterns:
      - "Recommended fix 1"
    evidence:
      - repo: owner/repo
        issue: 123
        pr: 456
        commit: abc123
        url: https://github.com/owner/repo/issues/123
        strength: high | medium | low
    confidence: 0.75
    false_positive_boundary: "Description of when this pattern should NOT trigger"
```

## Required Fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | ✅ | Unique identifier (kebab-case) |
| `title` | ✅ | Human-readable title |
| `language` | ✅ | Programming language |
| `bug_type` | ✅ | Category of bug |
| `root_cause` | ✅ | Root cause description |
| `evidence` | ✅ | At least one OSS evidence entry |
| `confidence` | ✅ | Float between 0.0 and 1.0 |

## Optional but Recommended

| Field | Description |
|-------|-------------|
| `frameworks` | Frameworks this pattern applies to |
| `severity_hint` | Default severity for findings |
| `symptoms` | Observable symptoms in production |
| `trigger_conditions` | Conditions that must be met |
| `bad_code_signals` | Code patterns to match |
| `fix_patterns` | Recommended fixes |
| `false_positive_boundary` | When to suppress this pattern |
