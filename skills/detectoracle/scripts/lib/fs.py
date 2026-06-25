from __future__ import annotations

from pathlib import Path


def find_project_root(start: Path | None = None) -> Path:
    cwd = start or Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent
        if parent == parent.parent:
            break
    return cwd


def find_files(root: Path, suffixes: set[str], max_depth: int = 10) -> list[Path]:
    files: list[Path] = []
    for child in root.iterdir():
        if child.name.startswith(".") or child.name.startswith("_"):
            continue
        if child.is_file() and child.suffix in suffixes:
            files.append(child)
        elif child.is_dir() and max_depth > 0:
            files.extend(find_files(child, suffixes, max_depth - 1))
    return sorted(files)


def safe_read(path: Path, encoding: str = "utf-8") -> str:
    try:
        return path.read_text(encoding=encoding, errors="replace")
    except Exception:
        return ""
