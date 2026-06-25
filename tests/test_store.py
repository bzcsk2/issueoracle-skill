from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

import store


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        os.environ["DETECTORACLE_HOME"] = str(self.tmp)
        os.environ.pop("ISSUEORACLE_HOME", None)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("DETECTORACLE_HOME", None)
        os.environ.pop("ISSUEORACLE_HOME", None)

    def test_ensure_home(self):
        home = store.ensure_home()
        self.assertTrue(home.exists())
        self.assertTrue((home / "reports").exists())
        self.assertTrue((home / "mining").exists())

    def test_save_experience_writes_canonical_bugplay_paths(self):
        bugplay_dir = store.save_experience("# Test", '{"experiences": []}')
        self.assertEqual(bugplay_dir, self.tmp / "bugplay")
        self.assertTrue((self.tmp / "bugplay" / "bug-experience.md").exists())
        self.assertTrue((self.tmp / "bugplay" / "experience.json").exists())
        self.assertEqual(store.resolve_experience_json_path(), self.tmp / "bugplay" / "experience.json")

    def test_resolve_experience_json_path_accepts_legacy_candidates_path(self):
        legacy = self.tmp / "bugplay" / "candidates"
        legacy.mkdir(parents=True)
        legacy_path = legacy / "experience.json"
        legacy_path.write_text('{"experiences": []}', encoding="utf-8")
        self.assertEqual(store.resolve_experience_json_path(), legacy_path)

    def test_save_report(self):
        md_path, json_path = store.save_report("# Test", '{"test": 1}', "test-repo")
        self.assertTrue(md_path.exists())
        self.assertTrue(json_path.exists())
        self.assertIn("test-repo", md_path.name)

    def test_save_mining(self):
        mining_dir = store.save_mining('{"candidates": []}', "test_repo")
        self.assertTrue(mining_dir.exists())
        self.assertTrue((mining_dir / "result.json").exists())
        self.assertTrue((mining_dir / "raw").exists())
        self.assertTrue((mining_dir / "candidates").exists())

    def test_write_last_run(self):
        store.write_last_run({"command": "test"})
        last_run = self.tmp / "last-run.json"
        self.assertTrue(last_run.exists())


if __name__ == "__main__":
    unittest.main()
