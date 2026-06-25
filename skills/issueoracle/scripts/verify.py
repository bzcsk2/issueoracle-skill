from __future__ import annotations

import sys
from pathlib import Path


def verify():
    errors = []

    scripts_dir = Path(__file__).parent
    skill_dir = scripts_dir.parent

    # Check critical files exist. The main script keeps its legacy file name during the rename.
    critical = [
        skill_dir / "SKILL.md",
        scripts_dir / "issueoracle.py",
        scripts_dir / "build_skill.py",
        scripts_dir / "lib" / "version.py",
        scripts_dir / "lib" / "schema.py",
        scripts_dir / "lib" / "env.py",
        scripts_dir / "lib" / "pack_loader.py",
        scripts_dir / "lib" / "pattern_match.py",
        scripts_dir / "lib" / "review.py",
        scripts_dir / "lib" / "github_search.py",
        scripts_dir / "lib" / "issue_filter.py",
    ]
    for f in critical:
        if not f.exists():
            errors.append(f"Missing critical file: {f}")

    # Try importing key modules
    sys.path.insert(0, str(scripts_dir))
    try:
        from lib import schema

        # Test round-trip
        p = schema.Pattern(
            id="test-pattern",
            title="Test",
            language="Python",
            bug_type="test",
            root_cause="test",
            evidence=[schema.OssEvidence(repo="o/r", url="https://github.com/o/r/issues/1")],
            confidence=0.5,
        )
        d = p.model_dump()
        p2 = schema.Pattern(**d)
        assert p.id == p2.id
    except Exception as e:
        errors.append(f"Schema round-trip failed: {e}")

    # Check packs
    packs_dir = skill_dir / "packs"
    if packs_dir.exists():
        patterns_found = list(packs_dir.rglob("patterns.yaml"))
        if not patterns_found:
            errors.append("No pattern packs found")
    else:
        errors.append("packs/ directory missing")

    if errors:
        print("DETECTORACLE VERIFY FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    else:
        print("DETECTORACLE VERIFY PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(verify())
