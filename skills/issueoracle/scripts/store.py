from __future__ import annotations

import datetime
import json
from pathlib import Path

from lib import env


def ensure_home() -> Path:
    home = env.get_detectoracle_home()
    (home / "reports").mkdir(parents=True, exist_ok=True)
    (home / "cache" / "github").mkdir(parents=True, exist_ok=True)
    (home / "cache" / "repo-profile").mkdir(parents=True, exist_ok=True)
    (home / "mining").mkdir(parents=True, exist_ok=True)
    (home / "bugplay").mkdir(parents=True, exist_ok=True)
    (home / "runs").mkdir(parents=True, exist_ok=True)
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


def create_run(repos: list[str]) -> Path:
    home = ensure_home()
    run_id = f"mine-{datetime.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}"
    run_dir = home / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    progress = {
        "run_id": run_id,
        "repos": repos,
        "completed_repos": [],
        "completed_issues": [],
        "failed_issues": [],
        "status": "running",
    }
    (run_dir / "progress.json").write_text(json.dumps(progress, indent=2), encoding="utf-8")
    return run_dir


def load_run(run_dir: Path) -> dict:
    return json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))


def save_run(run_dir: Path, progress: dict) -> None:
    (run_dir / "progress.json").write_text(json.dumps(progress, indent=2), encoding="utf-8")


def append_run_line(run_dir: Path, name: str, line: str) -> None:
    with open(run_dir / name, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def find_last_run_dir() -> Path | None:
    home = ensure_home()
    runs_dir = home / "runs"
    if not runs_dir.exists():
        return None
    dirs = sorted(runs_dir.iterdir(), reverse=True)
    for d in dirs:
        if d.is_dir() and (d / "progress.json").exists():
            return d
    return None
