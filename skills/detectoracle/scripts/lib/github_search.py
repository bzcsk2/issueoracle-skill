from __future__ import annotations

from typing import Any

from lib import http, safety, schema

GITHUB_API = "https://api.github.com"


def _request(path: str, token: str | None, params: dict | None = None, method: str = "GET") -> Any:
    data, _ = http.get_json(path, token=token, params=params, use_cache=True)
    return data


def _paginated_get(path: str, token: str | None, params: dict | None = None) -> list[dict]:
    p = dict(params or {})
    p.setdefault("per_page", 100)
    all_data: list[dict] = []
    for page in range(1, 4):
        p["page"] = page
        raw, _ = http.get_json(path, token=token, params=p, use_cache=True)
        if not raw:
            break
        if isinstance(raw, list):
            all_data.extend(raw)
            if len(raw) < p["per_page"]:
                break
        else:
            all_data.append(raw)
            break
    return all_data


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
        issues.append(
            schema.GitHubIssue(
                number=item["number"],
                title=item["title"],
                state=item["state"],
                labels=[lb["name"] for lb in item.get("labels", [])],
                body=safe_body,
                url=item["html_url"],
                created_at=item["created_at"],
                closed_at=item.get("closed_at"),
                author=item.get("user", {}).get("login", ""),
            )
        )
    return issues


def search_similar_repos(
    language: str,
    topics: list[str],
    *,
    token: str | None = None,
    max_results: int = 5,
) -> list[schema.RepoCandidate]:
    seen: dict[str, schema.RepoCandidate] = {}
    queries: list[tuple[str, int]] = []

    if topics:
        queries.append((f"language:{language} topic:{topics[0]} stars:>100", 100))
    if len(topics) > 1:
        queries.append((f"language:{language} topic:{topics[1]} stars:>50", 50))

    framework_keywords = [
        t for t in topics if t in ("fastapi", "flask", "django", "express", "react", "vue")
    ]
    if framework_keywords:
        kw = framework_keywords[0]
        queries.append((f"language:{language} {kw} stars:>50", 50))

    queries.append((f"language:{language} stars:>20 pushed:>2025-01-01", 20))

    for q, _min_stars in queries:
        data = _request(
            "/search/repositories",
            token,
            {"q": q, "sort": "stars", "order": "desc", "per_page": 10},
        )
        for item in data.get("items", []):
            repo = item["full_name"]
            if repo in seen:
                continue
            seen[repo] = schema.RepoCandidate(
                owner_repo=repo,
                stars=item["stargazers_count"],
                description=item.get("description", "") or "",
                url=item["html_url"],
                topics=item.get("topics", []),
                matched_topics=[t for t in topics if t in item.get("topics", [])],
                last_pushed_at=item.get("pushed_at"),
                open_issues_count=item.get("open_issues_count"),
            )
        if len(seen) >= max_results * 2:
            break

    candidates = list(seen.values())

    max_stars = max((c.stars for c in candidates), default=1)
    import datetime

    now = datetime.datetime.now().timestamp()
    for c in candidates:
        topic_overlap = len(c.matched_topics) / max(len(topics), 1)
        framework_overlap = (
            1.0 if any(t in (c.matched_topics or []) for t in framework_keywords) else 0.0
        )
        stars_score = min(c.stars / max_stars, 1.0)
        recent_score = 0.0
        if c.last_pushed_at:
            try:
                pushed = datetime.datetime.fromisoformat(
                    c.last_pushed_at.replace("Z", "+00:00")
                ).timestamp()
                days_since = (now - pushed) / 86400
                recent_score = max(0.0, 1.0 - days_since / 365)
            except Exception:
                pass
        issue_score = min((c.open_issues_count or 0) / 100, 1.0) if c.open_issues_count else 0.0
        c.score = (
            0.35 * framework_overlap
            + 0.25 * topic_overlap
            + 0.20 * stars_score
            + 0.10 * recent_score
            + 0.10 * issue_score
        )

    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates[:max_results]


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
