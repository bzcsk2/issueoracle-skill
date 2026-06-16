from __future__ import annotations

import json
from pathlib import Path

import pytest

from lib import schema
from lib import experience as exp_mod

SAMPLE_EVIDENCE = [schema.OssEvidence(repo="test/repo", issue=42, url="https://github.com/test/repo/issues/42", pr_url="")]
SAMPLE_CANDIDATES = [
    schema.CandidatePattern(
        id="bug-001", title="Missing validation",
        language="Python", bug_type="validation_bug",
        symptoms=["Input not validated"],
        root_cause="No input check", trigger_conditions=[],
        bad_code_signals=["if", "validate"],
        fix_patterns=["add check function"],
        evidence=SAMPLE_EVIDENCE, confidence=0.8,
        frameworks=[], false_positive_boundary="test",
        source_issue=1, source_repo="test/repo",
    ),
]


class TestAggregate:
    def test_aggregate_empty(self):
        report = exp_mod.aggregate([], ["test/repo"])
        assert len(report.experiences) == 0
        assert report.source_repos == ["test/repo"]

    def test_aggregate_with_candidates(self):
        report = exp_mod.aggregate(SAMPLE_CANDIDATES, ["test/repo"],
                                   total_issues=10, bug_issues=3)
        assert len(report.experiences) == 1
        assert report.total_issues == 10
        assert report.bug_issues == 3
        assert report.experiences[0].id == "bug-001"

    def test_aggregate_fields_mapped(self):
        report = exp_mod.aggregate(SAMPLE_CANDIDATES, ["test/repo"])
        be = report.experiences[0]
        assert be.title == "Missing validation"
        assert be.symptom == "Input not validated"
        assert be.root_cause == "No input check"
        assert be.bug_type == "validation_bug"
        assert be.confidence == 0.8


class TestToMarkdown:
    def test_markdown_empty(self):
        report = schema.ExperienceReport(source_repos=["test/repo"])
        md = exp_mod.to_markdown(report)
        assert "Bug Experience Report" in md
        assert "test/repo" in md

    def test_markdown_with_experiences(self):
        report = exp_mod.aggregate(SAMPLE_CANDIDATES, ["test/repo"])
        md = exp_mod.to_markdown(report)
        assert "Missing validation" in md
        assert "Input not validated" in md
        assert "No input check" in md
        assert "Validation Bug" in md
        assert "test/repo#42" in md

    def test_markdown_signal_formatting(self):
        cand = schema.CandidatePattern(
            id="bug-002", title="SQL injection",
            language="Python", bug_type="security_bug",
            symptoms=["SQL injection risk"],
            root_cause="Raw query building", trigger_conditions=[],
            bad_code_signals=["execute(", "raw sql"],
            fix_patterns=["Use parameterized queries"],
            evidence=SAMPLE_EVIDENCE, confidence=0.9,
            frameworks=[], false_positive_boundary="test",
            source_issue=2, source_repo="test/repo",
        )
        report = exp_mod.aggregate([cand], ["test/repo"])
        md = exp_mod.to_markdown(report)
        assert "`execute(`" in md
        assert "`raw sql`" in md


class TestLoadAsPatterns:
    def test_load_nonexistent(self):
        assert exp_mod.load_as_patterns("nonexistent.json") == []

    def test_load_empty_json(self, tmp_path: Path):
        f = tmp_path / "exp.json"
        f.write_text('{"experiences": []}', encoding="utf-8")
        patterns = exp_mod.load_as_patterns(str(f))
        assert patterns == []

    def test_load_with_experience_json(self, tmp_path: Path):
        data = {
            "experiences": [{
                "id": "exp-1", "title": "Null pointer",
                "symptom": "Crash on null", "root_cause": "Missing null check",
                "trigger_condition": "When input is None",
                "bad_code_signals": ["null check", "if"],
                "fix": "Add null guard",
                "evidence": [{"repo": "test/repo", "issue": 42, "url": "https://github.com/test/repo/issues/42", "pr_url": ""}],
                "bug_type": "null_bug", "language": "Python",
                "frameworks": [], "confidence": 0.8,
            }]
        }
        f = tmp_path / "exp.json"
        f.write_text(json.dumps(data, indent=2), encoding="utf-8")
        patterns = exp_mod.load_as_patterns(str(f))
        assert len(patterns) == 1
        assert patterns[0].id == "exp-exp-1"
        assert "Null pointer" in patterns[0].title
        assert patterns[0].language == "Python"

    def test_load_markdown(self, tmp_path: Path):
        md = """# Bug Experience Report

## Null Bug (1 bugs)

### 1. Null pointer issue
- **Symptom**: App crashes on null input
- **Root cause**: Missing null check
- **Trigger condition**: input is None
- **Bad code signals**: `null check`, `if guard`
- **Fix**: Add null check before dereference
- **Evidence**: test/repo#42
"""
        f = tmp_path / "exp.md"
        f.write_text(md, encoding="utf-8")
        patterns = exp_mod.load_as_patterns(str(f))
        assert len(patterns) >= 1
        assert "Null pointer" in patterns[0].title


class TestBugExperienceToPattern:
    def test_minimal(self):
        be = schema.BugExperience(id="x1", title="test")
        pattern = exp_mod._bug_experience_to_pattern(be)
        assert pattern is None

    def test_with_signals(self):
        ev = schema.OssEvidence(repo="test/repo", issue=1, url="u", pr_url="")
        be = schema.BugExperience(
            id="x1", title="test", root_cause="bad init",
            bad_code_signals=["init", "config"],
            trigger_condition="on startup",
            evidence=[ev],
        )
        pattern = exp_mod._bug_experience_to_pattern(be)
        assert pattern is not None
        assert len(pattern.trigger_conditions) == 1
        assert pattern.trigger_conditions[0].code_signals == ["init", "config"]


class TestExperienceDrivenReview:
    """Integration test: experience.json → Pattern → review pipeline producing findings."""

    EXPERIENCE_JSON = {
        "source_repos": ["test/repo"],
        "mined_at": "2026-06-16T00:00:00",
        "total_issues": 1,
        "bug_issues": 1,
        "experiences": [{
            "id": "missing-finally-1",
            "title": "Session not closed on exception path",
            "symptom": "Connection pool exhaustion",
            "root_cause": "Session opened without finally block",
            "trigger_condition": "DB session opened without finally",
            "bad_code_signals": ["session", "query(", "execute("],
            "fix": "Wrap in try/finally",
            "evidence": [
                {"repo": "test/repo", "issue": 42,
                 "url": "https://github.com/test/repo/issues/42", "pr_url": ""},
            ],
            "bug_type": "resource_leak",
            "language": "Python",
            "frameworks": ["FastAPI", "SQLAlchemy"],
            "confidence": 0.8,
        }],
    }

    BAD_CODE = '''from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

app = FastAPI()
engine = create_engine("sqlite:///test.db")

@app.get("/users")
def get_users():
    session = Session(engine)
    result = session.query("SELECT * FROM users").all()
    return {"users": result}
'''

    GOOD_CODE = '''from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

app = FastAPI()
engine = create_engine("sqlite:///test.db")

@app.get("/users")
def get_users():
    session = Session(engine)
    try:
        result = session.query("SELECT * FROM users").all()
        return {"users": result}
    finally:
        session.close()
'''

    @pytest.fixture
    def experience_file(self, tmp_path: Path) -> Path:
        f = tmp_path / "experience.json"
        f.write_text(json.dumps(self.EXPERIENCE_JSON, indent=2), encoding="utf-8")
        return f

    @pytest.fixture
    def bad_project(self, tmp_path: Path) -> Path:
        d = tmp_path / "bad_project"
        d.mkdir()
        (d / "app.py").write_text(self.BAD_CODE, encoding="utf-8")
        return d

    @pytest.fixture
    def good_project(self, tmp_path: Path) -> Path:
        d = tmp_path / "good_project"
        d.mkdir()
        (d / "app.py").write_text(self.GOOD_CODE, encoding="utf-8")
        return d

    def test_bad_code_produces_findings(self, experience_file: Path, bad_project: Path):
        from lib import code_index, pack_loader, pattern_match, profile, review

        patterns = exp_mod.load_as_patterns(str(experience_file))
        assert len(patterns) == 1

        prof = profile.profile_repo(str(bad_project))
        chunks = code_index.index_repo(str(bad_project), prof)
        matches = pattern_match.match(chunks, patterns, prof)
        findings, _ = review.build_findings(matches, "low", 20)

        assert len(findings) > 0, (
            "Experience-driven review should produce findings for bad code. "
            f"Got {len(matches)} matches, {len(findings)} findings."
        )
        assert any("session" in str(f) for f in findings)

    def test_experience_loads_and_matches(self, experience_file: Path, bad_project: Path):
        patterns = exp_mod.load_as_patterns(str(experience_file))
        assert len(patterns) == 1
        p = patterns[0]
        assert "session not closed" in p.title.lower()
        assert "session" in p.bad_code_signals
        assert len(p.evidence) == 1


class TestPatternExtractSignalsEnhanced:
    def test_extract_from_title(self):
        from lib.pattern_extract import _extract_signals
        signals = _extract_signals("", title="async session timeout error")
        assert "async " in signals or "session" in signals or "timeout" in signals

    def test_extract_from_pr_titles(self):
        from lib.pattern_extract import _extract_signals
        signals = _extract_signals("", title="fix", pr_titles=["fix async session timeout"])
        assert len(signals) > 0
