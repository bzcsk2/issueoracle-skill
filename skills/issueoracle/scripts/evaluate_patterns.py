"""Evaluate pattern quality against fixtures."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib import pack_loader


def evaluate_patterns(packs_dir: Path, emit: str = "text"):
    patterns, errors = pack_loader.load_pack_dir(packs_dir)
    total = len(patterns)
    with_evidence = sum(1 for p in patterns if p.evidence)
    with_triggers = sum(1 for p in patterns if p.trigger_conditions)
    with_signals = sum(1 for p in patterns if p.bad_code_signals)
    with_fixes = sum(1 for p in patterns if p.fix_patterns)
    with_boundary = sum(1 for p in patterns if p.false_positive_boundary)
    avg_confidence = sum(p.confidence for p in patterns) / total if total else 0

    result = {
        "total_patterns": total,
        "invalid": len(errors),
        "with_evidence": with_evidence,
        "with_triggers": with_triggers,
        "with_signals": with_signals,
        "with_fixes": with_fixes,
        "with_boundary": with_boundary,
        "avg_confidence": round(avg_confidence, 2),
    }

    if emit == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"Patterns: {total}")
        print(f"  Invalid: {len(errors)}")
        print(f"  With OSS evidence: {with_evidence}")
        print(f"  With trigger conditions: {with_triggers}")
        print(f"  With bad code signals: {with_signals}")
        print(f"  With fix patterns: {with_fixes}")
        print(f"  With false-positive boundary: {with_boundary}")
        print(f"  Avg confidence: {avg_confidence}")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Evaluate IssueOracle pattern quality")
    skill_dir = Path(__file__).resolve().parent.parent
    parser.add_argument("--packs", default=str(skill_dir / "packs"))
    parser.add_argument("--emit", default="text", choices=["text", "json"])
    args = parser.parse_args()
    return evaluate_patterns(Path(args.packs), emit=args.emit)


if __name__ == "__main__":
    sys.exit(main())
