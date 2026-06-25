from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lib import pack_loader


class PackLoaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_load_empty_dir(self):
        patterns, errors = pack_loader.load_pack_dir(self.tmp)
        self.assertEqual(patterns, [])
        self.assertEqual(errors, [])

    def test_load_invalid_yaml(self):
        (self.tmp / "bad.yaml").write_text("invalid: [yaml: broken", encoding="utf-8")
        patterns, errors = pack_loader.load_pack_dir(self.tmp)
        self.assertEqual(patterns, [])
        self.assertGreater(len(errors), 0)

    def test_duplicate_pattern_id_detected(self):
        yaml_content = """
- id: dup-pattern
  title: Duplicate
  language: Python
  bug_type: resource_leak
  root_cause: dup
  confidence: 0.7
  evidence:
    - repo: test/repo
      url: https://github.com/test/repo/issues/1
"""
        (self.tmp / "a.yaml").write_text(yaml_content, encoding="utf-8")
        (self.tmp / "b.yaml").write_text(yaml_content, encoding="utf-8")
        patterns, errors = pack_loader.load_pack_dir(self.tmp)
        self.assertEqual(len(patterns), 1)
        dup_errors = [e for e in errors if "Duplicate pattern id" in str(e)]
        self.assertEqual(len(dup_errors), 1)

    def test_duplicate_in_same_file_allowed(self):
        yaml_content = """
- id: shared-pattern
  title: First
  language: Python
  bug_type: resource_leak
  root_cause: first
  confidence: 0.7
  evidence:
    - repo: test/repo
      url: https://github.com/test/repo/issues/1
- id: shared-pattern
  title: Second
  language: Python
  bug_type: resource_leak
  root_cause: second
  confidence: 0.7
  evidence:
    - repo: test/repo
      url: https://github.com/test/repo/issues/2
"""
        (self.tmp / "dup.yaml").write_text(yaml_content, encoding="utf-8")
        patterns, errors = pack_loader.load_pack_dir(self.tmp)
        self.assertEqual(len(patterns), 1)
        dup_errors = [e for e in errors if "Duplicate pattern id" in str(e)]
        self.assertEqual(len(dup_errors), 1)

    def test_duplicate_pattern_id_fails_validation(self):
        yaml_content = """
- id: clash-pattern
  title: Clash
  language: Python
  bug_type: misc
  root_cause: clash
  confidence: 0.5
  evidence:
    - repo: test/repo
      url: https://github.com/test/repo/issues/1
"""
        (self.tmp / "a.yaml").write_text(yaml_content, encoding="utf-8")
        (self.tmp / "b.yaml").write_text(yaml_content, encoding="utf-8")
        patterns, errors = pack_loader.load_pack_dir(self.tmp)
        self.assertEqual(len(patterns), 1)
        dup_found = any("Duplicate pattern id" in str(e) for e in errors)
        self.assertTrue(dup_found)

    def test_duplicate_pattern_id_fails_review_load(self):
        import subprocess
        import sys
        from pathlib import Path

        packs_dir = Path(__file__).resolve().parent.parent / "skills" / "issueoracle" / "packs"
        result = subprocess.run(
            [
                sys.executable,
                str(
                    Path(__file__).resolve().parent.parent
                    / "skills"
                    / "issueoracle"
                    / "scripts"
                    / "issueoracle.py"
                ),
                "validate",
                str(packs_dir),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(
            result.returncode, 0, msg=f"validate exited {result.returncode}:\n{result.stderr}"
        )

    def test_load_valid_pattern(self):
        yaml_content = """
- id: test-pattern
  title: Test Pattern
  language: Python
  bug_type: resource_leak
  root_cause: Session not closed
  confidence: 0.7
  evidence:
    - repo: test/repo
      url: https://github.com/test/repo/issues/1
"""
        (self.tmp / "patterns.yaml").write_text(yaml_content, encoding="utf-8")
        patterns, errors = pack_loader.load_pack_dir(self.tmp)
        self.assertEqual(len(patterns), 1)
        self.assertEqual(errors, [])
        self.assertEqual(patterns[0].id, "test-pattern")
        self.assertEqual(patterns[0].confidence, 0.7)


if __name__ == "__main__":
    unittest.main()
