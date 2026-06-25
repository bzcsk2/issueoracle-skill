from __future__ import annotations

import subprocess
from pathlib import Path


def get_changed_files(repo_path: str | Path, base: str = "main") -> list[str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", base, "--relative"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(repo_path),
        )
        if result.returncode != 0:
            return []
        files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
        return files
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def get_diff(repo_path: str | Path, base: str = "main") -> str:
    try:
        result = subprocess.run(
            ["git", "diff", base, "--relative"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(repo_path),
        )
        if result.returncode != 0:
            return ""
        return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def get_staged_diff(repo_path: str | Path) -> str:
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--relative"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(repo_path),
        )
        if result.returncode != 0:
            return ""
        return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def check_git_available() -> bool:
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def is_git_repo(path: str | Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(path),
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
