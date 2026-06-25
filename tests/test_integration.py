from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = (
            Path(__file__).resolve().parent.parent
            / "skills"
            / "detectoracle"
            / "scripts"
            / "detectoracle.py"
        )
        cls.packs = Path(__file__).resolve().parent.parent / "skills" / "detectoracle" / "packs"
        cls.python = sys.executable

    def _run(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run(
            [self.python, str(self.script)] + list(args),
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_diagnose(self):
        result = self._run("diagnose")
        self.assertEqual(result.returncode, 0)
        self.assertIn("python_version", result.stdout)
        self.assertIn("packs_found", result.stdout)

    def test_validate(self):
        result = self._run("validate", str(self.packs), "--emit", "json")
        self.assertEqual(result.returncode, 0)
        self.assertIn("patterns_valid", result.stdout)

    def test_validate_nonexistent(self):
        result = self._run("validate", "/nonexistent")
        self.assertNotEqual(result.returncode, 0)

    def test_review_self(self):
        result = self._run("review", ".", "--emit", "compact")
        self.assertEqual(result.returncode, 0)

    def test_review_json(self):
        result = self._run("review", ".", "--emit", "json")
        self.assertEqual(result.returncode, 0)

    def test_review_nonexistent(self):
        result = self._run("review", "/nonexistent")
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
