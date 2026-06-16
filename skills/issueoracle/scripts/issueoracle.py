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

import store  # noqa: E402
from lib import env, log, render, schema  # noqa: E402
from lib import experience as experience_mod  # noqa: E402
from lib.version import __version__  # noqa: E402


def build_parser():
    parser = argparse.ArgumentParser(
        description="Scan, mine, and review code using OSS bug patterns."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="Profile a local repo and find similar OSS projects")
    p_scan.add_argument("repo_path")
    p_scan.add_argument("--emit", default="markdown", choices=["markdown", "json"])
    p_scan.add_argument("--max-repos", type=int, default=5)
    p_scan.add_argument("--save-dir", default=None)
    p_scan.add_argument("--debug", action="store_true")

    p_review = sub.add_parser("review", help="Review a local repo using loaded patterns")
    p_review.add_argument("repo_path")
    p_review.add_argument("--experience", default=None, help="Path to bug experience JSON/MD")
    p_review.add_argument("--changed", action="store_true")
    p_review.add_argument("--base", default="main")
    p_review.add_argument("--languages")
    p_review.add_argument("--frameworks")
    p_review.add_argument("--packs", default=None)
    p_review.add_argument(
        "--severity-threshold", default="medium", choices=["low", "medium", "high"]
    )
    p_review.add_argument("--max-findings", type=int, default=20)
    p_review.add_argument("--emit", default="markdown", choices=["markdown", "json", "compact"])
    p_review.add_argument("--save-dir", default=None)
    p_review.add_argument("--include-candidates", action="store_true", help="Include candidate-status experience patterns")
    p_review.add_argument("--trust-candidates", action="store_true", help="Allow candidate findings at any severity")
    p_review.add_argument("--debug", action="store_true")

    p_mine = sub.add_parser("mine", help="Mine bug patterns from GitHub repos (comma-separated)")
    p_mine.add_argument(
        "owner_repo",
        help="GitHub repo(s) as owner/repo (comma-separated)",
    )
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

    p_experience = sub.add_parser("experience", help="Manage bug experiences")
    p_exp_sub = p_experience.add_subparsers(dest="experience_command", required=True)
    p_exp_list = p_exp_sub.add_parser("list", help="List experiences by status")
    p_exp_list.add_argument("--status", default="candidate", choices=["candidate", "reviewed", "approved", "rejected", "all"])
    p_exp_list.add_argument("--emit", default="text", choices=["text", "json"])

    p_exp_show = p_exp_sub.add_parser("show", help="Show a single experience")
    p_exp_show.add_argument("id")

    p_exp_approve = p_exp_sub.add_parser("approve", help="Approve a candidate experience")
    p_exp_approve.add_argument("id")
    p_exp_approve.add_argument("--review-notes", default="Approved via CLI")

    p_exp_reject = p_exp_sub.add_parser("reject", help="Reject a candidate experience")
    p_exp_reject.add_argument("id")
    p_exp_reject.add_argument("--review-notes", default="Rejected via CLI")

    p_exp_export = p_exp_sub.add_parser("export-approved", help="Export approved experiences as review-ready patterns")
    p_exp_export.add_argument("--emit", default="text", choices=["text", "json"])

    sub.add_parser("diagnose", help="Print environment and pack status")

    sub.add_parser("doctor", help="User-facing health check")

    return parser


def diagnose() -> dict:
    import importlib.util

    packs_dir = SCRIPT_DIR.parent / "packs"
    packs_found = 0
    if packs_dir.exists():
        for _p in packs_dir.rglob("patterns.yaml"):
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


def cmd_doctor() -> int:
    from lib import pack_loader
    from lib.version import __version__

    checks = []
    ok = True

    python_ver = sys.version_info
    if python_ver >= (3, 12):
        checks.append({"ok": True, "message": f"Python {python_ver.major}.{python_ver.minor}.{python_ver.micro}"})
    else:
        checks.append({"ok": False, "message": f"Python {python_ver.major}.{python_ver.minor} < 3.12"})
        ok = False

    skill_dir = SCRIPT_DIR.parent
    if skill_dir.exists():
        checks.append({"ok": True, "message": f"Skill dir: {skill_dir}"})
    else:
        checks.append({"ok": False, "message": "Skill dir not found"})
        ok = False

    packs_dir = skill_dir / "packs"
    patterns, errors = pack_loader.load_pack_dir(packs_dir)
    if errors:
        checks.append({"ok": False, "message": f"Packs: {len(patterns)} patterns, {len(errors)} errors"})
        ok = False
    else:
        checks.append({"ok": True, "message": f"Packs: {len(patterns)} patterns"})

    fixtures_dir = skill_dir / "evals" / "fixtures"
    fixture_count = len([d for d in fixtures_dir.iterdir() if d.is_dir()]) if fixtures_dir.exists() else 0
    checks.append({"ok": True, "message": f"Eval fixtures: {fixture_count}"})

    git_available = False
    try:
        import subprocess
        subprocess.run(["git", "--version"], capture_output=True, timeout=5)
        git_available = True
    except Exception:
        pass
    checks.append({"ok": git_available, "message": "Git: available" if git_available else "Git: not found"})

    github_token = env.get_config().get("GITHUB_TOKEN")
    if github_token:
        checks.append({"ok": True, "message": "GitHub token: configured"})
    else:
        checks.append({"ok": True, "message": "GitHub token: missing, public rate limit only (60 req/hr)"})

    home = env.get_issueoracle_home()
    checks.append({"ok": True, "message": f"ISSUEORACLE_HOME: {home}"})

    data = {
        "version": __version__,
        "checks": checks,
        "suggested": "/issueoracle scan .",
    }
    print(render.render_doctor(data))
    return 0 if ok else 1


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
        "errors": [
            {
                "file": str(e.get("file", "")),
                "pattern_id": str(e.get("id", "")),
                "errors": e.get("errors", []),
            }
            for e in errors
        ],
    }
    output = render.render_validation(result, emit=args.emit)
    print(output)
    return 1 if errors else 0


def cmd_scan(args) -> int:
    from lib import github_search, profile

    logger = log.get_logger()
    repo_path = Path(args.repo_path).resolve()
    if not repo_path.exists():
        print(f"Error: repo path does not exist: {repo_path}", file=sys.stderr)
        return 1
    logger.info(f"Scanning repo: {repo_path}")
    prof = profile.profile_repo(str(repo_path))
    project_type = profile.classify_project_type(prof)
    topics = profile.infer_search_topics(prof)
    primary_lang = prof.languages[0] if prof.languages else ""
    cfg = env.get_config()
    token = cfg.get("GITHUB_TOKEN") or None
    candidates = github_search.search_similar_repos(
        primary_lang,
        topics,
        token=token,
        max_results=args.max_repos,
    )
    profile_dict = {
        "languages": prof.languages,
        "frameworks": prof.frameworks,
        "dependencies": prof.dependencies,
        "risk_surfaces": prof.risk_surfaces,
        "project_type": project_type,
        "search_topics": topics,
    }
    result = {"profile": profile_dict, "candidates": [c.model_dump() for c in candidates]}
    output = render.render_scan(profile_dict, [c.model_dump() for c in candidates], emit=args.emit)
    print(output)
    if args.save_dir:
        save_path = Path(args.save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        (save_path / "scan.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0


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
            logger.error(f"Pack error: {e}")
        return 1

    if args.experience:
        exp_path = Path(args.experience).resolve()
        if exp_path.exists():
            include_candidates = getattr(args, "include_candidates", False)
            exp_patterns, exp_warnings = experience_mod.load_as_patterns(str(exp_path), include_candidates=include_candidates)
            for w in exp_warnings:
                logger.warning(f"Experience: {w}")
            logger.info(f"Loaded {len(exp_patterns)} patterns from experience: {exp_path}")
            patterns.extend(exp_patterns)
            if not exp_patterns and exp_warnings:
                logger.error(f"--experience provided but no usable patterns loaded: {exp_path}")
                return 1
        else:
            logger.error(f"Experience path not found: {exp_path}")
            return 1

    if not patterns:
        logger.warning("No patterns loaded")
        report = {
            "version": __version__,
            "scope": {
                "repo": str(repo_path),
                "mode": "diff" if args.changed else "full",
                "patterns_loaded": 0,
                "files_scanned": 0,
            },
            "summary": {
                "findings_total": 0,
                "suppressed": 0,
                "by_severity": {},
                "patterns_loaded": 0,
                "files_scanned": 0,
            },
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

        if args.experience and not getattr(args, "trust_candidates", False):
            for f in findings_list:
                if f.matched_pattern.startswith("exp-"):
                    if f.severity.value not in ("low", "medium"):
                        f.severity = "medium"

        report = {
            "version": __version__,
            "scope": {
                "repo": str(repo_path),
                "mode": "diff" if args.changed else "full",
                "patterns_loaded": len(patterns),
                "files_scanned": len(chunks),
            },
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

    output = (
        render.render_review(report)
        if args.emit == "markdown"
        else (
            render.render_review_json(report)
            if args.emit == "json"
            else render.render_review_compact(report)
        )
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


def cmd_experience(args) -> int:
    from lib import store
    home = store.ensure_home()
    exp_path = home / "bugplay" / "experience.json"

    if not exp_path.exists():
        print("No experience data found. Run `issueoracle mine` first.", file=sys.stderr)
        return 1

    report_data = json.loads(exp_path.read_text(encoding="utf-8"))
    experiences = report_data.get("experiences", [])

    cmd = args.experience_command

    if cmd == "list":
        status_filter = args.status
        filtered = (
            experiences
            if status_filter == "all"
            else [e for e in experiences if e.get("status", "candidate") == status_filter]
        )
        if args.emit == "json":
            print(json.dumps(filtered, indent=2, default=str))
        else:
            print(f"Experiences ({status_filter}): {len(filtered)}")
            for e in filtered:
                status_mark = {"candidate": "?", "approved": "+", "rejected": "-", "reviewed": "~"}
                mark = status_mark.get(e.get("status", "candidate"), "?")
                print(f"  {mark} {e['id']}: {e['title'][:60]}")
        return 0

    if cmd == "show":
        exp_id = args.id
        for e in experiences:
            if e.get("id") == exp_id:
                print(json.dumps(e, indent=2, default=str))
                return 0
        print(f"Experience not found: {exp_id}", file=sys.stderr)
        return 1

    if cmd in ("approve", "reject"):
        import datetime
        exp_id = args.id
        new_status = "approved" if cmd == "approve" else "rejected"
        found = False
        for e in experiences:
            if e.get("id") == exp_id:
                e["status"] = new_status
                if cmd == "approve":
                    e["approved_by"] = "cli"
                    e["approved_at"] = datetime.datetime.now().isoformat()
                e["review_notes"] = e.get("review_notes", []) + [args.review_notes]
                found = True
                break
        if not found:
            print(f"Experience not found: {exp_id}", file=sys.stderr)
            return 1
        report_data["experiences"] = experiences
        exp_path.write_text(json.dumps(report_data, indent=2, default=str), encoding="utf-8")
        print(f"Experience {exp_id} → {new_status}")
        return 0

    if cmd == "export-approved":
        approved = [e for e in experiences if e.get("status") == "approved"]
        if args.emit == "json":
            print(json.dumps({"experiences": approved}, indent=2, default=str))
        else:
            print(f"Approved experiences: {len(approved)}")
            for e in approved:
                print(f"  + {e['id']}: {e['title'][:60]}")
        return 0

    return 1


def cmd_mine(args) -> int:
    from lib import evidence_linker, github_search, issue_filter, pattern_extract

    cfg = env.get_config()
    if args.debug:
        log.set_debug(True)
    logger = log.get_logger()

    token = cfg.get("GITHUB_TOKEN") or None
    repos = [r.strip() for r in args.owner_repo.split(",")]
    logger.info(f"Mining repos: {repos}")

    all_candidates: list[schema.CandidatePattern] = []
    total_issues = 0
    bug_issues_count = 0

    for repo in repos:
        logger.info(f"Mining {repo}...")
        issues = github_search.search_closed_issues(
            repo, label=args.label, max_results=args.max_issues, token=token
        )
        logger.info(f"  Found {len(issues)} closed issues with label '{args.label}'")
        bug_issues = issue_filter.filter_issues(issues)
        logger.info(f"  After filter: {len(bug_issues)} likely-bug issues")
        total_issues += len(issues)
        bug_issues_count += len(bug_issues)
        language_hint = ""
        for issue in bug_issues:
            prs = evidence_linker.link_issue_to_prs(issue, repo, token)
            cand = pattern_extract.extract_candidate(issue, prs, repo, language_hint)
            if cand:
                all_candidates.append(cand)

    logger.info(f"Total candidates across all repos: {len(all_candidates)}")

    report = experience_mod.aggregate(
        all_candidates,
        repos,
        total_issues=total_issues,
        bug_issues=bug_issues_count,
    )
    report_md = experience_mod.to_markdown(report)
    report_json = report.model_dump_json(indent=2)

    bugplay_dir = store.save_experience(report_md, report_json)

    result_dict = report.model_dump()
    output = render.render_bug_experience(result_dict, emit=args.emit)
    print(output)

    logger.info(f"Bug experience report saved to {bugplay_dir / 'bug-experience.md'}")
    logger.info(f"Run `issueoracle review <repo> --experience {bugplay_dir / 'bug-experience.md'}`")
    store.write_last_run(
        {
            "command": "mine",
            "repos": repos,
            "candidates": len(all_candidates),
            "bugplay_dir": str(bugplay_dir),
        }
    )
    return 0


def main():
    args = build_parser().parse_args()
    if getattr(args, "debug", False):
        os.environ["ISSUEORACLE_DEBUG"] = "1"
    try:
        if args.command == "doctor":
            return cmd_doctor()
        elif args.command == "diagnose":
            return cmd_diagnose(args)
        elif args.command == "validate":
            return cmd_validate(args)
        elif args.command == "scan":
            return cmd_scan(args)
        elif args.command == "review":
            return cmd_review(args)
        elif args.command == "mine":
            return cmd_mine(args)
        elif args.command == "experience":
            return cmd_experience(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if os.environ.get("ISSUEORACLE_DEBUG"):
            import traceback

            traceback.print_exc(file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
