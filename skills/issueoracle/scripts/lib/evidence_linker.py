from __future__ import annotations

import re

from lib import github_fetch, schema

CLOSE_KEYWORDS = re.compile(
    r"\b(close[sd]?|fix(es|ed)?|resolve[sd]?|resolves|fixed)\s+"
    r"(?:#?(\d+)|(?:[\w-]+/[\w-]+)?#(\d+))",
    re.IGNORECASE,
)


def link_issue_to_prs(
    issue: schema.GitHubIssue, owner_repo: str, token: str | None = None
) -> list[schema.LinkedPR]:
    prs: list[schema.LinkedPR] = []
    seen: set[int] = set()
    for pr_num in github_fetch.find_linked_prs(owner_repo, issue.number, token):
        if pr_num in seen:
            continue
        pr = github_fetch.fetch_pr(owner_repo, pr_num, token)
        if pr and pr.merged:
            prs.append(pr)
            seen.add(pr_num)
    return prs


def build_evidence(
    issue: schema.GitHubIssue, prs: list[schema.LinkedPR], owner_repo: str
) -> list[schema.OssEvidence]:
    evidences: list[schema.OssEvidence] = []
    for pr in prs:
        evidences.append(
            schema.OssEvidence(
                repo=owner_repo,
                issue=issue.number,
                pr=pr.number,
                commit=pr.commit_sha,
                url=issue.url,
                strength="high" if pr.merged else "medium",
            )
        )
    if not evidences:
        evidences.append(
            schema.OssEvidence(
                repo=owner_repo,
                issue=issue.number,
                url=issue.url,
                strength="low",
            )
        )
    return evidences
