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
        hits, suppressed, bonus = pattern_match._match_signals(self.pattern.bad_code_signals, self.chunk)
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
        hits, suppressed, bonus = pattern_match._match_signals(self.pattern.bad_code_signals, chunk)
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

    def test_typed_signal_required(self):
        chunk = schema.CodeChunk(
            file="x.py", start_line=1, end_line=3, symbol="x", language="Python",
            code_excerpt="allow_credentials = True",
        )
        typed = schema.TypedSignal(kind="required", value="allow_credentials")
        hits, suppressed, bonus = pattern_match._match_signals([typed], chunk)
        self.assertIn("allow_credentials", hits)
        self.assertFalse(suppressed)

    def test_typed_signal_required_any(self):
        chunk = schema.CodeChunk(
            file="x.py", start_line=1, end_line=3, symbol="x", language="Python",
            code_excerpt="allow_origins=['*']",
        )
        typed = schema.TypedSignal(kind="required_any", values=["allow_origins=['*']", 'allow_origins=["*"]'])
        hits, suppressed, bonus = pattern_match._match_signals([typed], chunk)
        self.assertEqual(len(hits), 1)

    def test_typed_signal_suppress_if_present(self):
        chunk = schema.CodeChunk(
            file="x.py", start_line=1, end_line=3, symbol="x", language="Python",
            code_excerpt="allow_origins=['*']; allow_credentials=False",
        )
        req = schema.TypedSignal(kind="required", value="allow_origins")
        sup = schema.TypedSignal(kind="suppress_if_present", value="allow_credentials=False")
        hits, suppressed, bonus = pattern_match._match_signals([req, sup], chunk)
        self.assertTrue(suppressed)
        self.assertIn("allow_origins", hits)

    def test_typed_signal_negative_lowers_confidence(self):
        chunk = schema.CodeChunk(
            file="x.py", start_line=1, end_line=3, symbol="x", language="Python",
            code_excerpt="allow_origins=['*']; allow_credentials=False",
        )
        req = schema.TypedSignal(kind="required", value="allow_origins")
        neg = schema.TypedSignal(kind="negative", value="allow_credentials=False")
        hits, suppressed, bonus = pattern_match._match_signals([req, neg], chunk)
        self.assertIn("allow_origins", hits)
        self.assertLess(bonus, 0)
        self.assertFalse(suppressed)

    def test_typed_signal_optional_bonus(self):
        chunk = schema.CodeChunk(
            file="x.py", start_line=1, end_line=3, symbol="x", language="Python",
            code_excerpt="import typing",
        )
        opt = schema.TypedSignal(kind="optional", value="typing")
        hits, suppressed, bonus = pattern_match._match_signals([opt], chunk)
        self.assertGreater(bonus, 0)


if __name__ == "__main__":
    unittest.main()
