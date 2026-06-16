from __future__ import annotations

import unittest

from lib import git


class GitTests(unittest.TestCase):
    def test_check_git_available(self):
        result = git.check_git_available()
        self.assertIsInstance(result, bool)

    def test_is_git_repo(self):
        result = git.is_git_repo(".")
        self.assertTrue(result)

    def test_get_changed_files(self):
        files = git.get_changed_files(".")
        self.assertIsInstance(files, list)


if __name__ == "__main__":
    unittest.main()
