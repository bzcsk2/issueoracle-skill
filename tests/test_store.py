from __future__ import annotations

import unittest
import tempfile
from pathlib import Path

import store


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        import os
        os.environ["ISSUEORACLE_HOME"] = str(self.tmp)

    def tearDown(self):
        import shutil
        import os
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("ISSUEORACLE_HOME", None)

    def test_ensure_home(self):
        home = store.ensure_home()
        self.assertTrue(home.exists())
        self.assertTrue((home / "reports").exists())
        self.assertTrue((home / "mining").exists())

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
