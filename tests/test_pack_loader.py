from __future__ import annotations

import unittest
import tempfile
from pathlib import Path

from lib import pack_loader, schema


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
