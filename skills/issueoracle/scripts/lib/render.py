from __future__ import annotations

import json
from typing import Any


def render_diagnose(data: dict) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def render_finding(finding: dict, idx: int) -> list[str]:
    lines: list[str] = []
    lines.append(f"### {idx}. {finding['title']}")
    lines.append(f"- **Severity**: {finding['severity']}")
    lines.append(f"- **Confidence**: {finding['confidence']}")
    lines.append(f"- **File**: `{finding['file']}:{finding['start_line']}-{finding['end_line']}`")
    lines.append(f"- **Pattern**: `{finding['matched_pattern']}`")
    lines.append(f"- **Trigger**: {finding['trigger_condition']}")
    if finding.get("local_evidence"):
        for ev in finding["local_evidence"][:3]:
            lines.append(f"  - Line {ev['line']}: {ev['description']}")
    if finding.get("oss_evidence"):
        for ev in finding["oss_evidence"][:2]:
            lines.append(f"  - OSS: [{ev['repo']}#{ev['issue']}]({ev['url']})")
    lines.append(f"- **Suggested fix**: {finding['suggested_fix']}")
    lines.append(f"- **Validation**: {finding['validation']}")
    lines.append(f"- **False-positive boundary**: {finding['false_positive_boundary']}")
    lines.append("")
    return lines


def render_review(report: dict) -> str:
    lines: list[str] = []
    lines.append("# IssueOracle Review Report")
    lines.append("")
    s = report.get("summary", {})
    lines.append(f"- **Scope**: {report.get('scope', {}).get('repo', 'unknown')}")
    lines.append(f"- **Mode**: {report.get('scope', {}).get('mode', 'full')}")
    lines.append(f"- **Patterns loaded**: {s.get('patterns_loaded', 0)}")
    lines.append(f"- **Files scanned**: {s.get('files_scanned', 0)}")
    lines.append(f"- **Findings**: {s.get('findings_total', 0)}")
    lines.append(f"- **Suppressed**: {s.get('suppressed', 0)}")
    by_sev = s.get("by_severity", {})
    if by_sev:
        lines.append(f"- **By severity**: {json.dumps(by_sev)}")
    lines.append("")
    for idx, f in enumerate(report.get("findings", []), 1):
        lines.extend(render_finding(f, idx))
    if report.get("suppressed"):
        lines.append("---")
        lines.append(f"## Suppressed Findings ({len(report['suppressed'])})")
        lines.append("")
        for idx, f in enumerate(report["suppressed"], 1):
            lines.extend(render_finding(f, idx))
    return "\n".join(lines)


def render_review_json(report: dict) -> str:
    return json.dumps(report, indent=2, default=str)


def render_review_compact(report: dict) -> str:
    lines: list[str] = []
    for f in report.get("findings", []):
        lines.append(
            f"[{f['severity']}] {f['file']}:{f['start_line']} "
            f"({f['confidence']}) {f['title']}"
        )
    return "\n".join(lines) if lines else "No findings."


def render_mining(result: dict, emit: str = "markdown") -> str:
    if emit == "json":
        return json.dumps(result, indent=2, default=str)
    lines: list[str] = []
    lines.append("# Mining Report")
    lines.append("")
    lines.append(f"- **Repo**: {result.get('repo', 'N/A')}")
    lines.append(f"- **Mined at**: {result.get('mined_at', 'N/A')}")
    lines.append(f"- **Issues searched**: {result.get('issues_searched', 0)}")
    lines.append(f"- **Issues kept (bug)**: {result.get('issues_kept', 0)}")
    lines.append(f"- **With linked PR**: {result.get('issues_with_pr', 0)}")
    lines.append(f"- **Candidates**: {len(result.get('candidates', []))}")
    lines.append("")
    for idx, c in enumerate(result.get("candidates", []), 1):
        lines.append(f"### {idx}. {c['id']}")
        lines.append(f"- **Issue**: #{c.get('source_issue', '?')}")
        lines.append(f"- **Bug type**: {c.get('bug_type', '?')}")
        lines.append(f"- **Root cause**: {c.get('root_cause', '?')}")
        lines.append(f"- **Confidence**: {c.get('confidence', 0.5)} (candidate)")
        signals = c.get("bad_code_signals", [])
        if signals:
            lines.append(f"- **Bad signals**: {', '.join(signals)}")
        ev = c.get("evidence", [])
        for e in ev:
            lines.append(f"- **Evidence**: [{e['repo']}#{e.get('issue', '?')}]({e['url']})")
        lines.append(f"- **False-positive boundary**: {c.get('false_positive_boundary', 'N/A')}")
        lines.append("")
    return "\n".join(lines)


def render_scan(profile: dict, candidates: list[dict], emit: str = "markdown") -> str:
    if emit == "json":
        return json.dumps({"profile": profile, "candidates": candidates}, indent=2, default=str)
    lines: list[str] = []
    lines.append("# IssueOracle Scan Report")
    lines.append("")
    lines.append("## Project Profile")
    lines.append(f"- **Languages**: {', '.join(profile.get('languages', []))}")
    lines.append(f"- **Frameworks**: {', '.join(profile.get('frameworks', []))}")
    lines.append(f"- **Project type**: {profile.get('project_type', 'unknown')}")
    lines.append(f"- **Risk surfaces**: {', '.join(profile.get('risk_surfaces', []))}")
    lines.append(f"- **Dependencies**: {', '.join(profile.get('dependencies', []))}")
    lines.append("")
    lines.append("## Recommended Similar Projects")
    lines.append("")
    if candidates:
        lines.append("| # | Repo | Stars | Description |")
        lines.append("|---|------|-------|-------------|")
        for i, c in enumerate(candidates, 1):
            desc = c.get("description", "")[:60]
            lines.append(f"| {i} | [{c['owner_repo']}]({c.get('url', '')}) | {c.get('stars', 0)} | {desc} |")
        lines.append("")
        repos = ",".join(c["owner_repo"] for c in candidates)
        lines.append("## Next Step")
        lines.append("Run mining on these projects to extract bug experience:")
        lines.append(f"```")
        lines.append(f"issueoracle.py mine {repos}")
        lines.append(f"```")
    else:
        lines.append("No similar projects found.")
    lines.append("")
    return "\n".join(lines)


def render_bug_experience(report: dict, emit: str = "markdown") -> str:
    if emit == "json":
        return json.dumps(report, indent=2, default=str)
    lines: list[str] = []
    lines.append("# Bug Experience Report")
    lines.append("")
    src = report.get("source_repos", [])
    lines.append(f"Mined from: {', '.join(src)}")
    lines.append(f"Date: {report.get('mined_at', 'unknown')}")
    lines.append(f"Total issues: {report.get('total_issues', 0)} | Bug issues: {report.get('bug_issues', 0)}")
    lines.append("")
    exp_by_type: dict[str, list[dict]] = {}
    for e in report.get("experiences", []):
        bt = e.get("bug_type", "general_bug")
        exp_by_type.setdefault(bt, []).append(e)
    for bug_type, items in exp_by_type.items():
        lines.append(f"## {bug_type.replace('_', ' ').title()} ({len(items)} bugs)")
        lines.append("")
        for idx, e in enumerate(items, 1):
            lines.append(f"### {idx}. {e.get('title', '?')}")
            if e.get("symptom"):
                lines.append(f"- **Symptom**: {e['symptom']}")
            if e.get("root_cause"):
                lines.append(f"- **Root cause**: {e['root_cause']}")
            if e.get("trigger_condition"):
                lines.append(f"- **Trigger condition**: {e['trigger_condition']}")
            sigs = e.get("bad_code_signals", [])
            if sigs:
                lines.append(f"- **Bad code signals**: `{'`, `'.join(sigs)}`")
            if e.get("fix"):
                lines.append(f"- **Fix**: {e['fix']}")
            ev = e.get("evidence", [])
            for ev_item in ev:
                lines.append(f"- **Evidence**: [{ev_item['repo']}#{ev_item.get('issue', '?')}]({ev_item['url']})")
            lines.append("")
    return "\n".join(lines)


def render_validation(result: dict, emit: str = "markdown") -> str:
    if emit == "json":
        return json.dumps(result, indent=2, default=str)
    lines: list[str] = []
    lines.append("# Validation Report")
    lines.append("")
    lines.append(f"- **Pack path**: {result.get('pack_path', 'N/A')}")
    lines.append(f"- **Valid patterns**: {result.get('patterns_valid', 0)}")
    lines.append(f"- **Invalid patterns**: {result.get('patterns_invalid', 0)}")
    for err in result.get("errors", []):
        lines.append(f"  - `{err.get('pattern_id', '?')}` in {err.get('file', '?')}: {err.get('errors', '?')}")
    return "\n".join(lines)
