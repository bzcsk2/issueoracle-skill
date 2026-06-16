from __future__ import annotations

import unittest

from lib import schema


class ProjectProfileTests(unittest.TestCase):
    def test_defaults(self):
        p = schema.ProjectProfile(repo_path="/tmp/test")
        self.assertEqual(p.repo_path, "/tmp/test")
        self.assertEqual(p.languages, [])
        self.assertEqual(p.project_type, "")

    def test_full(self):
        p = schema.ProjectProfile(
            repo_path="/tmp/test", languages=["Python"], frameworks=["FastAPI"],
            dependencies=["pydantic"], risk_surfaces=["web"],
            project_type="web_api", search_topics=["fastapi"],
        )
        self.assertEqual(p.project_type, "web_api")


class RepoCandidateTests(unittest.TestCase):
    def test_defaults(self):
        c = schema.RepoCandidate(owner_repo="test/repo")
        self.assertEqual(c.stars, 0)
        self.assertEqual(c.description, "")

    def test_minimal(self):
        c = schema.RepoCandidate(owner_repo="test/repo", stars=100)
        self.assertEqual(c.owner_repo, "test/repo")


class BugExperienceTests(unittest.TestCase):
    def test_defaults(self):
        be = schema.BugExperience(id="b1", title="bug")
        self.assertEqual(be.bug_type, "general_bug")
        self.assertEqual(be.confidence, 0.5)

    def test_with_evidence(self):
        ev = schema.OssEvidence(repo="r", issue=1, url="u", pr_url="")
        be = schema.BugExperience(id="b1", title="bug", evidence=[ev])
        self.assertEqual(len(be.evidence), 1)


class ExperienceReportTests(unittest.TestCase):
    def test_empty(self):
        r = schema.ExperienceReport()
        self.assertEqual(r.source_repos, [])
        self.assertEqual(r.experiences, [])

    def test_with_repos(self):
        r = schema.ExperienceReport(source_repos=["a/b", "c/d"])
        self.assertEqual(len(r.source_repos), 2)


class PatternTests(unittest.TestCase):
    def test_roundtrip(self):
        p = schema.Pattern(
            id="test-pattern",
            title="Test Pattern",
            language="Python",
            bug_type="resource_leak",
            root_cause="Session not closed on exception",
            evidence=[schema.OssEvidence(repo="o/r", url="https://github.com/o/r/issues/1")],
            confidence=0.7,
        )
        d = p.model_dump()
        p2 = schema.Pattern(**d)
        self.assertEqual(p.id, p2.id)
        self.assertEqual(p.title, p2.title)
        self.assertEqual(p.language, p2.language)
        self.assertEqual(p.bug_type, p2.bug_type)
        self.assertEqual(p.root_cause, p2.root_cause)
        self.assertEqual(p.confidence, p2.confidence)
        self.assertEqual(len(p2.evidence), 1)
        self.assertEqual(p2.evidence[0].repo, "o/r")

    def test_pattern_requires_evidence(self):
        with self.assertRaises(Exception):
            schema.Pattern(
                id="no-evidence",
                title="No Evidence",
                language="Python",
                bug_type="test",
                root_cause="test",
                evidence=[],
                confidence=0.5,
            )

    def test_confidence_range(self):
        with self.assertRaises(Exception):
            schema.Pattern(
                id="bad-confidence",
                title="Bad",
                language="Python",
                bug_type="test",
                root_cause="test",
                evidence=[schema.OssEvidence(repo="o/r", url="https://github.com/o/r/issues/1")],
                confidence=1.5,
            )

    def test_oss_evidence_defaults(self):
        ev = schema.OssEvidence(repo="o/r", url="https://github.com/o/r/issues/1")
        self.assertEqual(ev.strength, "medium")
        self.assertIsNone(ev.issue)
        self.assertIsNone(ev.pr)

    def test_trigger_condition(self):
        tc = schema.TriggerCondition(description="async function without try-finally")
        self.assertEqual(tc.description, "async function without try-finally")
        self.assertEqual(tc.code_signals, [])


class GitHubIssueTests(unittest.TestCase):
    def test_minimal(self):
        gi = schema.GitHubIssue(
            number=1, title="Bug", state="closed", url="https://github.com/o/r/issues/1",
            created_at="2024-01-01",
        )
        self.assertEqual(gi.number, 1)
        self.assertEqual(gi.labels, [])
        self.assertEqual(gi.body, "")

    def test_full(self):
        gi = schema.GitHubIssue(
            number=42, title="Crash on startup", state="closed",
            labels=["bug", "high-priority"],
            body="Error trace...", url="https://github.com/o/r/issues/42",
            created_at="2024-01-01", closed_at="2024-01-05", author="dev",
        )
        self.assertEqual(len(gi.labels), 2)
        self.assertEqual(gi.author, "dev")


class CandidatePatternTests(unittest.TestCase):
    def test_defaults(self):
        cp = schema.CandidatePattern(
            id="mined-test-1", title="Test", language="Python",
            bug_type="resource_leak", root_cause="test",
            evidence=[schema.OssEvidence(repo="o/r", url="https://github.com/o/r/issues/1")],
            source_issue=1, source_repo="o/r",
        )
        self.assertEqual(cp.confidence, 0.5)
        self.assertEqual(cp.status, "candidate")
        self.assertEqual(cp.severity_hint, "medium")


class FindingTests(unittest.TestCase):
    def test_minimal(self):
        f = schema.Finding(
            id="finding-1", severity="high", confidence=0.8,
            file="src/app.py", start_line=10, end_line=20,
            title="Test finding", matched_pattern="test-pattern",
            trigger_condition="async without finally",
            suggested_fix="Add finally block", validation="",
            false_positive_boundary="Only applies to async functions",
        )
        self.assertEqual(f.severity, "high")
        self.assertEqual(f.confidence, 0.8)
        self.assertEqual(f.local_evidence, [])


class ReviewReportTests(unittest.TestCase):
    def test_empty(self):
        r = schema.ReviewReport(
            version="0.1.0",
            scope={"repo": ".", "mode": "full"},
            summary={"findings_total": 0},
            findings=[],
            suppressed=[],
        )
        self.assertEqual(len(r.findings), 0)
        self.assertEqual(len(r.suppressed), 0)


class MiningResultTests(unittest.TestCase):
    def test_empty_candidates(self):
        mr = schema.MiningResult(
            repo="o/r", mined_at="2024-01-01",
            issues_searched=10, issues_kept=5, issues_with_pr=3,
            candidates=[], raw_dir="/tmp/raw", review_path="/tmp/review.md",
        )
        self.assertEqual(len(mr.candidates), 0)


class LinkedPRTests(unittest.TestCase):
    def test_minimal(self):
        pr = schema.LinkedPR(
            number=1, title="Fix bug", state="closed", merged=True,
            url="https://github.com/o/r/pull/1",
        )
        self.assertTrue(pr.merged)
        self.assertEqual(pr.files_changed, [])


if __name__ == "__main__":
    unittest.main()
