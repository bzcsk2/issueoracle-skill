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
    suppressed: bool = False


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
            signal_hits, suppress, score_bonus = _match_signals(pattern.bad_code_signals, chunk)
            if not signal_hits:
                continue
            trigger_cov = _trigger_coverage(pattern.trigger_conditions, chunk)
            if trigger_cov == 0.0:
                continue
            score = _score(pattern, signal_hits, trigger_cov) + score_bonus
            results.append(
                MatchResult(
                    pattern=pattern,
                    chunk=chunk,
                    signal_hits=signal_hits,
                    suppressed=suppress,
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


def _match_signals(
    bad_signals: list[schema.TypedSignal | str], chunk: schema.CodeChunk
) -> tuple[list[str], bool, float]:
    chunk_text = chunk.code_excerpt.lower()
    chunk_signals = [s.lower() for s in chunk.signals]

    typed_signals = [s for s in bad_signals if isinstance(s, schema.TypedSignal)]
    legacy_signals = [s for s in bad_signals if isinstance(s, str)]

    if not typed_signals:
        hits = [s for s in legacy_signals if _contains(s, chunk_text, chunk_signals)]
        return hits, False, 0.0

    hits: list[str] = []
    suppressed = False
    score_bonus = 0.0

    for signal in typed_signals:
        values = _signal_values(signal)
        matched = [value for value in values if _contains(value, chunk_text, chunk_signals)]

        if signal.kind == "required" or signal.kind == "required_any":
            if not matched:
                return [], suppressed, score_bonus
            hits.extend(matched)
        elif signal.kind == "negative":
            if matched:
                score_bonus -= 0.15
        elif signal.kind == "suppress_if_present":
            if matched:
                suppressed = True
        elif signal.kind == "optional":
            if matched:
                score_bonus += 0.1
                hits.extend(matched)

    # Keep legacy string signals as optional compatibility hints once typed gates pass.
    for signal in legacy_signals:
        if _contains(signal, chunk_text, chunk_signals):
            hits.append(signal)

    return list(dict.fromkeys(hits)), suppressed, score_bonus


def _signal_values(signal: schema.TypedSignal) -> list[str]:
    values = list(signal.values or [])
    if signal.value:
        values.append(signal.value)
    return [v for v in values if v]


def _contains(value: str, chunk_text: str, chunk_signals: list[str]) -> bool:
    value_lower = value.lower()
    return value_lower in chunk_text or value_lower in chunk_signals


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
