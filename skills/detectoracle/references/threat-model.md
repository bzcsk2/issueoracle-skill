# Threat Model

## Attack Surfaces

1. **GitHub Issue/PR Content**
   - Prompt injection via issue body
   - Malicious code blocks attempting shell execution
   - System prompt manipulation attempts
   - _Mitigation_: `safety.py` sanitizes all untrusted content; bodies are truncated; dangerous patterns are redacted

2. **Pattern Pack YAML**
   - Malicious pattern definitions
   - Code injection via `bad_code_signals` or `fix_patterns`
   - _Mitigation_: Pattern packs are loaded locally; Pydantic validation rejects malformed entries; packs are version-controlled

3. **GitHub API Credentials**
   - Token leakage in error messages or logs
   - _Mitigation_: Token is never logged; `env.py` only reads from env/config; `diagnose` only shows whether token is configured, not the value

4. **Local Code Scanning**
   - DetectorOracle reads local source files only
   - No code is transmitted externally without explicit opt-in
   - _Mitigation_: `DETECTORACLE_ALLOW_REMOTE_LLM=0` by default; legacy `ISSUEORACLE_ALLOW_REMOTE_LLM=0` is also accepted; code stays local

## Trust Boundaries

| Boundary | Trusted? | Notes |
|----------|----------|-------|
| Local filesystem | ✅ | User's own code |
| `~/.detectoracle/` | ✅ | User-controlled config and local data |
| `~/.issueoracle/` | ✅ | Legacy user-controlled config and local data |
| Pattern packs | ✅ (with validation) | Pydantic-schema validated |
| GitHub API response | ❌ | Untrusted; must be sanitized |
| Mined candidates | ❌ (until reviewed) | Must pass human review before default review use |

## Data Flow

```text
GitHub API → safety.sanitize() → issue_filter → evidence_linker → pattern_extract
  ↓
Mining result (local only, no redistribution)
  ↓
Human review → approved → packs/ or approved experience JSON
  ↓
Pattern loaded → code_index → pattern_match → review → report (local only)
```
