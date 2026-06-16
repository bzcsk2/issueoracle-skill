from __future__ import annotations

import json
from pathlib import Path

from lib import schema


def profile_repo(repo_path: str, changed_files: list[str] | None = None) -> schema.RepoProfile:
    repo = Path(repo_path).resolve()
    languages = _detect_languages(repo)
    frameworks = _detect_frameworks(repo)
    deps = _detect_dependencies(repo)
    pkg_mgrs = _detect_package_managers(repo)
    risk = _infer_risk_surfaces(frameworks, deps, repo)
    return schema.RepoProfile(
        repo_path=str(repo),
        languages=languages,
        frameworks=frameworks,
        package_managers=pkg_mgrs,
        dependencies=deps,
        risk_surfaces=risk,
        changed_files=changed_files or [],
    )


_SUFFIX_LANG = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
}


def _detect_languages(repo: Path) -> list[str]:
    langs: dict[str, int] = {}
    for f in repo.rglob("*"):
        if f.is_file() and f.suffix in _SUFFIX_LANG:
            lang = _SUFFIX_LANG[f.suffix]
            langs[lang] = langs.get(lang, 0) + 1
    sorted_langs = sorted(langs, key=langs.__getitem__, reverse=True)
    return sorted_langs[:5]


def _detect_frameworks(repo: Path) -> list[str]:
    frameworks: list[str] = []
    # pyproject.toml
    pyproject = repo / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="replace")
        if "fastapi" in content:
            frameworks.append("fastapi")
        if "django" in content:
            frameworks.append("django")
        if "flask" in content:
            frameworks.append("flask")
        if "sqlalchemy" in content:
            frameworks.append("sqlalchemy")
        if "pydantic" in content:
            frameworks.append("pydantic")
    # package.json
    pkg_json = repo / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8", errors="replace"))
            all_deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            for dep in all_deps:
                if "express" in dep.lower():
                    frameworks.append("express")
                if "next" in dep.lower():
                    frameworks.append("nextjs")
                if "react" in dep.lower():
                    frameworks.append("react")
        except Exception:
            pass
    return sorted(set(frameworks))


def _detect_dependencies(repo: Path) -> list[str]:
    deps: list[str] = []
    pyproject = repo / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="replace")
        import tomllib

        try:
            data = tomllib.loads(content)
            project = data.get("project", {})
            deps.extend(project.get("dependencies", []))
        except Exception:
            pass
    pkg_json = repo / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8", errors="replace"))
            deps.extend(data.get("dependencies", {}).keys())
        except Exception:
            pass
    return sorted(set(deps))


def _detect_package_managers(repo: Path) -> list[str]:
    mgrs: list[str] = []
    if (repo / "pyproject.toml").exists():
        mgrs.append("pip/uv")
    if (repo / "requirements.txt").exists():
        mgrs.append("pip")
    if (repo / "Pipfile").exists():
        mgrs.append("pipenv")
    if (repo / "poetry.lock").exists():
        mgrs.append("poetry")
    if (repo / "package.json").exists():
        mgrs.append("npm")
    if (repo / "yarn.lock").exists():
        mgrs.append("yarn")
    if (repo / "pnpm-lock.yaml").exists():
        mgrs.append("pnpm")
    if (repo / "go.mod").exists():
        mgrs.append("go")
    if (repo / "Cargo.toml").exists():
        mgrs.append("cargo")
    return mgrs


_RISK_KEYWORDS: dict[str, list[str]] = {
    "web": ["flask", "fastapi", "django", "express", "nextjs", "react"],
    "database": ["sqlalchemy", "django", "psycopg2", "pymongo", "mysql"],
    "auth": ["jwt", "oauth", "passport", "authlib", "python-jose"],
    "file_io": ["pillow", "pandas", "openpyxl"],
    "network": ["requests", "httpx", "aiohttp", "axios"],
}


def _infer_risk_surfaces(frameworks: list[str], deps: list[str], repo: Path) -> list[str]:
    surfaces: list[str] = []
    all_items = [f.lower() for f in frameworks] + [d.lower() for d in deps]
    for surface, keywords in _RISK_KEYWORDS.items():
        if any(kw in all_items for kw in keywords):
            surfaces.append(surface)
    if (any(repo.rglob("*/auth*")) or any(repo.rglob("*/login*"))) and "auth" not in surfaces:
        surfaces.append("auth")
    if repo.rglob("*/admin*") and "web" not in surfaces:
        surfaces.append("web")
    return sorted(set(surfaces))


def classify_project_type(profile: schema.RepoProfile) -> str:
    fw = {f.lower() for f in profile.frameworks}
    deps = {d.lower() for d in profile.dependencies}
    all_kw = fw | deps
    if any(
        k in all_kw for k in ("fastapi", "flask", "django", "express", "next", "koa", "starlette")
    ):
        return "web_api"
    if any(k in all_kw for k in ("click", "typer", "commander", "yargs", "cobra", "clap")):
        return "cli"
    if any(k in all_kw for k in ("react", "vue", "angular", "svelte")):
        return "frontend"
    if any(k in all_kw for k in ("pytest", "unittest", "mypy", "ruff", "black", "flake8")):
        return "library"
    return "library"


_TOPIC_MAP: dict[str, list[str]] = {
    "fastapi": ["fastapi"],
    "flask": ["flask"],
    "django": ["django"],
    "express": ["express"],
    "nextjs": ["nextjs"],
    "react": ["react"],
    "vue": ["vue"],
    "sqlalchemy": ["sqlalchemy"],
    "pydantic": ["pydantic"],
    "click": ["cli"],
    "typer": ["cli"],
    "pytest": ["testing"],
    "ruff": ["linter"],
    "numpy": ["numpy"],
    "pandas": ["pandas"],
    "requests": ["requests"],
}

_PROJECT_TYPE_TOPICS: dict[str, list[str]] = {
    "web_api": ["web-api", "rest-api"],
    "cli": ["cli"],
    "frontend": ["frontend"],
    "library": ["library"],
}


_LANGUAGE_NAMES = {
    "python",
    "typescript",
    "javascript",
    "rust",
    "go",
    "java",
    "ruby",
    "csharp",
    "cpp",
    "swift",
    "kotlin",
}


def infer_search_topics(profile: schema.RepoProfile) -> list[str]:
    topics: list[str] = []
    for name in list(profile.frameworks) + list(profile.dependencies):
        name_lower = name.lower()
        if name_lower in _TOPIC_MAP:
            topics.extend(_TOPIC_MAP[name_lower])
    # Only add project-type topics when we have no framework matches
    if not topics:
        project_type = classify_project_type(profile)
        topics.extend(_PROJECT_TYPE_TOPICS.get(project_type, []))
        primary_lang = profile.languages[0].lower() if profile.languages else "python"
        if primary_lang not in _LANGUAGE_NAMES:
            topics.append(primary_lang)
    # Exclude language names — they are not valid GitHub topics
    topics = [t for t in topics if t not in _LANGUAGE_NAMES]
    return list(dict.fromkeys(topics))[:3]
