from __future__ import annotations

from lib import github_search, schema


def fetch_timeline(owner_repo: str, issue_number: int, token: str | None = None) -> list[dict]:
    data = github_search._request(
        f"/repos/{owner_repo}/issues/{issue_number}/timeline",
        token, {"per_page": 100},
    )
    return data if isinstance(data, list) else []


def find_linked_prs(owner_repo: str, issue_number: int, token: str | None = None) -> list[int]:
    timeline = fetch_timeline(owner_repo, issue_number, token)
    pr_numbers: list[int] = []
    for event in timeline:
        src = event.get("source", {}).get("issue", {})
        if src.get("pull_request") and src.get("number"):
            pr_numbers.append(src["number"])
    return list(dict.fromkeys(pr_numbers))


def fetch_pr(owner_repo: str, pr_number: int, token: str | None = None) -> schema.LinkedPR | None:
    try:
        data = github_search._request(f"/repos/{owner_repo}/pulls/{pr_number}", token)
    except Exception:
        return None
    return schema.LinkedPR(
        number=data["number"],
        title=data["title"],
        state=data["state"],
        merged=data.get("merged", False),
        url=data["html_url"],
        commit_sha=(data.get("merge_commit_sha") or "") or None,
        files_changed=[],
    )


def fetch_pr_files(owner_repo: str, pr_number: int, token: str | None = None) -> list[str]:
    try:
        data = github_search._request(
            f"/repos/{owner_repo}/pulls/{pr_number}/files",
            token, {"per_page": 100},
        )
        return [f["filename"] for f in data] if isinstance(data, list) else []
    except Exception:
        return []
