"""Eval runner for IssueOracle pattern fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from lib import code_index, pack_loader, pattern_match, profile, review  # noqa: E402


def run_eval(fixtures_dir: Path, golden_dir: Path, packs_dir: Path, emit: str = "text"):
    from lib import experience as experience_mod

    patterns, _ = pack_loader.load_pack_dir(packs_dir)
    results = []
    passed = 0
    failed = 0
    total_fixtures = 0
    total_bad = 0
    total_good = 0
    pattern_recall_hits = 0
    pattern_recall_total = 0
    wrong_pattern_hit_count = 0
    false_positive_count = 0

    for fixture_dir in sorted(fixtures_dir.iterdir()):
        if not fixture_dir.is_dir():
            continue
        fixture_name = fixture_dir.name
        golden_path = golden_dir / f"{fixture_name}.expected.json"
        if not golden_path.exists():
            continue

        golden = json.loads(golden_path.read_text(encoding="utf-8"))

        eval_patterns = list(patterns)
        exp_file = fixture_dir / "experience.json"
        if exp_file.exists():
            exp_pats, _ = experience_mod.load_as_patterns(str(exp_file), include_candidates=True)
            eval_patterns += exp_pats

        for variant in ("bad", "good"):
            variant_dir = fixture_dir / variant
            if not variant_dir.exists():
                continue

            total_fixtures += 1
            if variant == "bad":
                total_bad += 1
            else:
                total_good += 1

            prof = profile.profile_repo(str(variant_dir))
            chunks = code_index.index_repo(str(variant_dir), prof)
            matches = pattern_match.match(chunks, eval_patterns, prof)
            findings, _ = review.build_findings(matches, "low", 20)

            expected = golden.get(variant, {})
            exp_findings = expected.get("expected_findings", False)
            must_include = expected.get("must_include_patterns", [])
            must_not_include = expected.get("must_not_include_patterns", [])
            must_include_files = expected.get("must_include_files", [])
            min_confidence = expected.get("min_confidence", 0.0)

            has_findings = len(findings) > 0
            found_patterns = {f.matched_pattern for f in findings}
            found_files = {f.file for f in findings}
            max_conf = max((f.confidence for f in findings), default=0.0)

            variant_ok = True
            detail_errors = []

            if has_findings != exp_findings:
                variant_ok = False
                detail_errors.append(
                    f"expected_findings={exp_findings}, "
                    f"got={has_findings} ({len(findings)} findings)"
                )

            for pid in must_include:
                pattern_recall_total += 1
                if pid in found_patterns:
                    pattern_recall_hits += 1
                else:
                    variant_ok = False
                    detail_errors.append(f"must_include_pattern '{pid}' not found")

            for pid in must_not_include:
                if pid in found_patterns:
                    variant_ok = False
                    wrong_pattern_hit_count += 1
                    detail_errors.append(f"must_not_include_pattern '{pid}' found (false positive)")

            if has_findings:
                for f in findings:
                    if not f.file or not f.start_line:
                        variant_ok = False
                        detail_errors.append(
                            f"finding missing file/line: pattern={f.matched_pattern}"
                        )
                    if not f.matched_pattern:
                        variant_ok = False
                        detail_errors.append("finding missing matched_pattern")

            for fn in must_include_files:
                if not any(fn in fp for fp in found_files):
                    variant_ok = False
                    detail_errors.append(f"must_include_file '{fn}' not found in findings")

            if max_conf < min_confidence:
                variant_ok = False
                detail_errors.append(
                    f"max_confidence={max_conf:.2f} < min_confidence={min_confidence}"
                )

            if has_findings and not exp_findings:
                false_positive_count += 1

            if variant_ok:
                passed += 1
            else:
                failed += 1
                results.append(
                    {
                        "fixture": fixture_name,
                        "variant": variant,
                        "errors": detail_errors,
                        "findings": len(findings),
                        "patterns": list(found_patterns),
                    }
                )

    summary = {
        "total": passed + failed,
        "passed": passed,
        "failed": failed,
        "fixtures_total": total_fixtures,
        "positive_total": total_bad,
        "negative_total": total_good,
        "pattern_recall": f"{pattern_recall_hits}/{pattern_recall_total}",
        "wrong_pattern_hit_count": wrong_pattern_hit_count,
        "false_positive_count": false_positive_count,
        "details": results,
    }

    if emit == "json":
        print(json.dumps(summary, indent=2))
    else:
        print(f"Eval Results: {passed}/{passed + failed} passed")
        print(
            f"  pattern_recall: {pattern_recall_hits}/{pattern_recall_total}"
            f"  wrong_pattern_hits: {wrong_pattern_hit_count}"
            f"  false_positives: {false_positive_count}"
        )
        if failed:
            print(f"  {failed} failure(s):")
            for r in results:
                print(f"    {r['fixture']}/{r['variant']}:")
                for e in r["errors"]:
                    print(f"      - {e}")

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
        Path(args.fixtures),
        Path(args.golden),
        Path(args.packs),
        emit=args.emit,
    )


if __name__ == "__main__":
    sys.exit(main())
