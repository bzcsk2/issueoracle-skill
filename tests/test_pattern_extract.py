from __future__ import annotations

import unittest

from lib import pattern_extract, schema


class PatternExtractTests(unittest.TestCase):
    def _make_issue(
        self, number: int, title: str, body: str = "", labels: list[str] | None = None
    ) -> schema.GitHubIssue:
        return schema.GitHubIssue(
            number=number,
            title=title,
            state="closed",
            labels=labels or [],
            body=body,
            url=f"https://github.com/o/r/issues/{number}",
            created_at="2024-01-01",
        )

    def test_extract_candidate_basic(self):
        issue = self._make_issue(
            1,
            "Memory leak in async session",
            body="Code: ```python\nsession = AsyncSession()\nawait session.query()\n```",
        )
        prs = [
            schema.LinkedPR(
                number=10,
                title="Fix: close session in finally",
                state="closed",
                merged=True,
                url="https://github.com/o/r/pull/10",
                commit_sha="def",
            )
        ]
        cand = pattern_extract.extract_candidate(issue, prs, "o/r")
        self.assertIsNotNone(cand)
        self.assertEqual(cand.source_issue, 1)
        self.assertEqual(cand.confidence, 0.5)
        self.assertEqual(cand.status, "candidate")
        self.assertIn("session", cand.bad_code_signals)
        self.assertIn("query(", cand.bad_code_signals)

    def test_extract_candidate_no_pr(self):
        issue = self._make_issue(2, "Crash on null input")
        cand = pattern_extract.extract_candidate(issue, [], "o/r")
        self.assertIsNotNone(cand)
        self.assertEqual(cand.source_repo, "o/r")

    def test_classify_leak(self):
        bug_type = pattern_extract._classify_bug_type("Memory leak in handler", [])
        self.assertEqual(bug_type, "resource_leak")

    def test_classify_injection(self):
        bug_type = pattern_extract._classify_bug_type("SQL injection in search", [])
        self.assertEqual(bug_type, "injection")

    def test_classify_fallback(self):
        bug_type = pattern_extract._classify_bug_type("Unexpected behavior", [])
        self.assertEqual(bug_type, "general_bug")

    def test_guess_language_python(self):
        self.assertEqual(pattern_extract._guess_language("fastapi/fastapi"), "Python")
        self.assertEqual(pattern_extract._guess_language("django/django"), "Python")

    def test_guess_language_typescript(self):
        self.assertEqual(pattern_extract._guess_language("expressjs/express"), "TypeScript")

    def test_extract_signals_from_body(self):
        body = "```python\nsession.execute(query)\nawait session.commit()\n```"
        signals = pattern_extract._extract_signals(body)
        self.assertIn("session", signals)
        self.assertIn("execute(", signals)

    def test_extract_root_cause_from_pr(self):
        issue = self._make_issue(1, "Bug title")
        prs = [
            schema.LinkedPR(
                number=5,
                title="Fix: add null check before access",
                state="closed",
                merged=True,
                url="https://github.com/o/r/pull/5",
            )
        ]
        cause = pattern_extract._extract_root_cause(issue, prs)
        self.assertIn("add null check", cause)


if __name__ == "__main__":
    unittest.main()
