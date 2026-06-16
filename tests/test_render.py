from __future__ import annotations

import unittest
import json

from lib import render


class RenderTests(unittest.TestCase):
    def test_render_diagnose(self):
        data = {"python": "3.12", "packs": 5}
        output = render.render_diagnose(data)
        parsed = json.loads(output)
        self.assertEqual(parsed["python"], "3.12")

    def test_render_review_empty(self):
        report = {
            "version": "0.1.0",
            "scope": {"repo": ".", "mode": "full"},
            "summary": {"findings_total": 0, "suppressed": 0, "by_severity": {}, "patterns_loaded": 0, "files_scanned": 0},
            "findings": [],
            "suppressed": [],
        }
        output = render.render_review(report)
        self.assertIn("Review Report", output)
        self.assertIn("Findings**: 0", output)

    def test_render_review_with_finding(self):
        report = {
            "version": "0.1.0",
            "scope": {"repo": ".", "mode": "full"},
            "summary": {"findings_total": 1, "suppressed": 0, "by_severity": {"high": 1}, "patterns_loaded": 1, "files_scanned": 1},
            "findings": [
                {
                    "id": "f1", "severity": "high", "confidence": 0.9,
                    "file": "app.py", "start_line": 1, "end_line": 10,
                    "title": "Test finding", "matched_pattern": "test",
                    "trigger_condition": "async without finally",
                    "local_evidence": [{"line": 5, "description": "session used"}],
                    "oss_evidence": [{"repo": "o/r", "issue": 1, "url": "https://github.com/o/r/issues/1"}],
                    "suggested_fix": "Add finally", "validation": "",
                    "false_positive_boundary": "Test",
                }
            ],
            "suppressed": [],
        }
        output = render.render_review(report)
        self.assertIn("Test finding", output)
        self.assertIn("app.py", output)

    def test_render_review_json(self):
        report = {"version": "0.1.0", "scope": {}, "summary": {}, "findings": [], "suppressed": []}
        output = render.render_review_json(report)
        parsed = json.loads(output)
        self.assertEqual(parsed["version"], "0.1.0")

    def test_render_review_compact(self):
        report = {
            "findings": [{"severity": "high", "file": "app.py", "start_line": 1, "confidence": 0.9, "title": "Bug"}]
        }
        output = render.render_review_compact(report)
        self.assertIn("[high]", output)
        self.assertIn("app.py", output)

    def test_render_mining_markdown(self):
        result = {
            "repo": "o/r", "mined_at": "2024-01-01",
            "issues_searched": 10, "issues_kept": 5, "issues_with_pr": 3,
            "candidates": [
                {
                    "id": "mined-o-r-1", "source_issue": 1,
                    "bug_type": "resource_leak", "root_cause": "Session leak",
                    "confidence": 0.5,
                    "bad_code_signals": ["session"],
                    "evidence": [{"repo": "o/r", "issue": 1, "url": "https://github.com/o/r/issues/1"}],
                    "false_positive_boundary": "Verify before use",
                }
            ],
        }
        output = render.render_mining(result, emit="markdown")
        self.assertIn("Mining Report", output)
        self.assertIn("mined-o-r-1", output)

    def test_render_mining_json(self):
        result = {"repo": "o/r", "candidates": []}
        output = render.render_mining(result, emit="json")
        parsed = json.loads(output)
        self.assertEqual(parsed["repo"], "o/r")

    def test_render_validation(self):
        result = {"pack_path": "/packs", "patterns_valid": 5, "patterns_invalid": 0, "errors": []}
        output = render.render_validation(result)
        self.assertIn("5", output)

    def test_render_validation_with_errors(self):
        result = {"pack_path": "/packs", "patterns_valid": 4, "patterns_invalid": 1, "errors": [{"file": "bad.yaml", "pattern_id": "p1", "errors": ["Missing field"]}]}
        output = render.render_validation(result)
        self.assertIn("bad.yaml", output)


if __name__ == "__main__":
    unittest.main()
