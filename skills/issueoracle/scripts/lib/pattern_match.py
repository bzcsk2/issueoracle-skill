from __future__ import annotations

from dataclasses import dataclass

from lib import schema


@dataclass
class MatchResult:
    pattern: schema.Pattern
    chunk: schema.CodeChunk
    signal_hits: list[str]
    trigger_coverage: float
    score: float


def match(
    chunks: list[schema.CodeChunk],
    patterns: list[schema.Pattern],
    profile: schema.RepoProfile,
) -> list[MatchResult]:
    results: list[MatchResult] = []
    for pattern in patterns:
        if not _metadata_recall(pattern, profile):
            continue
        for chunk in chunks:
            signal_hits = _match_signals(pattern.bad_code_signals, chunk)
            if not signal_hits:
                continue
            trigger_cov = _trigger_coverage(pattern.trigger_conditions, chunk)
            if trigger_cov == 0.0:
                continue
            score = _score(pattern, signal_hits, trigger_cov)
            results.append(
                MatchResult(
                    pattern=pattern,
                    chunk=chunk,
                    signal_hits=signal_hits,
                    trigger_coverage=trigger_cov,
                    score=score,
                )
            )
    results.sort(key=lambda r: r.score, reverse=True)
    return results


def _metadata_recall(pattern: schema.Pattern, profile: schema.RepoProfile) -> bool:
    if pattern.language not in profile.languages:
        if pattern.language == "TypeScript":
            if "JavaScript" not in profile.languages:
                return False
        elif pattern.language == "Python":
            if "Python" not in profile.languages:
                return False
        else:
            return False
    if not pattern.frameworks or not profile.frameworks:
        return True
    return any(f.lower() in [pf.lower() for pf in profile.frameworks] for f in pattern.frameworks)


def _match_signals(bad_signals: list[str], chunk: schema.CodeChunk) -> list[str]:
    hits: list[str] = []
    chunk_text = chunk.code_excerpt.lower()
    chunk_signals = [s.lower() for s in chunk.signals]
    for signal in bad_signals:
        sig_lower = signal.lower()
        if sig_lower in chunk_text or sig_lower in chunk_signals:
            hits.append(signal)
    return hits


def _trigger_coverage(triggers: list[schema.TriggerCondition], chunk: schema.CodeChunk) -> float:
    if not triggers:
        return 1.0
    covered = 0
    chunk_text = chunk.code_excerpt.lower()
    for trigger in triggers:
        sigs = trigger.code_signals
        if not sigs:
            covered += 1
            continue
        if any(s.lower() in chunk_text for s in sigs):
            covered += 1
    return covered / len(triggers)


def _evidence_strength(pattern: schema.Pattern) -> float:
    if not pattern.evidence:
        return 0.0
    strengths = {"low": 0.3, "medium": 0.6, "high": 1.0}
    total = 0.0
    for ev in pattern.evidence:
        total += strengths.get(ev.strength, 0.5)
    return min(1.0, total / len(pattern.evidence))


def _score(pattern: schema.Pattern, signal_hits: list[str], trigger_cov: float) -> float:
    return (
        0.25 * pattern.confidence
        + 0.25 * min(1.0, len(signal_hits) / 2)
        + 0.20 * _evidence_strength(pattern)
        + 0.15 * trigger_cov
        + 0.15 * min(1.0, len(signal_hits) / 3)
    )
