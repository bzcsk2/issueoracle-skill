from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Severity = Literal["low", "medium", "high", "critical"]
Strength = Literal["low", "medium", "high"]


class OssEvidence(BaseModel):
    repo: str
    issue: int | None = None
    pr: int | None = None
    commit: str | None = None
    url: str
    strength: Strength = "medium"


class TriggerCondition(BaseModel):
    description: str
    code_signals: list[str] = Field(default_factory=list)


class Pattern(BaseModel):
    id: str
    title: str
    language: str
    frameworks: list[str] = Field(default_factory=list)
    bug_type: str
    severity_hint: Severity = "medium"
    symptoms: list[str] = Field(default_factory=list)
    root_cause: str
    trigger_conditions: list[TriggerCondition] = Field(default_factory=list)
    bad_code_signals: list[str] = Field(default_factory=list)
    fix_patterns: list[str] = Field(default_factory=list)
    evidence: list[OssEvidence] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    false_positive_boundary: str = ""

    @field_validator("evidence")
    @classmethod
    def evidence_non_empty(cls, v):
        if not v:
            raise ValueError("pattern must have at least one OSS evidence")
        return v


class CodeChunk(BaseModel):
    file: str
    start_line: int
    end_line: int
    symbol: str
    language: str
    imports: list[str] = Field(default_factory=list)
    signals: list[str] = Field(default_factory=list)
    code_excerpt: str = ""


class RepoProfile(BaseModel):
    repo_path: str
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    package_managers: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    risk_surfaces: list[str] = Field(default_factory=list)
    changed_files: list[str] = Field(default_factory=list)


class LocalEvidence(BaseModel):
    line: int
    description: str


class Finding(BaseModel):
    id: str
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    file: str
    start_line: int
    end_line: int
    title: str
    matched_pattern: str
    trigger_condition: str
    local_evidence: list[LocalEvidence] = Field(default_factory=list)
    oss_evidence: list[OssEvidence] = Field(default_factory=list)
    suggested_fix: str
    validation: str
    false_positive_boundary: str


class ReviewReport(BaseModel):
    version: str
    scope: dict
    summary: dict
    findings: list[Finding]
    suppressed: list[Finding]


class GitHubIssue(BaseModel):
    number: int
    title: str
    state: str
    labels: list[str] = Field(default_factory=list)
    body: str = ""
    url: str
    created_at: str
    closed_at: str | None = None
    author: str = ""


class LinkedPR(BaseModel):
    number: int
    title: str
    state: str
    merged: bool
    url: str
    commit_sha: str | None = None
    files_changed: list[str] = Field(default_factory=list)


class CandidatePattern(BaseModel):
    id: str
    title: str
    language: str
    frameworks: list[str] = Field(default_factory=list)
    bug_type: str
    severity_hint: Severity = "medium"
    symptoms: list[str] = Field(default_factory=list)
    root_cause: str
    trigger_conditions: list[TriggerCondition] = Field(default_factory=list)
    bad_code_signals: list[str] = Field(default_factory=list)
    fix_patterns: list[str] = Field(default_factory=list)
    evidence: list[OssEvidence]
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    false_positive_boundary: str = ""
    source_issue: int
    source_repo: str
    status: Literal["candidate", "approved", "rejected"] = "candidate"


class MiningResult(BaseModel):
    repo: str
    mined_at: str
    issues_searched: int
    issues_kept: int
    issues_with_pr: int
    candidates: list[CandidatePattern]
    raw_dir: str
    review_path: str


class ProjectProfile(BaseModel):
    repo_path: str
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    risk_surfaces: list[str] = Field(default_factory=list)
    project_type: str = ""
    search_topics: list[str] = Field(default_factory=list)


class RepoCandidate(BaseModel):
    owner_repo: str
    stars: int = 0
    description: str = ""
    url: str = ""
    topics: list[str] = Field(default_factory=list)


class BugExperience(BaseModel):
    id: str
    title: str
    symptom: str = ""
    root_cause: str = ""
    trigger_condition: str = ""
    bad_code_signals: list[str] = Field(default_factory=list)
    fix: str = ""
    evidence: list[OssEvidence] = Field(default_factory=list)
    bug_type: str = "general_bug"
    language: str = ""
    frameworks: list[str] = Field(default_factory=list)
    confidence: float = 0.5
    status: Literal["candidate", "reviewed", "approved", "rejected"] = "candidate"
    review_notes: list[str] = Field(default_factory=list)
    approved_by: str | None = None
    approved_at: str | None = None


class ExperienceReport(BaseModel):
    schema_version: str = "1"
    source_repos: list[str] = Field(default_factory=list)
    mined_at: str = ""
    total_issues: int = 0
    bug_issues: int = 0
    experiences: list[BugExperience] = Field(default_factory=list)


class ValidationResult(BaseModel):
    pack_path: str
    patterns_valid: int
    patterns_invalid: int
    errors: list[dict]
