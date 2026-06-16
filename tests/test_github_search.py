from __future__ import annotations

import unittest
from unittest import mock

from lib import github_search, schema


class GithubSearchTests(unittest.TestCase):
    @mock.patch("lib.github_search._request")
    def test_search_closed_issues(self, mock_req):
        mock_req.return_value = {
            "items": [
                {
                    "number": 1,
                    "title": "Bug: crash on startup",
                    "state": "closed",
                    "labels": [{"name": "bug"}, {"name": "critical"}],
                    "body": "Stack trace on init",
                    "html_url": "https://github.com/o/r/issues/1",
                    "created_at": "2024-01-01T00:00:00Z",
                    "closed_at": "2024-01-02T00:00:00Z",
                    "user": {"login": "testuser"},
                }
            ]
        }
        issues = github_search.search_closed_issues("o/r", label="bug", max_results=10, token="test-token")
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].number, 1)
        self.assertEqual(issues[0].labels, ["bug", "critical"])
        self.assertEqual(issues[0].author, "testuser")

    @mock.patch("lib.github_search._request")
    def test_search_empty(self, mock_req):
        mock_req.return_value = {"items": []}
        issues = github_search.search_closed_issues("o/r", max_results=10, token=None)
        self.assertEqual(issues, [])

    @mock.patch("lib.github_search._request")
    def test_search_similar_repos(self, mock_req):
        mock_req.return_value = {
            "items": [
                {
                    "full_name": "fastapi/fastapi",
                    "stargazers_count": 75000,
                    "description": "FastAPI framework",
                    "html_url": "https://github.com/fastapi/fastapi",
                    "topics": ["fastapi", "web", "python"],
                },
                {
                    "full_name": "encode/starlette",
                    "stargazers_count": 10000,
                    "description": "Starlette ASGI framework",
                    "html_url": "https://github.com/encode/starlette",
                    "topics": ["asgi", "python"],
                },
            ]
        }
        repos = github_search.search_similar_repos("Python", ["fastapi"], token="test-token", max_results=2)
        self.assertEqual(len(repos), 2)
        self.assertEqual(repos[0].owner_repo, "fastapi/fastapi")
        self.assertEqual(repos[0].stars, 75000)
        self.assertEqual(repos[1].owner_repo, "encode/starlette")

    @mock.patch("lib.github_search._request")
    def test_search_similar_repos_empty(self, mock_req):
        mock_req.return_value = {"items": []}
        repos = github_search.search_similar_repos("Python", ["unknown"], token=None)
        self.assertEqual(repos, [])

    @mock.patch("lib.github_search._request")
    def test_check_rate_limit(self, mock_req):
        mock_req.return_value = {
            "resources": {
                "core": {"remaining": 4999, "limit": 5000},
                "search": {"remaining": 29, "limit": 30},
            }
        }
        result = github_search.check_rate_limit("token")
        self.assertEqual(result["core_remaining"], 4999)
        self.assertEqual(result["search_remaining"], 29)


if __name__ == "__main__":
    unittest.main()
