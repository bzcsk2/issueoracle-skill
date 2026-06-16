from __future__ import annotations

import unittest
from pathlib import Path

from lib import profile


class ProfileTests(unittest.TestCase):
    def test_profile_self(self):
        p = profile.profile_repo(".")
        self.assertIsInstance(p.languages, list)
        self.assertIsInstance(p.frameworks, list)
        self.assertIsInstance(p.dependencies, list)
        self.assertIsInstance(p.risk_surfaces, list)
        self.assertTrue("Python" in p.languages or not p.languages)

    def test_profile_with_changed(self):
        p = profile.profile_repo(".", changed_files=["test_schema.py"])
        self.assertIn("test_schema.py", p.changed_files)

    def test_detect_languages(self):
        repo = Path(".").resolve()
        langs = profile._detect_languages(repo)
        self.assertIsInstance(langs, list)

    def test_detect_frameworks(self):
        repo = Path(".").resolve()
        fws = profile._detect_frameworks(repo)
        self.assertIsInstance(fws, list)


if __name__ == "__main__":
    unittest.main()
