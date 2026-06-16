from __future__ import annotations

import ast
import re
from pathlib import Path

from lib import schema

_LANG_SUFFIX = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".rb": "Ruby",
}

_CODE_SUFFIXES = set(_LANG_SUFFIX.keys()) | {
    ".css",
    ".html",
    ".sql",
    ".yaml",
    ".yml",
    ".toml",
    ".json",
}


def index_repo(
    repo_path: str, profile: schema.RepoProfile, only_files: list[str] | None = None
) -> list[schema.CodeChunk]:
    repo = Path(repo_path).resolve()
    chunks: list[schema.CodeChunk] = []
    target_files = only_files or _collect_code_files(repo, profile.languages)
    for f in target_files:
        f_path = Path(f) if isinstance(f, str) else f
        if not f_path.is_file():
            continue
        lang = _language_for_suffix(f_path.suffix)
        text = f_path.read_text(encoding="utf-8", errors="replace")
        try:
            if lang == "Python":
                chunks.extend(_index_python(f_path, text))
            elif lang in ("TypeScript", "JavaScript"):
                chunks.extend(_index_ts_js(f_path, text))
            else:
                chunks.extend(_index_fallback(f_path, text))
        except Exception:
            chunks.extend(_index_fallback(f_path, text))
    return chunks


def _collect_code_files(repo: Path, languages: list[str]) -> list[Path]:
    files: list[Path] = []
    for suffix in _CODE_SUFFIXES:
        files.extend(repo.rglob(f"*{suffix}"))
    result: list[Path] = []
    seen = set()
    for f in files:
        if f.name.startswith("."):
            continue
        parts = f.parts
        if any(
            p.startswith(".")
            or p == "__pycache__"
            or p == "node_modules"
            or p == ".venv"
            or p == "dist"
            or p == "build"
            for p in parts
        ):
            continue
        if str(f) not in seen:
            seen.add(str(f))
            result.append(f)
    return sorted(result)


def _language_for_suffix(suffix: str) -> str:
    return _LANG_SUFFIX.get(suffix, "Unknown")


def _index_python(file_path: Path, text: str) -> list[schema.CodeChunk]:
    chunks: list[schema.CodeChunk] = []
    try:
        tree = ast.parse(text, filename=str(file_path))
    except SyntaxError:
        return _index_fallback(file_path, text)

    imports = _get_imports(tree)
    signals = _extract_signals(text)

    has_function_or_class = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            has_function_or_class = True
            start = node.lineno or 0
            end = getattr(node, "end_lineno", None) or start
            code = _safe_extract_lines(text, start, end)
            chunks.append(
                schema.CodeChunk(
                    file=str(file_path),
                    start_line=start,
                    end_line=end,
                    symbol=node.name,
                    language="Python",
                    imports=imports,
                    signals=signals,
                    code_excerpt=code,
                )
            )
    if not has_function_or_class:
        lines = text.split("\n")
        chunks.append(
            schema.CodeChunk(
                file=str(file_path),
                start_line=1,
                end_line=len(lines),
                symbol=file_path.stem,
                language="Python",
                imports=imports,
                signals=signals,
                code_excerpt=text[:2000],
            )
        )
    return chunks


def _index_ts_js(file_path: Path, text: str) -> list[schema.CodeChunk]:
    chunks: list[schema.CodeChunk] = []
    pattern = re.compile(
        r"(?:export\s+)?(?:async\s+)?function\s+(\w+)|"
        r"(?:export\s+)?(?:async\s+)?\(?\s*(?:\w+\s*=\s*)?(?:async\s+)?(?:\([^)]*\))\s*(?:=>|:\s*async\s*\([^)]*\)\s*=>)|"
        r"(?:export\s+)?class\s+(\w+)|"
        r"(?:export\s+)?default\s+(?:function|class)\s+(\w+)|"
        r"const\s+(\w+)\s*=\s*(?:async\s*)?\(|"
        r'router\.(?:get|post|put|delete|patch)\s*\(\s*[\'"]',
    )
    lines = text.split("\n")
    imports = [
        line
        for line in lines
        if line.startswith("import ") or line.startswith("const ") and "require(" in line
    ]
    signals = _extract_signals(text)

    for i, line in enumerate(lines, 1):
        m = pattern.search(line)
        if m:
            name = next(g for g in m.groups() if g) or "anonymous"
            end = min(i + 30, len(lines))
            code = "\n".join(lines[i - 1 : end])
            chunks.append(
                schema.CodeChunk(
                    file=str(file_path),
                    start_line=i,
                    end_line=end,
                    symbol=name,
                    language="TypeScript",
                    imports=imports,
                    signals=signals,
                    code_excerpt=code,
                )
            )
    return chunks


_WINDOW_SIZE = 50
_WINDOW_STEP = 10


def _index_fallback(file_path: Path, text: str) -> list[schema.CodeChunk]:
    chunks: list[schema.CodeChunk] = []
    lines = text.split("\n")
    signals = _extract_signals(text[:2000])
    for start in range(0, len(lines), _WINDOW_STEP):
        end = min(start + _WINDOW_SIZE, len(lines))
        window = "\n".join(lines[start:end])
        if len(window.strip()) < 10:
            continue
        chunks.append(
            schema.CodeChunk(
                file=str(file_path),
                start_line=start + 1,
                end_line=end,
                symbol=f"lines-{start + 1}-{end}",
                language="Unknown",
                signals=signals,
                code_excerpt=window,
            )
        )
    return chunks


def _get_imports(tree: ast.AST) -> list[str]:
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def _extract_signals(text: str) -> list[str]:
    signals = []
    keywords = [
        "await ",
        "async ",
        "session",
        "query(",
        "execute(",
        "fetch(",
        ".all()",
        "commit()",
        "rollback()",
        "cursor",
        "db.",
        "try:",
        "except",
        "finally:",
        ".save()",
        ".delete()",
    ]
    for kw in keywords:
        if kw in text:
            signals.append(kw.strip())
    return list(dict.fromkeys(signals))[:10]


def _safe_extract_lines(text: str, start: int, end: int) -> str:
    lines = text.split("\n")
    return "\n".join(lines[max(0, start - 1) : min(len(lines), end)])
