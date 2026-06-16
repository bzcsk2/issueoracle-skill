from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

MIN_PYTHON = (3, 12)


def ensure_supported_python(version_info=None):
    vi = version_info or sys.version_info
    if vi < MIN_PYTHON:
        print(
            f"Error: Python {'.'.join(str(x) for x in MIN_PYTHON)}+ required, "
            f"got {'.'.join(str(x) for x in vi[:3])}",
            file=sys.stderr,
        )
        sys.exit(1)


ensure_supported_python()

if os.name == "nt":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

from lib import config as config_mod, env, log, render, schema
import store


def build_parser():
    parser = argparse.ArgumentParser(
        description="Mine bug patterns from GitHub issues and review local code with evidence."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_review = sub.add_parser("review", help="Review a local repo using loaded patterns")
    p_review.add_argument("repo_path")
    p_review.add_argument("--changed", action="store_true")
    p_review.add_argument("--base", default="main")
    p_review.add_argument("--languages")
    p_review.add_argument("--frameworks")
    p_review.add_argument("--packs", default=None)
    p_review.add_argument("--severity-threshold", default="medium", choices=["low", "medium", "high"])
    p_review.add_argument("--max-findings", type=int, default=20)
    p_review.add_argument("--emit", default="markdown", choices=["markdown", "json", "compact"])
    p_review.add_argument("--save-dir", default=None)
    p_review.add_argument("--debug", action="store_true")

    p_mine = sub.add_parser("mine", help="Mine bug patterns from a GitHub repo's closed issues")
    p_mine.add_argument("owner_repo", help="GitHub repo as owner/repo (e.g. fastapi/fastapi)")
    p_mine.add_argument("--label", default="bug")
    p_mine.add_argument("--state", default="closed")
    p_mine.add_argument("--max-issues", type=int, default=50)
    p_mine.add_argument("--human-review", action="store_true", default=True)
    p_mine.add_argument("--emit", default="markdown", choices=["markdown", "json"])
    p_mine.add_argument("--save-dir", default=None)
    p_mine.add_argument("--debug", action="store_true")

    p_validate = sub.add_parser("validate", help="Validate a pattern pack directory")
    p_validate.add_argument("pack_path")
    p_validate.add_argument("--emit", default="markdown", choices=["markdown", "json"])

    sub.add_parser("diagnose", help="Print environment and pack status")

    return parser


def diagnose() -> dict:
    import importlib.util

    packs_dir = SCRIPT_DIR.parent / "packs"
    packs_found = 0
    if packs_dir.exists():
        for p in packs_dir.rglob("patterns.yaml"):
            packs_found += 1

    github_token = env.get_config().get("GITHUB_TOKEN")
    info = {
        "python_version": sys.version,
        "platform": sys.platform,
        "script_dir": str(SCRIPT_DIR),
        "packs_dir": str(packs_dir),
        "packs_found": packs_found,
        "github_token_configured": bool(github_token),
        "github_api_limit": "5000/hr" if github_token else "60/hr (unauthenticated)",
        "dependencies": {},
    }
    for mod_name in ("pydantic", "yaml"):
        spec = importlib.util.find_spec(mod_name)
        info["dependencies"][mod_name] = spec is not None
    return info


def cmd_diagnose(args) -> int:
    data = diagnose()
    print(render.render_diagnose(data))
    return 0


def cmd_validate(args) -> int:
    from lib import pack_loader

    pack_path = Path(args.pack_path)
    if not pack_path.exists():
        print(f"Error: pack path does not exist: {pack_path}", file=sys.stderr)
        return 1
    patterns, errors = pack_loader.load_pack_dir(pack_path)
    result = {
        "pack_path": str(pack_path.resolve()),
        "patterns_valid": len(patterns),
        "patterns_invalid": len(errors),
        "errors": [{"file": str(e.get("file", "")), "pattern_id": str(e.get("id", "")), "errors": e.get("errors", [])} for e in errors],
    }
    output = render.render_validation(result, emit=args.emit)
    print(output)
    return 1 if errors else 0


def cmd_review(args) -> int:
    from lib import code_index, git, pack_loader, pattern_match, profile, review

    cfg = env.get_config()
    if args.debug:
        log.set_debug(True)
    logger = log.get_logger()

    repo_path = Path(args.repo_path).resolve()
    if not repo_path.exists():
        print(f"Error: repo path does not exist: {repo_path}", file=sys.stderr)
        return 1

    logger.info(f"Reviewing repo: {repo_path}")

    packs_dir = args.packs or str(SCRIPT_DIR.parent / "packs")
    patterns, errors = pack_loader.load_pack_dir(Path(packs_dir))
    if errors:
        for e in errors:
            logger.warning(f"Pack error: {e}")

    if not patterns:
        logger.warning("No patterns loaded")
        report = {
            "version": "0.1.0",
            "scope": {"repo": str(repo_path), "mode": "diff" if args.changed else "full", "patterns_loaded": 0, "files_scanned": 0},
            "summary": {"findings_total": 0, "suppressed": 0, "by_severity": {}, "patterns_loaded": 0, "files_scanned": 0},
            "findings": [],
            "suppressed": [],
        }
    else:
        logger.info(f"Loaded {len(patterns)} patterns")

        changed = None
        if args.changed:
            changed = git.get_changed_files(repo_path, base=args.base)

        prof = profile.profile_repo(str(repo_path), changed_files=changed)
        logger.info(f"Profile: {prof.languages} / {prof.frameworks}")

        chunks = code_index.index_repo(str(repo_path), prof, only_files=changed)
        logger.info(f"Indexed {len(chunks)} code chunks")

        matches = pattern_match.match(chunks, patterns, prof)
        logger.info(f"Found {len(matches)} matches")

        threshold = args.severity_threshold or cfg.get("SEVERITY_THRESHOLD", "medium")
        max_f = args.max_findings or cfg.get("MAX_FINDINGS", 20)
        findings_list, suppressed = review.build_findings(matches, str(threshold), int(max_f))

        report = {
            "version": "0.1.0",
            "scope": {"repo": str(repo_path), "mode": "diff" if args.changed else "full", "patterns_loaded": len(patterns), "files_scanned": len(chunks)},
            "summary": {
                "findings_total": len(findings_list),
                "suppressed": len(suppressed),
                "by_severity": _count_by_severity(findings_list),
                "patterns_loaded": len(patterns),
                "files_scanned": len(chunks),
            },
            "findings": [f.model_dump() for f in findings_list],
            "suppressed": [f.model_dump() for f in suppressed],
        }

    output = render.render_review(report) if args.emit == "markdown" else (
        render.render_review_json(report) if args.emit == "json" else render.render_review_compact(report)
    )
    print(output)

    save_dir = args.save_dir
    if save_dir:
        md = render.render_review(report)
        js = render.render_review_json(report)
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        repo_slug = repo_path.name
        (save_path / f"{repo_slug}-review.md").write_text(md, encoding="utf-8")
        (save_path / f"{repo_slug}-review.json").write_text(js, encoding="utf-8")
        logger.info(f"Report saved to {save_path}")

    return 0


def _count_by_severity(findings):
    counts = {}
    for f in findings:
        s = f.severity
        counts[s] = counts.get(s, 0) + 1
    return counts


def cmd_mine(args) -> int:
    from lib import evidence_linker, github_search, issue_filter, pattern_extract, safety

    cfg = env.get_config()
    if args.debug:
        log.set_debug(True)
    logger = log.get_logger()

    token = cfg.get("GITHUB_TOKEN") or None
    repo = args.owner_repo

    logger.info(f"Mining closed bug issues from {repo}...")

    issues = github_search.search_closed_issues(
        repo, label=args.label, max_results=args.max_issues, token=token
    )
    logger.info(f"Found {len(issues)} closed issues with label '{args.label}'")

    bug_issues = issue_filter.filter_issues(issues)
    logger.info(f"After filter: {len(bug_issues)} likely-bug issues")

    candidates = []
    issues_with_pr = 0
    language_hint = ""

    for issue in bug_issues:
        prs = evidence_linker.link_issue_to_prs(issue, repo, token)
        if prs:
            issues_with_pr += 1
        cand = pattern_extract.extract_candidate(issue, prs, repo, language_hint)
        if cand:
            candidates.append(cand)

    result_dict = {
        "repo": repo,
        "mined_at": __import__("datetime").datetime.now().isoformat(),
        "issues_searched": len(issues),
        "issues_kept": len(bug_issues),
        "issues_with_pr": issues_with_pr,
        "candidates": [c.model_dump() for c in candidates],
        "raw_dir": "",
        "review_path": "",
    }

    mining_dir = store.save_mining(
        json.dumps(result_dict, indent=2, default=str), repo.replace("/", "_")
    )

    for cand in candidates:
        cand_path = mining_dir / "candidates" / f"{cand.id}.yaml"
        try:
            import yaml
            cand_path.write_text(yaml.dump(cand.model_dump(), default_flow_style=False), encoding="utf-8")
        except Exception:
            cand_path.write_text(json.dumps(cand.model_dump(), indent=2, default=str), encoding="utf-8")

    review_md = render.render_mining(result_dict, emit="markdown")
    review_path = mining_dir / "review.md"
    review_path.write_text(review_md, encoding="utf-8")

    result_dict["raw_dir"] = str(mining_dir / "raw")
    result_dict["review_path"] = str(review_path)

    store.write_last_run({"command": "mine", "repo": repo, "candidates": len(candidates), "mining_dir": str(mining_dir)})

    logger.info(f"Mining complete: {len(candidates)} candidates written to {mining_dir}")
    logger.info(f"Review them at: {review_path}")
    logger.info("Approved candidates can be moved to packs/ after human review.")

    output = render.render_mining(result_dict, emit=args.emit)
    print(output)
    return 0


def main():
    args = build_parser().parse_args()
    if getattr(args, "debug", False):
        os.environ["ISSUEORACLE_DEBUG"] = "1"
    try:
        if args.command == "diagnose":
            return cmd_diagnose(args)
        elif args.command == "validate":
            return cmd_validate(args)
        elif args.command == "review":
            return cmd_review(args)
        elif args.command == "mine":
            return cmd_mine(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if os.environ.get("ISSUEORACLE_DEBUG"):
            import traceback
            traceback.print_exc(file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
