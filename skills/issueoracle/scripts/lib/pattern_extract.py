from __future__ import annotations

import re
from typing import Any

from lib import safety, schema


def extract_candidate(
    issue: schema.GitHubIssue,
    prs: list[schema.LinkedPR],
    owner_repo: str,
    language_hint: str = "",
) -> schema.CandidatePattern | None:
    root_cause = _extract_root_cause(issue, prs)
    if not root_cause:
        return None
    signals = _extract_signals(issue.body)
    fixes = _extract_fixes(prs)
    triggers = _infer_triggers(issue, signals)
    pid = f"mined-{owner_repo.replace('/', '-')}-{issue.number}"
    return schema.CandidatePattern(
        id=pid,
        title=issue.title,
        language=language_hint or _guess_language(owner_repo),
        frameworks=_guess_frameworks(owner_repo),
        bug_type=_classify_bug_type(issue.title, signals),
        severity_hint="medium",
        symptoms=_extract_symptoms(issue.body),
        root_cause=root_cause,
        trigger_conditions=triggers,
        bad_code_signals=signals,
        fix_patterns=fixes,
        evidence=safety.build_safe_evidence(issue, prs, owner_repo),
        confidence=0.5,
        false_positive_boundary=(
            "This candidate was auto-extracted from a single OSS issue. "
            "Verify the trigger condition applies to your codebase before trusting it."
        ),
        source_issue=issue.number,
        source_repo=owner_repo,
        status="candidate",
    )


def _extract_root_cause(issue: schema.GitHubIssue, prs: list[schema.LinkedPR]) -> str:
    for pr in prs:
        if pr.title.lower().startswith(("fix", "fixes", "fix:", "fixes:")):
            parts = pr.title.split(":", 1)
            if len(parts) > 1:
                return parts[-1].strip()
    return issue.title


def _extract_signals(body: str) -> list[str]:
    signals: list[str] = []
    keywords = ("await ", "async ", "session", "query(", "execute(", "fetch(",
                ".all()", "commit()", "rollback()")
    for block in re.findall(r"```(?:python|typescript|go|rust|js|ts)?\n(.*?)```", body, re.DOTALL):
        for kw in keywords:
            if kw in block:
                signals.append(kw.strip())
    return list(dict.fromkeys(signals))[:5]


def _extract_fixes(prs: list[schema.LinkedPR]) -> list[str]:
    fixes: list[str] = []
    for pr in prs:
        title = pr.title.strip()
        if title.lower().startswith(("fix", "fixes")):
            fixes.append(f"PR #{pr.number}: {title}")
        else:
            fixes.append(f"PR #{pr.number}: {title}")
    return fixes[:3]


def _infer_triggers(issue: schema.GitHubIssue, signals: list[str]) -> list[schema.TriggerCondition]:
    triggers: list[schema.TriggerCondition] = []
    if signals:
        triggers.append(schema.TriggerCondition(
            description=f"Code containing: {', '.join(signals[:3])}",
            code_signals=signals[:3],
        ))
    if "leak" in issue.title.lower() or "session" in issue.title.lower():
        triggers.append(schema.TriggerCondition(
            description="Resource cleanup may be missing",
            code_signals=["session", "close"],
        ))
    return triggers if triggers else [schema.TriggerCondition(description="Review the issue for context")]


def _extract_symptoms(body: str) -> list[str]:
    symptoms: list[str] = []
    lines = body.split("\n")[:20]
    for line in lines:
        line = line.strip()
        if line.startswith("-") or line.startswith("*"):
            symptoms.append(line.lstrip("-* ").strip()[:120])
    return symptoms[:5]


def _guess_language(owner_repo: str) -> str:
    repo_lower = owner_repo.lower()
    if any(x in repo_lower for x in ("py", "python", "django", "flask", "fastapi", "sqlalchemy")):
        return "Python"
    if any(x in repo_lower for x in ("ts", "js", "node", "express", "react", "next", "angular")):
        return "TypeScript"
    if any(x in repo_lower for x in ("go", "golang")):
        return "Go"
    if any(x in repo_lower for x in ("rs", "rust")):
        return "Rust"
    return "Python"


def _guess_frameworks(owner_repo: str) -> list[str]:
    repo_lower = owner_repo.lower()
    fw: list[str] = []
    if "fastapi" in repo_lower:
        fw.append("fastapi")
    if "django" in repo_lower:
        fw.append("django")
    if "flask" in repo_lower:
        fw.append("flask")
    if "sqlalchemy" in repo_lower:
        fw.append("sqlalchemy")
    if "express" in repo_lower:
        fw.append("express")
    if "react" in repo_lower:
        fw.append("react")
    if "next" in repo_lower:
        fw.append("nextjs")
    return fw


_BUG_TYPES = [
    ("leak", "resource_leak"),
    ("injection", "injection"),
    ("sql", "sql_injection"),
    ("xss", "xss"),
    ("crash", "crash"),
    ("deadlock", "deadlock"),
    ("race", "race_condition"),
    ("overflow", "buffer_overflow"),
    ("auth", "auth_bypass"),
    ("permission", "auth_bypass"),
    ("cors", "misconfiguration"),
    ("ssl", "misconfiguration"),
    ("timeout", "performance"),
    ("memory", "resource_leak"),
    ("hang", "crash"),
    ("regression", "regression"),
]


def _classify_bug_type(title: str, signals: list[str]) -> str:
    title_lower = title.lower()
    for keyword, bug_type in _BUG_TYPES:
        if keyword in title_lower:
            return bug_type
    for signal in signals:
        if "session" in signal or "close" in signal or "rollback" in signal:
            return "resource_leak"
        if "query" in signal or "execute" in signal or "fetch" in signal:
            return "sql_injection"
    return "general_bug"
