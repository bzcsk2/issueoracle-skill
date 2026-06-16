from __future__ import annotations

import uuid

from lib import pattern_match, schema

SEVERITY_THRESHOLD = {"low": 0.3, "medium": 0.5, "high": 0.7}


def build_findings(
    matches: list[pattern_match.MatchResult],
    threshold: str,
    max_findings: int,
) -> tuple[list[schema.Finding], list[schema.Finding]]:
    findings: list[schema.Finding] = []
    suppressed: list[schema.Finding] = []
    threshold_val = SEVERITY_THRESHOLD.get(threshold, 0.5)

    for m in matches:
        if m.score < threshold_val:
            continue
        f = _to_finding(m)
        if not f.file or not f.matched_pattern or not f.trigger_condition:
            suppressed.append(f)
            continue
        if f.confidence < threshold_val:
            suppressed.append(f)
            continue
        findings.append(f)

    findings.sort(key=lambda x: x.confidence, reverse=True)
    return findings[:max_findings], suppressed + findings[max_findings:]


def _to_finding(m: pattern_match.MatchResult) -> schema.Finding:
    trigger_desc = ""
    if m.pattern.trigger_conditions:
        trigger_desc = m.pattern.trigger_conditions[0].description

    local_evidence = [
        schema.LocalEvidence(line=m.chunk.start_line, description=sig) for sig in m.signal_hits[:5]
    ]

    return schema.Finding(
        id=str(uuid.uuid4())[:8],
        severity=m.pattern.severity_hint,
        confidence=round(m.score, 2),
        file=m.chunk.file,
        start_line=m.chunk.start_line,
        end_line=m.chunk.end_line,
        title=m.pattern.title,
        matched_pattern=m.pattern.id,
        trigger_condition=trigger_desc,
        local_evidence=local_evidence,
        oss_evidence=m.pattern.evidence,
        suggested_fix="\n".join(m.pattern.fix_patterns)
        if m.pattern.fix_patterns
        else "Review the matched pattern.",
        validation="See fix patterns above.",
        false_positive_boundary=m.pattern.false_positive_boundary,
    )
