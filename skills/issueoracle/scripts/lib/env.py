from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

_config_override = os.environ.get("ISSUEORACLE_CONFIG_DIR")
if _config_override == "":
    CONFIG_DIR: Path | None = None
elif _config_override:
    CONFIG_DIR = Path(_config_override)
else:
    CONFIG_DIR = Path.home() / ".issueoracle"

def get_issueoracle_home() -> Path:
    override = os.environ.get("ISSUEORACLE_HOME")
    return Path(override) if override else (Path.home() / ".issueoracle")


def load_toml(path: Path) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def get_config() -> dict[str, Any]:
    global_cfg = load_toml(CONFIG_DIR / "config.toml") if CONFIG_DIR else {}
    project_cfg: dict[str, Any] = {}
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        cand = parent / ".issueoracle" / "config.toml"
        if cand.exists():
            project_cfg = load_toml(cand)
            break
        if parent == Path.home() or parent == parent.parent:
            break
    merged = {**global_cfg, **project_cfg}
    config = {
        "GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN") or merged.get("github_token"),
        "ISSUEORACLE_ALLOW_REMOTE_LLM": (
            os.environ.get("ISSUEORACLE_ALLOW_REMOTE_LLM")
            or str(merged.get("allow_remote_llm", False))
        ),
        "SEVERITY_THRESHOLD": (
            os.environ.get("ISSUEORACLE_SEVERITY_THRESHOLD")
            or merged.get("severity_threshold", "medium")
        ),
        "MAX_FINDINGS": int(
            os.environ.get("ISSUEORACLE_MAX_FINDINGS")
            or merged.get("max_findings", 20)
        ),
    }
    return config
