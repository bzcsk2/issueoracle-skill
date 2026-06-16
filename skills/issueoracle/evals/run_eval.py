"""Eval runner for IssueOracle pattern fixtures."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from lib import code_index, pack_loader, pattern_match, profile, review


def run_eval(fixtures_dir: Path, golden_dir: Path, packs_dir: Path, emit: str = "text"):
    patterns, _ = pack_loader.load_pack_dir(packs_dir)
    results = []
    passed = 0
    failed = 0

    for fixture_dir in sorted(fixtures_dir.iterdir()):
        if not fixture_dir.is_dir():
            continue
        fixture_name = fixture_dir.name
        golden_path = golden_dir / f"{fixture_name}.expected.json"
        if not golden_path.exists():
            continue

        golden = json.loads(golden_path.read_text(encoding="utf-8"))

        for variant in ("bad", "good"):
            variant_dir = fixture_dir / variant
            if not variant_dir.exists():
                continue

            prof = profile.profile_repo(str(variant_dir))
            chunks = code_index.index_repo(str(variant_dir), prof)
            matches = pattern_match.match(chunks, patterns, prof)
            findings, _ = review.build_findings(matches, "low", 20)

            has_findings = len(findings) > 0
            variant_key = f"{variant}_expected_findings"
            expected = golden.get(variant_key, False)

            if has_findings == expected:
                passed += 1
            else:
                failed += 1
                results.append({
                    "fixture": fixture_name,
                    "variant": variant,
                    "expected": expected,
                    "actual": has_findings,
                    "findings": len(findings),
                })

    summary = {
        "total": passed + failed,
        "passed": passed,
        "failed": failed,
        "details": results,
    }

    if emit == "json":
        print(json.dumps(summary, indent=2))
    else:
        print(f"Eval Results: {passed}/{passed + failed} passed")
        if failed:
            print(f"  {failed} failure(s):")
            for r in results:
                print(f"    {r['fixture']}/{r['variant']}: expected={r['expected']}, actual={r['actual']}")

    return 0 if failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="Run IssueOracle eval suite")
    skill_dir = Path(__file__).resolve().parent.parent
    parser.add_argument("--fixtures", default=str(skill_dir / "evals" / "fixtures"))
    parser.add_argument("--golden", default=str(skill_dir / "evals" / "golden"))
    parser.add_argument("--packs", default=str(skill_dir / "packs"))
    parser.add_argument("--emit", default="text", choices=["text", "json"])
    args = parser.parse_args()
    return run_eval(
        Path(args.fixtures), Path(args.golden), Path(args.packs), emit=args.emit,
    )


if __name__ == "__main__":
    sys.exit(main())
