from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from lib import schema


def aggregate(candidates: list[schema.CandidatePattern], source_repos: list[str],
              total_issues: int = 0, bug_issues: int = 0) -> schema.ExperienceReport:
    experiences: list[schema.BugExperience] = []
    for c in candidates:
        symptom = c.symptoms[0] if c.symptoms else ""
        trigger_desc = c.trigger_conditions[0].description if c.trigger_conditions else ""
        fix = c.fix_patterns[0] if c.fix_patterns else ""
        experiences.append(schema.BugExperience(
            id=c.id,
            title=c.title,
            symptom=symptom,
            root_cause=c.root_cause,
            trigger_condition=trigger_desc,
            bad_code_signals=c.bad_code_signals,
            fix=fix,
            evidence=c.evidence,
            bug_type=c.bug_type,
            language=c.language,
            frameworks=c.frameworks,
            confidence=c.confidence,
        ))
    import datetime
    return schema.ExperienceReport(
        source_repos=source_repos,
        mined_at=datetime.datetime.now().isoformat(),
        total_issues=total_issues,
        bug_issues=bug_issues,
        experiences=experiences,
    )


def to_markdown(report: schema.ExperienceReport) -> str:
    lines: list[str] = []
    lines.append("# Bug Experience Report")
    lines.append("")
    lines.append(f"Mined from: {', '.join(report.source_repos)}")
    lines.append(f"Date: {report.mined_at[:10]}")
    lines.append(f"Total issues analyzed: {report.total_issues} | Bug issues: {report.bug_issues}")
    lines.append("")
    by_type: dict[str, list[schema.BugExperience]] = {}
    for e in report.experiences:
        by_type.setdefault(e.bug_type, []).append(e)
    for bug_type, items in by_type.items():
        label = bug_type.replace("_", " ").title()
        lines.append(f"## {label} ({len(items)} bugs)")
        lines.append("")
        for idx, e in enumerate(items, 1):
            lines.append(f"### {idx}. {e.title}")
            if e.symptom:
                lines.append(f"- **Symptom**: {e.symptom}")
            if e.root_cause:
                lines.append(f"- **Root cause**: {e.root_cause}")
            if e.trigger_condition:
                lines.append(f"- **Trigger condition**: {e.trigger_condition}")
            if e.bad_code_signals:
                lines.append(f"- **Bad code signals**: `{'`, `'.join(e.bad_code_signals)}`")
            if e.fix:
                lines.append(f"- **Fix**: {e.fix}")
            for ev in e.evidence:
                lines.append(f"- **Evidence**: [{ev.repo}#{ev.issue or ''}]({ev.url})")
            lines.append("")
    return "\n".join(lines)


def load_as_patterns(path: str | Path) -> list[schema.Pattern]:
    p = Path(path)
    if not p.exists():
        return []
    data: dict[str, Any] = {}
    if p.suffix == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
    else:
        return _parse_markdown_experience(p)

    patterns: list[schema.Pattern] = []
    for exp_data in data.get("experiences", []):
        be = schema.BugExperience(**exp_data)
        pattern = _bug_experience_to_pattern(be)
        if pattern:
            patterns.append(pattern)
    return patterns


def _bug_experience_to_pattern(be: schema.BugExperience) -> schema.Pattern | None:
    if not be.bad_code_signals and not be.root_cause:
        return None
    if not be.evidence:
        return None
    triggers = []
    if be.trigger_condition:
        triggers.append(schema.TriggerCondition(
            description=be.trigger_condition,
            code_signals=be.bad_code_signals[:5],
        ))
    return schema.Pattern(
        id=f"exp-{be.id}",
        title=be.title,
        language=be.language or "Python",
        frameworks=be.frameworks,
        bug_type=be.bug_type,
        symptoms=[be.symptom] if be.symptom else [],
        root_cause=be.root_cause,
        trigger_conditions=triggers,
        bad_code_signals=be.bad_code_signals,
        fix_patterns=[be.fix] if be.fix else [],
        evidence=be.evidence,
        confidence=be.confidence,
        false_positive_boundary="Auto-generated from mined experience. Verify before trusting.",
    )


_MD_PATTERN = re.compile(
    r"### \d+\.\s*(?P<title>.+?)\s*\n"
    r"(?P<fields>(?:\- \*\*[^:]+?\*\*: .+?\n)+)",
    re.MULTILINE,
)


def _parse_markdown_experience(path: Path) -> list[schema.Pattern]:
    text = path.read_text(encoding="utf-8")
    patterns: list[schema.Pattern] = []
    for match in _MD_PATTERN.finditer(text):
        title = match.group("title").strip()
        fields_text = match.group("fields")
        fields: dict[str, str] = {}
        sigs: list[str] = []
        evidence_list: list[schema.OssEvidence] = []
        for line in fields_text.strip().split("\n"):
            m = re.match(r"- \*\*(.+?)\*\*: (.+)", line)
            if m:
                key = m.group(1).lower().replace(" ", "_")
                val = m.group(2).strip()
                if key == "bad_code_signals":
                    sigs = [s.strip().strip("`") for s in val.split("`, `")]
                elif key == "evidence":
                    for part in val.split(","):
                        part = part.strip()
                        # strip markdown link: [repo#n](url) -> repo#n
                        link_m = re.match(r"\[(.+?)\]\(.+?\)", part)
                        if link_m:
                            part = link_m.group(1)
                        m2 = re.match(r"(.+?)/(.+?)#(\d+)", part)
                        if m2:
                            evidence_list.append(schema.OssEvidence(
                                repo=f"{m2.group(1)}/{m2.group(2)}",
                                issue=int(m2.group(3)),
                                url=f"https://github.com/{m2.group(1)}/{m2.group(2)}/issues/{m2.group(3)}",
                                pr_url="",
                            ))
                else:
                    fields[key] = val
        if not evidence_list:
            continue
        triggers = []
        if fields.get("trigger_condition"):
            triggers.append(schema.TriggerCondition(
                description=fields["trigger_condition"],
                code_signals=sigs[:5],
            ))
        patterns.append(schema.Pattern(
            id=f"exp-{title[:20]}",
            title=title,
            language=fields.get("language", "Python"),
            bug_type=fields.get("bug_type", "general_bug").replace(" ", "_").lower(),
            root_cause=fields.get("root_cause", ""),
            trigger_conditions=triggers,
            bad_code_signals=sigs,
            fix_patterns=[fields.get("fix", "")] if fields.get("fix") else [],
            evidence=evidence_list,
            confidence=float(fields.get("confidence", 0.5)),
            false_positive_boundary="Auto-generated from mined experience.",
        ))
    return patterns
