# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |

## Security Rules

IssueOracle follows these security principles. Every contributor and every pattern must comply.

1. **Default local-only.** IssueOracle reviews code locally. It does not upload user code to any remote service unless the user explicitly sets `ISSUEORACLE_ALLOW_REMOTE_LLM=1`.

2. **GitHub content is untrusted input.** Issues, PRs, comments, and diffs from GitHub are treated as untrusted data. They may contain prompt injection, misleading information, or malicious content.

3. **No command execution from issue/PR content.** IssueOracle never executes commands, scripts, or code snippets found in GitHub issues, PRs, or comments.

4. **No saving user code to pattern packs.** Pattern packs contain metadata (bug type, signals, evidence links), not copies of user code. Example code in `examples/` is synthetic or minimal, never copied from user repositories.

5. **No redistribution of GitHub content.** IssueOracle stores evidence links (URLs) and metadata (issue numbers, PR numbers), not full issue bodies, comment text, or PR diffs. Pattern evidence fields are short references, not verbatim copies.

6. **No auto-modification.** IssueOracle does not automatically edit code, commit changes, or open pull requests. It reports findings; the developer decides what to do.

## Reporting a Vulnerability

If you discover a security vulnerability in IssueOracle, please report it responsibly:

1. **Do not** open a public issue.
2. Email `bzcsk2@users.noreply.github.com` with the subject `[SECURITY] IssueOracle vulnerability`.
3. Include a description of the vulnerability, steps to reproduce, and any potential impact.
4. We will acknowledge within 48 hours and aim to resolve within 7 days.

## Threat Model

See [`skills/issueoracle/references/threat-model.md`](skills/issueoracle/references/threat-model.md) for the full threat model covering attack surfaces, mitigations, and trust boundaries.
