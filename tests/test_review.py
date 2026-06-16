from __future__ import annotations

import unittest

from lib import pattern_match, review, schema


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.pattern = schema.Pattern(
            id="test-pattern",
            title="Test Pattern",
            language="Python",
            bug_type="resource_leak",
            root_cause="Session not closed",
            severity_hint="high",
            evidence=[
                schema.OssEvidence(
                    repo="o/r", url="https://github.com/o/r/issues/1", strength="high"
                )
            ],
            confidence=0.8,
            trigger_conditions=[
                schema.TriggerCondition(
                    description="async function with database query",
                    code_signals=["async", "session"],
                )
            ],
            bad_code_signals=["session", "query("],
            fix_patterns=["Add finally block"],
            false_positive_boundary="Only for async functions",
        )
        self.chunk = schema.CodeChunk(
            file="app.py",
            start_line=1,
            end_line=10,
            symbol="get_data",
            language="Python",
            signals=["session", "query(", "async"],
            code_excerpt="async def get_data():\n    session.query()",
        )
        self.profile = schema.RepoProfile(
            repo_path=".",
            languages=["Python"],
            frameworks=["fastapi"],
        )

    def test_build_findings_empty_matches(self):
        findings, suppressed = review.build_findings([], "medium", 20)
        self.assertEqual(findings, [])
        self.assertEqual(suppressed, [])

    def test_build_findings_with_matches(self):
        results = pattern_match.match([self.chunk], [self.pattern], self.profile)
        findings, suppressed = review.build_findings(results, "low", 20)
        self.assertGreater(len(findings), 0)
        self.assertEqual(findings[0].matched_pattern, "test-pattern")
        self.assertEqual(findings[0].file, "app.py")

    def test_build_findings_respects_max(self):
        results = pattern_match.match([self.chunk], [self.pattern], self.profile)
        findings, suppressed = review.build_findings(results, "low", 1)
        self.assertLessEqual(len(findings), 1)

    def test_build_findings_suppresses_low_confidence(self):
        low_pattern = schema.Pattern(
            id="low-pattern",
            title="Low",
            language="Python",
            bug_type="test",
            root_cause="test",
            evidence=[schema.OssEvidence(repo="o/r", url="https://github.com/o/r/issues/1")],
            confidence=0.1,
            bad_code_signals=["session"],
            trigger_conditions=[schema.TriggerCondition(description="test")],
            fix_patterns=[],
            false_positive_boundary="",
        )
        results = pattern_match.match([self.chunk], [low_pattern], self.profile)
        findings, suppressed = review.build_findings(results, "medium", 20)
        self.assertEqual(len(findings), 0)


if __name__ == "__main__":
    unittest.main()
