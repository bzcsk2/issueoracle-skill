from __future__ import annotations

import unittest
from unittest import mock

from lib import evidence_linker, schema


class EvidenceLinkerTests(unittest.TestCase):
    @mock.patch("lib.github_fetch.find_linked_prs")
    @mock.patch("lib.github_fetch.fetch_pr")
    def test_link_issue_to_prs(self, mock_fetch_pr, mock_find_linked):
        mock_find_linked.return_value = [42]
        mock_fetch_pr.return_value = schema.LinkedPR(
            number=42, title="Fix crash", state="closed", merged=True,
            url="https://github.com/o/r/pull/42",
            commit_sha="abc123",
        )
        issue = schema.GitHubIssue(
            number=1, title="Bug", state="closed",
            url="https://github.com/o/r/issues/1",
            created_at="2024-01-01",
        )
        prs = evidence_linker.link_issue_to_prs(issue, "o/r", token="test")
        self.assertEqual(len(prs), 1)
        self.assertEqual(prs[0].number, 42)
        self.assertTrue(prs[0].merged)

    def test_build_evidence_with_prs(self):
        issue = schema.GitHubIssue(
            number=1, title="Bug", state="closed",
            url="https://github.com/o/r/issues/1",
            created_at="2024-01-01",
        )
        prs = [schema.LinkedPR(
            number=42, title="Fix", state="closed", merged=True,
            url="https://github.com/o/r/pull/42", commit_sha="abc",
        )]
        evidence = evidence_linker.build_evidence(issue, prs, "o/r")
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].strength, "high")
        self.assertEqual(evidence[0].pr, 42)

    def test_build_evidence_no_prs(self):
        issue = schema.GitHubIssue(
            number=1, title="Bug", state="closed",
            url="https://github.com/o/r/issues/1",
            created_at="2024-01-01",
        )
        evidence = evidence_linker.build_evidence(issue, [], "o/r")
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].strength, "low")


if __name__ == "__main__":
    unittest.main()
