from __future__ import annotations

import unittest
import tempfile
from pathlib import Path

from lib import code_index, schema


class CodeIndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_index_python(self):
        pyfile = self.tmp / "test.py"
        pyfile.write_text("def foo():\n    pass\n\nclass Bar:\n    pass\n", encoding="utf-8")
        profile = schema.RepoProfile(repo_path=str(self.tmp), languages=["Python"])
        chunks = code_index.index_repo(str(self.tmp), profile)
        self.assertGreater(len(chunks), 0)
        symbols = [c.symbol for c in chunks]
        self.assertIn("foo", symbols)
        self.assertIn("Bar", symbols)

    def test_index_empty_dir(self):
        profile = schema.RepoProfile(repo_path=str(self.tmp), languages=["Python"])
        chunks = code_index.index_repo(str(self.tmp), profile)
        self.assertEqual(chunks, [])

    def test_language_for_suffix(self):
        self.assertEqual(code_index._language_for_suffix(".py"), "Python")
        self.assertEqual(code_index._language_for_suffix(".ts"), "TypeScript")
        self.assertEqual(code_index._language_for_suffix(".js"), "JavaScript")
        self.assertEqual(code_index._language_for_suffix(".unknown"), "Unknown")

    def test_extract_signals(self):
        text = "async def foo():\n    await session.query()"
        signals = code_index._extract_signals(text)
        self.assertIn("async", signals)
        self.assertIn("session", signals)
        self.assertIn("query(", signals)
        self.assertIn("await", signals)


if __name__ == "__main__":
    unittest.main()
