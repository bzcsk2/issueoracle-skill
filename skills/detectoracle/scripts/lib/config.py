from __future__ import annotations

from pydantic import BaseModel


class IssueOracleConfig(BaseModel):
    github_token: str | None = None
    allow_remote_llm: bool = False
    severity_threshold: str = "medium"
    max_findings: int = 20
