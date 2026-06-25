from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any


NEW_CONFIG_DIR = Path.home() / ".detectoracle"
LEGACY_CONFIG_DIR = Path.home() / ".issueoracle"
NEW_NUX_ENV_DIR = Path.home() / ".config" / "detectoracle"
LEGACY_NUX_ENV_DIR = Path.home() / ".config" / "issueoracle"
NUX_ENV_DIR = NEW_NUX_ENV_DIR
NUX_ENV_PATH = NUX_ENV_DIR / ".env"
LEGACY_NUX_ENV_PATH = LEGACY_NUX_ENV_DIR / ".env"


def _first_non_empty_env(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
        if value == "":
            return ""
    return None


def _resolve_config_dir() -> Path | None:
    override = _first_non_empty_env("DETECTORACLE_CONFIG_DIR", "ISSUEORACLE_CONFIG_DIR")
    if override == "":
        return None
    if override:
        return Path(override)
    if LEGACY_CONFIG_DIR.exists() and not NEW_CONFIG_DIR.exists():
        return LEGACY_CONFIG_DIR
    return NEW_CONFIG_DIR


CONFIG_DIR = _resolve_config_dir()


def _read_text_if_exists(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def is_first_run() -> bool:
    marker = "SETUP_COMPLETE=true"
    return marker not in _read_text_if_exists(NUX_ENV_PATH) and marker not in _read_text_if_exists(
        LEGACY_NUX_ENV_PATH
    )


def mark_setup_complete() -> None:
    NUX_ENV_DIR.mkdir(parents=True, exist_ok=True)
    content = (
        "SETUP_COMPLETE=true\n"
        "DETECTORACLE_HOME=~/.detectoracle\n"
        "DETECTORACLE_ALLOW_REMOTE_LLM=0\n"
    )
    NUX_ENV_PATH.write_text(content, encoding="utf-8")


def get_detectoracle_home() -> Path:
    override = _first_non_empty_env("DETECTORACLE_HOME", "ISSUEORACLE_HOME")
    if override:
        return Path(override).expanduser()
    if (Path.home() / ".issueoracle").exists() and not (Path.home() / ".detectoracle").exists():
        return Path.home() / ".issueoracle"
    return Path.home() / ".detectoracle"


def get_issueoracle_home() -> Path:
    """Backward-compatible alias retained during the DetectorOracle rename."""
    return get_detectoracle_home()


def load_toml(path: Path) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def _find_project_config(cwd: Path) -> dict[str, Any]:
    for parent in [cwd, *cwd.parents]:
        for dirname in (".detectoracle", ".issueoracle"):
            cand = parent / dirname / "config.toml"
            if cand.exists():
                return load_toml(cand)
        if parent == Path.home() or parent == parent.parent:
            break
    return {}


def get_config() -> dict[str, Any]:
    global_cfg = load_toml(CONFIG_DIR / "config.toml") if CONFIG_DIR else {}
    project_cfg = _find_project_config(Path.cwd())
    merged = {**global_cfg, **project_cfg}
    allow_remote_llm = (
        os.environ.get("DETECTORACLE_ALLOW_REMOTE_LLM")
        or os.environ.get("ISSUEORACLE_ALLOW_REMOTE_LLM")
        or str(merged.get("allow_remote_llm", False))
    )
    severity_threshold = (
        os.environ.get("DETECTORACLE_SEVERITY_THRESHOLD")
        or os.environ.get("ISSUEORACLE_SEVERITY_THRESHOLD")
        or merged.get("severity_threshold", "medium")
    )
    max_findings = int(
        os.environ.get("DETECTORACLE_MAX_FINDINGS")
        or os.environ.get("ISSUEORACLE_MAX_FINDINGS")
        or merged.get("max_findings", 20)
    )
    config = {
        "GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN") or merged.get("github_token"),
        "DETECTORACLE_ALLOW_REMOTE_LLM": allow_remote_llm,
        "ISSUEORACLE_ALLOW_REMOTE_LLM": allow_remote_llm,
        "SEVERITY_THRESHOLD": severity_threshold,
        "MAX_FINDINGS": max_findings,
    }
    return config
