from __future__ import annotations

import json
import os
import sys

import issueoracle
from lib import env, log, render
from lib import experience as experience_mod
from lib import store
from lib.version import __version__


def cmd_doctor() -> int:
    from lib import pack_loader

    checks = []
    ok = True

    python_ver = sys.version_info
    if python_ver >= (3, 12):
        checks.append(
            {
                "ok": True,
                "message": f"Python {python_ver.major}.{python_ver.minor}.{python_ver.micro}",
            }
        )
    else:
        checks.append(
            {"ok": False, "message": f"Python {python_ver.major}.{python_ver.minor} < 3.12"}
        )
        ok = False

    skill_dir = issueoracle.SCRIPT_DIR.parent
    if skill_dir.exists():
        checks.append({"ok": True, "message": f"Skill dir: {skill_dir}"})
    else:
        checks.append({"ok": False, "message": "Skill dir not found"})
        ok = False

    packs_dir = skill_dir / "packs"
    patterns, errors = pack_loader.load_pack_dir(packs_dir)
    if errors:
        checks.append(
            {"ok": False, "message": f"Packs: {len(patterns)} patterns, {len(errors)} errors"}
        )
        ok = False
    else:
        checks.append({"ok": True, "message": f"Packs: {len(patterns)} patterns"})

    fixtures_dir = skill_dir / "evals" / "fixtures"
    fixture_count = (
        len([d for d in fixtures_dir.iterdir() if d.is_dir()]) if fixtures_dir.exists() else 0
    )
    checks.append({"ok": True, "message": f"Eval fixtures: {fixture_count}"})

    git_available = False
    try:
        import subprocess

        subprocess.run(["git", "--version"], capture_output=True, timeout=5)
        git_available = True
    except Exception:
        pass
    checks.append(
        {"ok": git_available, "message": "Git: available" if git_available else "Git: not found"}
    )

    github_token = env.get_config().get("GITHUB_TOKEN")
    if github_token:
        checks.append({"ok": True, "message": "GitHub token: configured"})
    else:
        checks.append(
            {"ok": True, "message": "GitHub token: missing, public rate limit only (60 req/hr)"}
        )

    home = env.get_detectoracle_home()
    checks.append({"ok": True, "message": f"DETECTORACLE_HOME: {home}"})

    data = {
        "version": __version__,
        "checks": checks,
        "suggested": "/detectoracle scan .",
    }
    print(render.render_doctor(data))
    return 0 if ok else 1


def cmd_experience(args) -> int:
    store.ensure_home()
    exp_path = store.resolve_experience_json_path()

    if exp_path is None:
        print("No experience data found. Run `detectoracle mine` first.", file=sys.stderr)
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

    all_candidates = []
    total_issues = 0
    bug_issues_count = 0
    completed_issues_set: set[str] = set()
    run_dir = None

    if args.resume:
        last_run = store.find_last_run_dir()
        if last_run is None:
            logger.error("No previous run to resume")
            return 1
        run_dir = last_run
        progress = store.load_run(run_dir)
        completed_issues_set = set(progress.get("completed_issues", []))
        logger.info(
            f"Resuming run {progress['run_id']} ({len(completed_issues_set)} issues already done)"
        )
    else:
        run_dir = store.create_run(repos)

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
            issue_key = f"{repo}#{issue.number}"
            if issue_key in completed_issues_set:
                logger.debug(f"  Skipping already processed: {issue_key}")
                continue
            try:
                prs = evidence_linker.link_issue_to_prs(issue, repo, token)
                cand = pattern_extract.extract_candidate(issue, prs, repo, language_hint)
                if cand:
                    all_candidates.append(cand)
                    store.append_run_line(run_dir, "candidates.jsonl", cand.model_dump_json())
                store.append_run_line(run_dir, "issues.jsonl", issue.model_dump_json())
                if run_dir:
                    progress = store.load_run(run_dir)
                    progress.setdefault("completed_issues", []).append(issue_key)
                    store.save_run(run_dir, progress)
            except Exception as e:
                logger.warning(f"Failed to process {issue_key}: {e}")
                if run_dir:
                    store.append_run_line(
                        run_dir, "errors.jsonl", json.dumps({"issue": issue_key, "error": str(e)})
                    )

    if run_dir:
        progress = store.load_run(run_dir)
        progress["status"] = "completed"
        store.save_run(run_dir, progress)
        logger.info(f"Run progress saved to {run_dir / 'progress.json'}")

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
    logger.info(f"Run `detectoracle review <repo> --experience {bugplay_dir / 'experience.json'}`")
    store.write_last_run(
        {
            "command": "mine",
            "repos": repos,
            "candidates": len(all_candidates),
            "bugplay_dir": str(bugplay_dir),
        }
    )
    return 0


def main() -> int:
    args = issueoracle.build_parser().parse_args()
    if getattr(args, "debug", False):
        os.environ["DETECTORACLE_DEBUG"] = "1"
        os.environ.setdefault("ISSUEORACLE_DEBUG", "1")
    try:
        if args.command == "doctor":
            return cmd_doctor()
        if args.command == "diagnose":
            return issueoracle.cmd_diagnose(args)
        if args.command == "validate":
            return issueoracle.cmd_validate(args)
        if args.command == "scan":
            return issueoracle.cmd_scan(args)
        if args.command == "review":
            return issueoracle.cmd_review(args)
        if args.command == "mine":
            return cmd_mine(args)
        if args.command == "experience":
            return cmd_experience(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if os.environ.get("DETECTORACLE_DEBUG") or os.environ.get("ISSUEORACLE_DEBUG"):
            import traceback

            traceback.print_exc(file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
