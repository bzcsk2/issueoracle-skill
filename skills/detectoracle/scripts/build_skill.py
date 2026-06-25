from __future__ import annotations

import zipfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_DIR.parents[1]
DIST_DIR = REPO_ROOT / "dist"
OUT_PATH = DIST_DIR / "detectoracle.skill"

EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    ".venv",
    "dist",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
REQUIRED_ENTRIES = {
    "SKILL.md",
    "scripts/detectoracle.py",
    "scripts/issueoracle.py",
    "scripts/lib/schema.py",
    "scripts/lib/version.py",
}


def should_include(path: Path) -> bool:
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return False
    if path.name in {".DS_Store"}:
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    return path.is_file()


def verify_bundle(path: Path) -> None:
    with zipfile.ZipFile(path, "r") as zf:
        names = set(zf.namelist())
    missing = sorted(REQUIRED_ENTRIES - names)
    if missing:
        raise RuntimeError(f"Bundle missing required entries: {', '.join(missing)}")
    if not any(name.startswith("packs/") for name in names):
        raise RuntimeError("Bundle missing packs/ content")
    if not any(name.startswith("references/") for name in names):
        raise RuntimeError("Bundle missing references/ content")


def build() -> Path:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    if OUT_PATH.exists():
        OUT_PATH.unlink()

    with zipfile.ZipFile(OUT_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(SKILL_DIR.rglob("*")):
            if should_include(path):
                zf.write(path, path.relative_to(SKILL_DIR).as_posix())

    verify_bundle(OUT_PATH)
    return OUT_PATH


def main() -> int:
    out = build()
    size_kib = out.stat().st_size / 1024
    print(f"Built: {out} ({size_kib:.1f} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
