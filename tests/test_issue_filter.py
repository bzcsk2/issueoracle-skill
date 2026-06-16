from __future__ import annotations

import unittest

from lib import issue_filter, schema


class IssueFilterTests(unittest.TestCase):
    def _make_issue(self, number: int, title: str, labels: list[str] | None = None) -> schema.GitHubIssue:
        return schema.GitHubIssue(
            number=number, title=title, state="closed",
            labels=labels or [],
            url=f"https://github.com/o/r/issues/{number}",
            created_at="2024-01-01",
        )

    def test_bug_label_passes(self):
        issue = self._make_issue(1, "Something broken", labels=["bug"])
        self.assertTrue(issue_filter.is_likely_bug(issue))

    def test_question_label_excluded(self):
        issue = self._make_issue(2, "How to use X", labels=["question"])
        self.assertFalse(issue_filter.is_likely_bug(issue))

    def test_documentation_excluded(self):
        issue = self._make_issue(3, "Update docs", labels=["documentation"])
        self.assertFalse(issue_filter.is_likely_bug(issue))

    def test_non_bug_title_excluded(self):
        issue = self._make_issue(4, "Feature request: add dark mode", labels=[])
        self.assertFalse(issue_filter.is_likely_bug(issue))

    def test_bug_keyword_in_title(self):
        issue = self._make_issue(5, "Memory leak on large uploads", labels=[])
        self.assertTrue(issue_filter.is_likely_bug(issue))

    def test_crash_title(self):
        issue = self._make_issue(6, "Crash when parsing empty file", labels=[])
        self.assertTrue(issue_filter.is_likely_bug(issue))

    def test_enhancement_excluded(self):
        issue = self._make_issue(7, "Improve performance", labels=["enhancement"])
        self.assertFalse(issue_filter.is_likely_bug(issue))

    def test_duplicate_excluded(self):
        issue = self._make_issue(8, "Same bug", labels=["duplicate"])
        self.assertFalse(issue_filter.is_likely_bug(issue))

    def test_filter_issues(self):
        issues = [
            self._make_issue(1, "Bug: crash", labels=["bug"]),
            self._make_issue(2, "How to install", labels=["question"]),
            self._make_issue(3, "Memory leak", labels=[]),
            self._make_issue(4, "Add feature", labels=["enhancement"]),
        ]
        filtered = issue_filter.filter_issues(issues)
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].number, 1)
        self.assertEqual(filtered[1].number, 3)


if __name__ == "__main__":
    unittest.main()
