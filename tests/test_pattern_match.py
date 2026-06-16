from __future__ import annotations

import unittest

from lib import pattern_match, schema


class PatternMatchTests(unittest.TestCase):
    def setUp(self):
        self.pattern = schema.Pattern(
            id="test-pattern",
            title="Test",
            language="Python",
            bug_type="test",
            root_cause="test",
            evidence=[schema.OssEvidence(repo="o/r", url="https://github.com/o/r/issues/1")],
            confidence=0.7,
            trigger_conditions=[
                schema.TriggerCondition(
                    description="async function with query",
                    code_signals=["async", "session"],
                )
            ],
            bad_code_signals=["session", "query("],
        )
        self.profile = schema.RepoProfile(
            repo_path=".",
            languages=["Python"],
            frameworks=["fastapi"],
        )
        self.chunk = schema.CodeChunk(
            file="test.py",
            start_line=1,
            end_line=10,
            symbol="test_func",
            language="Python",
            signals=["session", "query(", "await"],
            code_excerpt="async def test_func():\n    session.query()",
        )

    def test_metadata_recall_match(self):
        result = pattern_match._metadata_recall(self.pattern, self.profile)
        self.assertTrue(result)

    def test_metadata_recall_no_match_language(self):
        profile = schema.RepoProfile(repo_path=".", languages=["TypeScript"])
        result = pattern_match._metadata_recall(self.pattern, profile)
        self.assertFalse(result)

    def test_match_signals_hit(self):
        hits = pattern_match._match_signals(self.pattern.bad_code_signals, self.chunk)
        self.assertIn("session", hits)
        self.assertIn("query(", hits)

    def test_match_signals_miss(self):
        chunk = schema.CodeChunk(
            file="other.py",
            start_line=1,
            end_line=5,
            symbol="other",
            language="Python",
            code_excerpt="x = 1 + 2",
        )
        hits = pattern_match._match_signals(self.pattern.bad_code_signals, chunk)
        self.assertEqual(hits, [])

    def test_trigger_coverage_full(self):
        cov = pattern_match._trigger_coverage(self.pattern.trigger_conditions, self.chunk)
        self.assertEqual(cov, 1.0)

    def test_trigger_coverage_empty(self):
        pattern = schema.Pattern(
            id="no-trigger",
            title="No Trigger",
            language="Python",
            bug_type="test",
            root_cause="test",
            evidence=[schema.OssEvidence(repo="o/r", url="https://github.com/o/r/issues/1")],
            confidence=0.5,
        )
        cov = pattern_match._trigger_coverage(pattern.trigger_conditions, self.chunk)
        self.assertEqual(cov, 1.0)

    def test_match_integration(self):
        chunks = [self.chunk]
        patterns = [self.pattern]
        results = pattern_match.match(chunks, patterns, self.profile)
        self.assertGreater(len(results), 0)
        self.assertGreater(results[0].score, 0)

    def test_score_range(self):
        score = pattern_match._score(self.pattern, ["session", "query("], 1.0)
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
