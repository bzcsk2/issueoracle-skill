from __future__ import annotations

import re
from typing import Any

from lib import schema

MAX_BODY_CHARS = 2000

DANGEROUS_PATTERNS = [
    (re.compile(r"<system[^>]*>", re.IGNORECASE), "[redacted system tag]"),
    (re.compile(r"ignore\s+(?:all\s+)?(?:previous|the\s+above)\s+instructions", re.IGNORECASE),
     "[redacted injection attempt]"),
    (re.compile(r"```(?:bash|sh|shell|cmd|powershell)\n.*?```", re.DOTALL),
     "[redacted shell block]"),
    (re.compile(r"```(?:py|python)\n.*?#\s*os\.system.*?```", re.DOTALL),
     "[redacted dangerous code]"),
]


def sanitize_issue_body(body: str) -> str:
    if not body:
        return ""
    cleaned = body
    for pattern, replacement in DANGEROUS_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)
    if len(cleaned) > MAX_BODY_CHARS:
        cleaned = cleaned[:MAX_BODY_CHARS] + "\n...[truncated]"
    return cleaned


def build_safe_evidence(
    issue: schema.GitHubIssue,
    prs: list[schema.LinkedPR],
    owner_repo: str,
) -> list[schema.OssEvidence]:
    evidences: list[schema.OssEvidence] = []
    for pr in prs:
        evidences.append(schema.OssEvidence(
            repo=owner_repo, issue=issue.number, pr=pr.number,
            commit=pr.commit_sha, url=issue.url,
            strength="high" if pr.merged else "medium",
        ))
    if not evidences:
        evidences.append(schema.OssEvidence(
            repo=owner_repo, issue=issue.number, url=issue.url, strength="low",
        ))
    return evidences
