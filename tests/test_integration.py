from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scripts_dir = Path(__file__).resolve().parent.parent / "skills" / "detectoracle" / "scripts"
        cls.script = scripts_dir / "issueoracle.py"
        cls.detectoracle_script = scripts_dir / "detectoracle.py"
        cls.packs = Path(__file__).resolve().parent.parent / "skills" / "detectoracle" / "packs"
        cls.python = sys.executable

    def _run(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run(
            [self.python, str(self.script)] + list(args),
            capture_output=True,
            text=True,
            timeout=30,
        )

    def _run_detectoracle(self, *args, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            [self.python, str(self.detectoracle_script)] + list(args),
            capture_output=True,
            env=env,
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

    def test_detectoracle_doctor_public_entrypoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["DETECTORACLE_HOME"] = tmp
            env.pop("ISSUEORACLE_HOME", None)
            result = self._run_detectoracle("doctor", env=env)

        self.assertIn("DETECTORACLE_HOME", result.stdout)
        self.assertIn("/detectoracle scan .", result.stdout)


if __name__ == "__main__":
    unittest.main()
