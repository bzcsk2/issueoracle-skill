from __future__ import annotations

import unittest
from pathlib import Path

from lib import profile, schema


class ClassifyProjectTypeTests(unittest.TestCase):
    def test_web_api_fastapi(self):
        prof = schema.RepoProfile(repo_path="/tmp", languages=["Python"], frameworks=["FastAPI"])
        self.assertEqual(profile.classify_project_type(prof), "web_api")

    def test_web_api_flask(self):
        prof = schema.RepoProfile(repo_path="/tmp", languages=["Python"], frameworks=["Flask"])
        self.assertEqual(profile.classify_project_type(prof), "web_api")

    def test_web_api_express(self):
        prof = schema.RepoProfile(
            repo_path="/tmp", languages=["TypeScript"], frameworks=["Express"]
        )
        self.assertEqual(profile.classify_project_type(prof), "web_api")

    def test_cli_click(self):
        prof = schema.RepoProfile(
            repo_path="/tmp", languages=["Python"], frameworks=[], dependencies=["click"]
        )
        self.assertEqual(profile.classify_project_type(prof), "cli")

    def test_cli_typer(self):
        prof = schema.RepoProfile(
            repo_path="/tmp", languages=["Python"], frameworks=[], dependencies=["typer"]
        )
        self.assertEqual(profile.classify_project_type(prof), "cli")

    def test_frontend_react(self):
        prof = schema.RepoProfile(repo_path="/tmp", languages=["JavaScript"], frameworks=["React"])
        self.assertEqual(profile.classify_project_type(prof), "frontend")

    def test_library_fallback(self):
        prof = schema.RepoProfile(
            repo_path="/tmp", languages=["Python"], frameworks=[], dependencies=["requests"]
        )
        self.assertEqual(profile.classify_project_type(prof), "library")

    def test_library_default(self):
        prof = schema.RepoProfile(
            repo_path="/tmp", languages=["Rust"], frameworks=[], dependencies=[]
        )
        self.assertEqual(profile.classify_project_type(prof), "library")


class InferSearchTopicsTests(unittest.TestCase):
    def test_fastapi_topics(self):
        prof = schema.RepoProfile(repo_path="/tmp", languages=["Python"], frameworks=["FastAPI"])
        topics = profile.infer_search_topics(prof)
        self.assertIn("fastapi", topics)
        self.assertTrue(len(topics) <= 5)

    def test_click_cli_topics(self):
        prof = schema.RepoProfile(repo_path="/tmp", languages=["Python"], frameworks=["click"])
        topics = profile.infer_search_topics(prof)
        self.assertIn("cli", topics)

    def test_fallback_to_project_type(self):
        prof = schema.RepoProfile(
            repo_path="/tmp", languages=["Rust"], frameworks=[], dependencies=[]
        )
        topics = profile.infer_search_topics(prof)
        self.assertIn("library", topics)
        self.assertNotIn("rust", topics)  # language names excluded from topics

    def test_pydantic_topics(self):
        prof = schema.RepoProfile(repo_path="/tmp", languages=["Python"], frameworks=["pydantic"])
        topics = profile.infer_search_topics(prof)
        self.assertIn("pydantic", topics)


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
