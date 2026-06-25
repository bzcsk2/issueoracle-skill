from __future__ import annotations

import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REQUIRED_BUNDLE_ENTRIES = {
    "SKILL.md",
    "scripts/detectoracle.py",
    "scripts/issueoracle.py",
    "scripts/lib/version.py",
    "scripts/lib/schema.py",
    "scripts/lib/env.py",
    "scripts/lib/pack_loader.py",
    "scripts/lib/pattern_match.py",
    "scripts/lib/review.py",
    "scripts/lib/github_search.py",
    "scripts/lib/issue_filter.py",
}


def _run(cmd: list[str], *, cwd: Path):
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _summarize_failure(result) -> str:
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    detail = stderr or stdout or "no output"
    return f"exit={result.returncode}: {detail}"


def _verify_bundle_archive(bundle_path: Path) -> list[str]:
    errors: list[str] = []

    if not bundle_path.exists():
        return [f"Bundle not found: {bundle_path}"]

    try:
        with zipfile.ZipFile(bundle_path, "r") as zf:
            names = set(zf.namelist())
        missing = sorted(REQUIRED_BUNDLE_ENTRIES - names)
        if missing:
            errors.append(f"Bundle missing required entries: {', '.join(missing)}")
        if not any(name.startswith("packs/") for name in names):
            errors.append("Bundle missing packs/ content")
        if not any(name.startswith("references/") for name in names):
            errors.append("Bundle missing references/ content")

        if errors:
            return errors

        with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(bundle_path, "r") as zf:
            extract_dir = Path(tmp) / "skill"
            zf.extractall(extract_dir)
            script = extract_dir / "scripts" / "detectoracle.py"
            packs_dir = extract_dir / "packs"

            diagnose = _run([sys.executable, str(script), "diagnose"], cwd=extract_dir)
            if diagnose.returncode != 0:
                errors.append(f"Bundle diagnose failed: {_summarize_failure(diagnose)}")

            validate = _run(
                [sys.executable, str(script), "validate", str(packs_dir)],
                cwd=extract_dir,
            )
            if validate.returncode != 0:
                errors.append(f"Bundle validate failed: {_summarize_failure(validate)}")
    except zipfile.BadZipFile as e:
        errors.append(f"Bundle is not a valid zip archive: {e}")
    except Exception as e:
        errors.append(f"Bundle smoke test failed: {e}")

    return errors


def verify() -> int:
    errors = []

    scripts_dir = Path(__file__).parent
    skill_dir = scripts_dir.parent
    repo_root = skill_dir.parents[1]
    bundle_path = repo_root / "dist" / "detectoracle.skill"

    critical = [
        skill_dir / "SKILL.md",
        scripts_dir / "detectoracle.py",
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

    sys.path.insert(0, str(scripts_dir))
    try:
        from lib import schema

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
        if p.id != p2.id:
            errors.append("Schema round-trip changed pattern id")
    except Exception as e:
        errors.append(f"Schema round-trip failed: {e}")

    packs_dir = skill_dir / "packs"
    if not packs_dir.exists():
        errors.append("packs/ directory missing")
    elif not list(packs_dir.rglob("patterns.yaml")):
        errors.append("No pattern packs found")

    errors.extend(_verify_bundle_archive(bundle_path))

    if errors:
        print("DETECTORACLE VERIFY FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("DETECTORACLE VERIFY PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(verify())
