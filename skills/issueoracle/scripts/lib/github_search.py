from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any

from lib import safety, schema

GITHUB_API = "https://api.github.com"


def _headers(token: str | None) -> dict[str, str]:
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "issueoracle-skill/0.1.0",
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _request(path: str, token: str | None, params: dict | None = None, method: str = "GET") -> Any:
    url = f"{GITHUB_API}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=_headers(token), method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def search_closed_issues(
    owner_repo: str,
    *,
    label: str = "bug",
    max_results: int = 50,
    token: str | None = None,
) -> list[schema.GitHubIssue]:
    q = f"repo:{owner_repo} is:issue is:closed label:{label} sort:updated-desc"
    data = _request("/search/issues", token, {"q": q, "per_page": min(max_results, 100)})
    issues: list[schema.GitHubIssue] = []
    for item in data.get("items", [])[:max_results]:
        safe_body = safety.sanitize_issue_body(item.get("body") or "")
        issues.append(schema.GitHubIssue(
            number=item["number"],
            title=item["title"],
            state=item["state"],
            labels=[l["name"] for l in item.get("labels", [])],
            body=safe_body,
            url=item["html_url"],
            created_at=item["created_at"],
            closed_at=item.get("closed_at"),
            author=item.get("user", {}).get("login", ""),
        ))
    return issues


def search_similar_repos(
    language: str, topics: list[str], *,
    token: str | None = None, max_results: int = 5,
) -> list[schema.RepoCandidate]:
    q_parts = [f"language:{language}"]
    q_parts += [f"topic:{t}" for t in topics[:3]]
    q_parts.append("stars:>100")
    q = " ".join(q_parts)
    data = _request("/search/repositories", token, {
        "q": q, "sort": "stars", "order": "desc", "per_page": max_results,
    })
    candidates: list[schema.RepoCandidate] = []
    for item in data.get("items", [])[:max_results]:
        candidates.append(schema.RepoCandidate(
            owner_repo=item["full_name"],
            stars=item["stargazers_count"],
            description=item.get("description", "") or "",
            url=item["html_url"],
            topics=item.get("topics", []),
        ))
    return candidates


def check_rate_limit(token: str | None) -> dict:
    data = _request("/rate_limit", token)
    core = data["resources"]["core"]
    search = data["resources"]["search"]
    return {
        "core_remaining": core["remaining"],
        "core_limit": core["limit"],
        "search_remaining": search["remaining"],
        "search_limit": search["limit"],
    }
