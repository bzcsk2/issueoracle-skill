from __future__ import annotations

import datetime
import json
from pathlib import Path

from lib import env


def ensure_home() -> Path:
    home = env.get_issueoracle_home()
    (home / "reports").mkdir(parents=True, exist_ok=True)
    (home / "cache" / "github").mkdir(parents=True, exist_ok=True)
    (home / "cache" / "repo-profile").mkdir(parents=True, exist_ok=True)
    (home / "mining").mkdir(parents=True, exist_ok=True)
    (home / "bugplay").mkdir(parents=True, exist_ok=True)
    return home


def save_experience(md: str, json_data: str) -> Path:
    home = ensure_home()
    bugplay = home / "bugplay"
    candidates_dir = bugplay / "candidates"
    candidates_dir.mkdir(parents=True, exist_ok=True)
    (candidates_dir / "bug-experience.md").write_text(md, encoding="utf-8")
    (candidates_dir / "experience.json").write_text(json_data, encoding="utf-8")
    return candidates_dir


def save_report(report_md: str, report_json: str, repo_slug: str) -> tuple[Path, Path]:
    home = ensure_home()
    ts = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    md_path = home / "reports" / f"{ts}-{repo_slug}-review.md"
    json_path = home / "reports" / f"{ts}-{repo_slug}-review.json"
    md_path.write_text(report_md, encoding="utf-8")
    json_path.write_text(report_json, encoding="utf-8")
    return md_path, json_path


def save_mining(result_json: str, repo_slug: str) -> Path:
    home = ensure_home()
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    mining_dir = home / "mining" / f"{repo_slug}_{date}"
    mining_dir.mkdir(parents=True, exist_ok=True)
    (mining_dir / "raw").mkdir(exist_ok=True)
    (mining_dir / "candidates").mkdir(exist_ok=True)
    out = mining_dir / "result.json"
    out.write_text(result_json, encoding="utf-8")
    return mining_dir


def write_last_run(payload: dict) -> None:
    home = ensure_home()
    (home / "last-run.json").write_text(
        json.dumps(payload, indent=2, default=str), encoding="utf-8"
    )
