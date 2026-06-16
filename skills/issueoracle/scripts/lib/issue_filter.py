from __future__ import annotations

from lib import schema

EXCLUDE_LABELS = {
    "question",
    "documentation",
    "docs",
    "feature",
    "enhancement",
    "duplicate",
    "wontfix",
    "wont-fix",
    "invalid",
    "discussion",
    "good first issue",
    "help wanted",
    "support",
}

NON_BUG_TITLE_HINTS = (
    "how to",
    "question:",
    "[question]",
    "feature request",
    "proposal:",
    "rfc:",
    "discussion:",
)

BUG_WORDS = (
    "bug",
    "crash",
    "error",
    "leak",
    "exception",
    "fail",
    "broken",
    "wrong",
    "incorrect",
    "regression",
    "hang",
    "deadlock",
)


def is_likely_bug(issue: schema.GitHubIssue) -> bool:
    labels_lower = {lb.lower() for lb in issue.labels}
    if labels_lower & EXCLUDE_LABELS:
        return False
    title_lower = issue.title.lower()
    if any(hint in title_lower for hint in NON_BUG_TITLE_HINTS):
        return False
    if "bug" in labels_lower:
        return True
    return bool(any(w in title_lower for w in BUG_WORDS))


def filter_issues(issues: list[schema.GitHubIssue]) -> list[schema.GitHubIssue]:
    return [i for i in issues if is_likely_bug(i)]
