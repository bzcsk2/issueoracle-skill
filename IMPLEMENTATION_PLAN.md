# IssueOracle Skill — 完整实施计划

> **文档定位**：这是 issueoracle-skill 从零开发的权威实施蓝图。任何执行 agent 照此文档逐步实施即可。
>
> **参考来源**：
> - `D:\Proj\issueoracle.md` —— 原始设计（15 节，定义了 Skill 架构、schema、安全规则、eval）
> - `D:\Proj\last30days-skill` —— Skill-first 参考实现（SKILL.md 合约 + Python engine + scripts/lib 模块化 + eval/verify + npx skills/symlink 安装）
>
> **当前状态**：`D:\Proj\issueoracle-skill` 已是空 git 仓库，根级文件（pyproject.toml/LICENSE/CLAUDE.md/AGENTS.md/SECURITY.md/CHANGELOG.md/CONTRIBUTING.md）已创建。

---

## 0. 关键方向调整（重要）

**与原始 issueoracle.md 的最大差异：mining 从 v0.2 前移到 v0.1 的核心交付。**

| 维度 | 原始 issueoracle.md | 本计划（v0.1） |
|------|---------------------|----------------|
| v0.1 核心 | 本地 pattern pack 审查 | **GitHub issue mining + 本地审查，双能力** |
| mining 时机 | v0.2 才做 | **v0.1 就做，且是主要卖点** |
| 内置 patterns | 10 个手工 patterns | 3-5 个 seed patterns（最小可用）+ mining 产出 candidate patterns |
| 用户主流程 | `/issueoracle review .` | `/issueoracle mine owner/repo` → 审阅候选 → `/issueoracle review .` |

**理由**：mining 是 IssueOracle 的护城河（"开源缺陷经验记忆层"）。如果第一版只有手工 patterns，它和普通 linter 没区别。把 mining 做进来，才能体现"从真实 OSS issue 提炼 bug pattern"的核心价值。

**v0.1 必须能跑通的端到端流程**：

```
用户：/issueoracle mine fastapi/fastapi
  ↓
engine：搜索 closed bug issues → 排除非 bug → 找 linked PR → 抽取 root cause/signals
  ↓
输出：candidate patterns 写入 ~/.issueoracle/mining/（不自动入 packs/）
  ↓
用户：人工审阅 candidate，确认后移入 packs/
  ↓
用户：/issueoracle review .
  ↓
engine：加载 packs + mining 产出的 patterns → 匹配本地代码 → 输出带证据的 finding 报告
```

---

## 1. 设计决策摘要（已确认）

| 决策点 | 选择 | 说明 |
|--------|------|------|
| Python 最低版本 | **3.12+** | 与 last30days 一致；有 tomllib、type parameter syntax |
| YAML Schema 校验 | **Pydantic v2** | 自动类型校验、嵌套模型、序列化 |
| Pattern Pack 语言 | **Python + TypeScript 先行** | FastAPI/SQLAlchemy/Django + Express/Next.js |
| v0.1 存储方案 | **文件系统** | JSON/Markdown 报告 + TOML 配置，零额外依赖 |
| Skill 形态 | **Skill-first** | SKILL.md 指挥 + Python engine 执行，不用 MCP |
| **mining 时机** | **v0.1 核心** | GitHub issue mining 是第一版主要交付 |
| GitHub 认证 | **GITHUB_TOKEN（可选）** | 无 token 走公开 API（低配额）；有 token 提高配额 |

---

## 2. 仓库最终目录结构

```
issueoracle-skill/
├── README.md                          # 项目首页、安装、快速开始
├── LICENSE                            # MIT
├── CHANGELOG.md                       # Keep a Changelog 格式
├── CONTRIBUTING.md                    # 贡献指南、PR 合并标准
├── SECURITY.md                        # 安全规则
├── CLAUDE.md                          # Claude Code 仓库级指令
├── AGENTS.md                          # Agent 入口（@CLAUDE.md 重定向）
├── IMPLEMENTATION_PLAN.md             # ★ 本文档
├── pyproject.toml                     # uv/pip 项目定义
├── uv.lock                            # 锁文件
│
├── skills/
│   └── issueoracle/
│       ├── SKILL.md                   # ★ 运行时唯一真相源
│       ├── nux-wizard.md              # 首次运行向导（可选 token 配置）
│       ├── agents/
│       │   └── default.yaml           # Agent manifest（interface + policy）
│       ├── references/
│       │   ├── pattern-schema.md      # Pattern YAML schema 文档
│       │   ├── review-report-format.md # 报告格式文档
│       │   ├── mining-workflow.md     # ★ mining 流程文档（v0.1 新增）
│       │   └── threat-model.md        # 威胁模型
│       ├── assets/
│       │   └── logo.svg               # Logo
│       ├── scripts/
│       │   ├── issueoracle.py         # ★ 核心 engine（argparse CLI）
│       │   ├── build-skill.sh         # 打包 .skill 文件
│       │   ├── verify.py              # 验证 bundle（unit + smoke）
│       │   ├── evaluate_patterns.py   # Eval runner
│       │   ├── store.py               # 本地文件系统存储
│       │   └── lib/
│       │       ├── __init__.py        # 空包标记（CLAUDE.md 规则）
│       │       ├── env.py             # 环境变量 + 配置加载
│       │       ├── config.py          # IssueOracle 配置模型
│       │       ├── schema.py          # Pydantic 数据模型
│       │       ├── profile.py         # Repo 语言/框架/依赖/风险面识别
│       │       ├── pack_loader.py     # Pattern pack 加载 + schema 校验
│       │       ├── code_index.py      # 代码切块（ast/正则/fallback）
│       │       ├── pattern_match.py   # 三段式匹配 + 评分
│       │       ├── review.py          # Finding 生成 + 过滤
│       │       ├── render.py          # Markdown/JSON/compact 输出
│       │       ├── github_search.py   # ★ GitHub issue/PR 搜索
│       │       ├── github_fetch.py    # ★ Issue/PR/commit 内容获取
│       │       ├── issue_filter.py    # ★ 排除非 bug issues
│       │       ├── evidence_linker.py # ★ issue→PR→commit 证据链
│       │       ├── pattern_extract.py # ★ 候选 pattern 生成
│       │       ├── safety.py          # GitHub 内容安全处理（提示注入防护）
│       │       ├── fs.py              # 文件系统工具
│       │       ├── git.py             # Git 操作（diff, changed files）
│       │       └── log.py             # 共享日志（DEBUG 模式）
│       ├── packs/                     # 内置 seed patterns（3-5 个）
│       │   ├── python/
│       │   │   └── fastapi/
│       │   │       ├── patterns.yaml
│       │   │       └── examples/
│       │   └── typescript/
│       │       └── express/
│       │           ├── patterns.yaml
│       │           └── examples/
│       └── evals/
│           ├── run_eval.py            # Eval runner CLI
│           ├── fixtures/              # bad/good 代码 fixtures
│           └── golden/                # expected outputs
│
└── tests/
    ├── conftest.py                   # sys.path 注入
    ├── __init__.py
    ├── test_schema.py
    ├── test_pack_loader.py
    ├── test_code_index.py
    ├── test_pattern_match.py
    ├── test_review.py
    ├── test_render.py
    ├── test_profile.py
    ├── test_git.py
    ├── test_store.py
    ├── test_safety.py
    ├── test_github_search.py          # ★ mining 测试
    ├── test_issue_filter.py           # ★ mining 测试
    ├── test_evidence_linker.py        # ★ mining 测试
    ├── test_pattern_extract.py        # ★ mining 测试
    └── test_integration.py            # 端到端
```

**★ 标记 = mining-first 方向新增/提升优先级的模块。**

---

## 3. Phase 划分（mining-first 重排）

| Phase | 名称 | 预计 | 核心交付 |
|-------|------|------|----------|
| **Phase 0** | 骨架搭建 | 1 天 | 项目骨架 + engine CLI 可跑 `diagnose` |
| **Phase 1** | Review 基础管线 | 2-3 天 | profile/pack_loader/code_index/match/review + 3-5 seed patterns + review 命令可用 |
| **Phase 2** | ★ GitHub Mining | 3-4 天 | search/fetch/filter/linker/extract + mine 命令可用 + candidate pattern 落盘 |
| **Phase 3** | Eval + 打磨 | 2 天 | eval fixtures + golden + verify + 文档 + 安装测试 |

**依赖关系**：Phase 1 是 Phase 2 的基础（mining 产出的 candidate pattern 必须能被 pack_loader 加载、被 review 消费）。Phase 2 不依赖 Phase 1 的 patterns 数量，只依赖 schema/loader/match 这套管线。

---

## 4. Phase 0：骨架搭建

### 4.1 目标产物（按顺序）

| # | 文件 | 用途 | 参考来源 |
|---|------|------|----------|
| 1 | `pyproject.toml` ✅ | 项目定义 | last30days pyproject.toml |
| 2 | `LICENSE` ✅ | MIT | — |
| 3 | `CLAUDE.md` ✅ | 仓库级 Agent 指令 | last30days CLAUDE.md |
| 4 | `AGENTS.md` ✅ | `@CLAUDE.md` 重定向 | last30days AGENTS.md |
| 5 | `SECURITY.md` ✅ | 6 条安全规则 + mining 安全补充 | issueoracle.md §11 |
| 6 | `CHANGELOG.md` ✅ | 空模板 | Keep a Changelog |
| 7 | `CONTRIBUTING.md` ✅ | 贡献指南 | issueoracle.md §14 |
| 8 | `scripts/lib/__init__.py` | 空包标记 | last30days lib/__init__.py |
| 9 | `scripts/lib/log.py` | DEBUG 日志 | last30days lib/log.py |
| 10 | `scripts/lib/env.py` | 环境变量 + 配置 | last30days lib/env.py（简化版） |
| 11 | `scripts/lib/config.py` | 配置模型 | — |
| 12 | `scripts/lib/schema.py` | Pydantic 数据模型 | last30days lib/schema.py（改用 Pydantic） |
| 13 | `scripts/lib/fs.py` | 文件系统工具 | — |
| 14 | `scripts/lib/render.py` | Markdown/JSON 输出 | last30days lib/render.py（简化版） |
| 15 | `scripts/store.py` | 文件系统存储 | — |
| 16 | `scripts/issueoracle.py` | 核心 engine CLI | last30days last30days.py |
| 17 | `SKILL.md` | ★ 运行时唯一真相源 | issueoracle.md §5 + last30days SKILL.md |
| 18 | `agents/default.yaml` | Agent manifest | last30days agents/openai.yaml |
| 19 | `scripts/build-skill.sh` | 打包 .skill | last30days build-skill.sh |
| 20 | `scripts/verify.py` | 验证 bundle | last30days verify_v3.py |
| 21 | `tests/conftest.py` + `tests/__init__.py` | 测试路径注入 | last30days conftest.py |
| 22 | `tests/test_schema.py` | schema round-trip | last30days test_schema_v3.py |
| 23 | `README.md` | 项目首页 | last30days README.md |

✅ = 已创建。

### 4.2 SKILL.md 核心设计

仿照 last30days SKILL.md 的 **frontmatter + 合约**结构。

**Frontmatter**：

```yaml
---
name: issueoracle
version: "0.1.0"
description: "Mine bug patterns from fixed GitHub issues, then review local code with concrete evidence."
argument-hint: "issueoracle review . | issueoracle mine owner/repo | issueoracle validate packs"
allowed-tools: Bash, Read, Write, AskUserQuestion, WebSearch
homepage: https://github.com/bzcsk2/issueoracle-skill
repository: https://github.com/bzcsk2/issueoracle-skill
author: bzcsk2
license: MIT
user-invocable: true
metadata:
  openclaw:
    emoji: "🔮"
requires:
  env: []
optionalEnv:
  - GITHUB_TOKEN
  - ISSUEORACLE_ALLOW_REMOTE_LLM
  - ISSUEORACLE_HOME
bins:
  - python3
files:
  - "scripts/*"
  - "packs/*"
  - "references/*"
tags:
  - code-review
  - bug-patterns
  - github-issues
  - oss
  - static-analysis
  - local-first
  - ai-skill
---
```

**合约正文骨架**（核心硬规则）：

```markdown
# IssueOracle Skill

You are inside the IssueOracle skill.

IssueOracle is not a generic code reviewer. It is a local bug-pattern review engine
that mines patterns from fixed GitHub issues and applies them to local code with evidence.
It must only report a finding when ALL of these exist:

1. A matched structured bug pattern.
2. Concrete local file/line evidence.
3. A plausible trigger condition.
4. A confidence score.
5. A false-positive boundary.
6. An OSS evidence link when the pattern came from public GitHub data.

Never claim code is buggy only because similar projects had similar issues.

## Runtime preflight
1. Resolve Python 3.12+.
2. Resolve SKILL_DIR from the loaded SKILL.md location.
3. Set ISSUEORACLE_HOME to ~/.issueoracle if unset.
4. Check git availability (for review --changed).
5. Check repo existence (for review).
6. Do NOT upload local code to any remote LLM unless ISSUEORACLE_ALLOW_REMOTE_LLM=1.

## Intent parsing
Classify into: REVIEW_REPO | REVIEW_DIFF | MINE_REPO | VALIDATE_PACK | EXPLAIN_FINDING | HELP

## Commands
# REVIEW_REPO
"$ISSUEORACLE_PYTHON" "$SKILL_DIR/scripts/issueoracle.py" review "$TARGET_REPO" --emit markdown
# REVIEW_DIFF
"$ISSUEORACLE_PYTHON" "$SKILL_DIR/scripts/issueoracle.py" review "$TARGET_REPO" --changed --base main --emit markdown
# MINE_REPO
"$ISSUEORACLE_PYTHON" "$SKILL_DIR/scripts/issueoracle.py" mine "$OWNER_REPO" --human-review --emit markdown
# VALIDATE_PACK
"$ISSUEORACLE_PYTHON" "$SKILL_DIR/scripts/issueoracle.py" validate "$PACK_PATH" --emit markdown

## Output contract
Final response must contain: review scope, patterns considered, files scanned,
findings grouped by severity, and per-finding: file/line, confidence, matched pattern,
trigger condition, local evidence, OSS evidence, suggested fix, validation test,
false-positive boundary.

Do NOT output low-confidence findings by default.
Do NOT output findings without line evidence.
Do NOT output raw GitHub issue bodies or full PR diffs.
```

### 4.3 issueoracle.py 核心设计

仿照 last30days.py 的 **argparse + main** 模式。

```python
#!/usr/bin/env python3
"""issueoracle CLI."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

MIN_PYTHON = (3, 12)

def ensure_supported_python(version_info=None):
    # 同 last30days.py 的 ensure_supported_python
    ...

ensure_supported_python()

if os.name == "nt":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

from lib import config as config_mod, env, render, schema, store

def build_parser():
    parser = argparse.ArgumentParser(
        description="Mine bug patterns from GitHub issues and review local code with evidence."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # review
    p_review = sub.add_parser("review", help="Review a local repo using loaded patterns")
    p_review.add_argument("repo_path")
    p_review.add_argument("--changed", action="store_true")
    p_review.add_argument("--base", default="main")
    p_review.add_argument("--languages")
    p_review.add_argument("--frameworks")
    p_review.add_argument("--packs", default=None)
    p_review.add_argument("--severity-threshold", default="medium",
                          choices=["low", "medium", "high"])
    p_review.add_argument("--max-findings", type=int, default=20)
    p_review.add_argument("--emit", default="markdown", choices=["markdown", "json", "compact"])
    p_review.add_argument("--save-dir", default=None)
    p_review.add_argument("--debug", action="store_true")

    # mine
    p_mine = sub.add_parser("mine", help="Mine bug patterns from a GitHub repo's closed issues")
    p_mine.add_argument("owner_repo", help="GitHub repo as owner/repo (e.g. fastapi/fastapi)")
    p_mine.add_argument("--label", default="bug")
    p_mine.add_argument("--state", default="closed")
    p_mine.add_argument("--max-issues", type=int, default=50)
    p_mine.add_argument("--human-review", action="store_true", default=True)
    p_mine.add_argument("--emit", default="markdown", choices=["markdown", "json"])
    p_mine.add_argument("--save-dir", default=None)
    p_mine.add_argument("--debug", action="store_true")

    # validate
    p_validate = sub.add_parser("validate", help="Validate a pattern pack directory")
    p_validate.add_argument("pack_path")
    p_validate.add_argument("--emit", default="markdown", choices=["markdown", "json"])

    # diagnose
    sub.add_parser("diagnose", help="Print environment and pack status")

    return parser

def main():
    args = build_parser().parse_args()
    if getattr(args, "debug", False):
        os.environ["ISSUEORACLE_DEBUG"] = "1"

    if args.command == "diagnose":
        print(json.dumps(diagnose(), indent=2, sort_keys=True))
        return 0
    elif args.command == "validate":
        return cmd_validate(args)
    elif args.command == "review":
        return cmd_review(args)
    elif args.command == "mine":
        return cmd_mine(args)
    return 2
```

### 4.4 schema.py Pydantic 模型（v0.1 完整版）

```python
"""Pydantic data models for IssueOracle."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, field_validator

Severity = Literal["low", "medium", "high", "critical"]
Strength = Literal["low", "medium", "high"]

# --- Pattern pack 层 ---

class OssEvidence(BaseModel):
    repo: str                       # owner/repo
    issue: int | None = None
    pr: int | None = None
    commit: str | None = None
    url: str                        # 必须有完整 URL
    strength: Strength = "medium"

class TriggerCondition(BaseModel):
    description: str
    code_signals: list[str] = Field(default_factory=list)

class Pattern(BaseModel):
    id: str
    title: str
    language: str                   # Python / TypeScript / Go / Rust
    frameworks: list[str] = Field(default_factory=list)
    bug_type: str                   # resource_leak / sql_injection / ...
    severity_hint: Severity = "medium"
    symptoms: list[str] = Field(default_factory=list)
    root_cause: str
    trigger_conditions: list[TriggerCondition] = Field(default_factory=list)
    bad_code_signals: list[str] = Field(default_factory=list)
    fix_patterns: list[str] = Field(default_factory=list)
    evidence: list[OssEvidence] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    false_positive_boundary: str = ""

    @field_validator("evidence")
    @classmethod
    def evidence_non_empty(cls, v):
        if not v:
            raise ValueError("pattern must have at least one OSS evidence")
        return v

# --- Review 层 ---

class CodeChunk(BaseModel):
    file: str
    start_line: int
    end_line: int
    symbol: str
    language: str
    imports: list[str] = Field(default_factory=list)
    signals: list[str] = Field(default_factory=list)
    code_excerpt: str = ""

class RepoProfile(BaseModel):
    repo_path: str
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    package_managers: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    risk_surfaces: list[str] = Field(default_factory=list)
    changed_files: list[str] = Field(default_factory=list)

class LocalEvidence(BaseModel):
    line: int
    description: str

class Finding(BaseModel):
    id: str
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    file: str
    start_line: int
    end_line: int
    title: str
    matched_pattern: str
    trigger_condition: str
    local_evidence: list[LocalEvidence] = Field(default_factory=list)
    oss_evidence: list[OssEvidence] = Field(default_factory=list)
    suggested_fix: str
    validation: str
    false_positive_boundary: str

class ReviewReport(BaseModel):
    version: str
    scope: dict                      # repo, mode, patterns_loaded, files_scanned
    summary: dict                    # findings_total, suppressed, by_severity
    findings: list[Finding]
    suppressed: list[Finding]

# --- Mining 层（v0.1 新增）---

class GitHubIssue(BaseModel):
    number: int
    title: str
    state: str
    labels: list[str] = Field(default_factory=list)
    body: str = ""
    url: str
    created_at: str
    closed_at: str | None = None
    author: str = ""

class LinkedPR(BaseModel):
    number: int
    title: str
    state: str
    merged: bool
    url: str
    commit_sha: str | None = None
    files_changed: list[str] = Field(default_factory=list)

class CandidatePattern(BaseModel):
    """mining 产出，待人工审阅的候选 pattern。结构与 Pattern 一致但 confidence 偏保守。"""
    id: str
    title: str
    language: str
    frameworks: list[str] = Field(default_factory=list)
    bug_type: str
    severity_hint: Severity = "medium"
    symptoms: list[str] = Field(default_factory=list)
    root_cause: str
    trigger_conditions: list[TriggerCondition] = Field(default_factory=list)
    bad_code_signals: list[str] = Field(default_factory=list)
    fix_patterns: list[str] = Field(default_factory=list)
    evidence: list[OssEvidence]
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    false_positive_boundary: str = ""
    source_issue: int                # 来自哪个 issue
    source_repo: str
    status: Literal["candidate", "approved", "rejected"] = "candidate"

class MiningResult(BaseModel):
    repo: str
    mined_at: str
    issues_searched: int
    issues_kept: int                 # issue_filter 之后
    issues_with_pr: int              # 有 linked PR 的
    candidates: list[CandidatePattern]
    raw_dir: str                     # raw issue/PR 数据落盘目录
    review_path: str                 # review.md 路径

class ValidationResult(BaseModel):
    pack_path: str
    patterns_valid: int
    patterns_invalid: int
    errors: list[dict]               # [{file, pattern_id, errors: [..]}]
```

### 4.5 env.py 设计

仿照 last30days 的三层优先级，大幅简化（无 Keychain、无浏览器 cookie）。

```python
"""Environment and configuration for IssueOracle skill."""
from __future__ import annotations
import os, tomllib
from pathlib import Path
from typing import Any

_config_override = os.environ.get("ISSUEORACLE_CONFIG_DIR")
if _config_override == "":
    CONFIG_DIR = None
elif _config_override:
    CONFIG_DIR = Path(_config_override)
else:
    CONFIG_DIR = Path.home() / ".issueoracle"

# ISSUEORACLE_HOME 是数据目录（reports/cache/mining），CONFIG_DIR 是配置目录
HOME_OVERRIDE = os.environ.get("ISSUEORACLE_HOME")
ISSUEORACLE_HOME = Path(HOME_OVERRIDE) if HOME_OVERRIDE else (Path.home() / ".issueoracle")

def load_toml(path: Path) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)

def get_config() -> dict[str, Any]:
    """Priority: os.environ > project .issueoracle/config.toml > global config.toml."""
    global_cfg = load_toml(CONFIG_DIR / "config.toml") if CONFIG_DIR else {}
    # project config: 向上查找 .issueoracle/config.toml
    project_cfg = {}
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
```

### 4.6 store.py 文件系统存储

```python
"""File-system storage for IssueOracle (no SQLite in v0.1)."""
from __future__ import annotations
import datetime, json
from pathlib import Path
from lib import env

def ensure_home() -> Path:
    home = env.ISSUEORACLE_HOME
    (home / "reports").mkdir(parents=True, exist_ok=True)
    (home / "cache" / "github").mkdir(parents=True, exist_ok=True)
    (home / "cache" / "repo-profile").mkdir(parents=True, exist_ok=True)
    (home / "mining").mkdir(parents=True, exist_ok=True)
    return home

def save_report(report_md: str, report_json: str, repo_slug: str) -> tuple[Path, Path]:
    home = ensure_home()
    ts = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    md_path = home / "reports" / f"{ts}-{repo_slug}-review.md"
    json_path = home / "reports" / f"{ts}-{repo_slug}-review.json"
    md_path.write_text(report_md, encoding="utf-8")
    json_path.write_text(report_json, encoding="utf-8")
    return md_path, json_path

def save_mining(result_json: str, repo_slug: str) -> Path:
    """mining 结果落盘到 ~/.issueoracle/mining/<repo>_<date>/"""
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
```

### 4.7 验收标准（Phase 0）

```bash
python3 skills/detectoracle/scripts/issueoracle.py diagnose
# → 输出环境/依赖/pack 状态 JSON（python 版本、pydantic/pyyaml 可用、packs 数量）

python3 skills/detectoracle/scripts/issueoracle.py validate skills/detectoracle/packs
# → 0 patterns loaded（此时 packs 还没写）

bash skills/detectoracle/scripts/build-skill.sh
# → 打包 dist/issueoracle.skill

python3 -m pytest tests/test_schema.py -q
# → schema round-trip 全绿
```

---

## 5. Phase 1：Review 基础管线

### 5.1 目标产物

| # | 文件 | 职责 |
|---|------|------|
| 1 | `scripts/lib/git.py` | Git diff、changed files 获取 |
| 2 | `scripts/lib/profile.py` | Repo 语言/框架/依赖/风险面识别 |
| 3 | `scripts/lib/pack_loader.py` | Pattern pack 加载 + Pydantic schema 校验 |
| 4 | `scripts/lib/code_index.py` | 代码切块（Python ast, TS 正则, fallback） |
| 5 | `scripts/lib/pattern_match.py` | 三段式匹配 + 评分 |
| 6 | `scripts/lib/review.py` | Finding 生成 + 硬规则过滤 |
| 7 | 3-5 个 seed patterns | Python FastAPI + TS Express |
| 8 | `issueoracle.py` 的 review 命令 | 端到端 review |
| 9 | 对应单元测试 | test_profile/pack_loader/code_index/pattern_match/review/git |

### 5.2 profile.py 设计

输入：`repo_path`（`.` 或指定路径）

识别来源与优先级：
1. `pyproject.toml` / `requirements.txt` / `setup.py` → Python + 依赖
2. `package.json` / `tsconfig.json` → TypeScript + 框架
3. 文件后缀统计 → 语言
4. import/require 语句扫描 → 框架 + 依赖
5. 目录结构 → 风险面（如 `app/` + `db/` → web/db 风险面）

输出：`RepoProfile`

```python
def profile_repo(repo_path: str, changed_files: list[str] | None = None) -> RepoProfile:
    repo = Path(repo_path).resolve()
    languages = _detect_languages(repo)
    frameworks = _detect_frameworks(repo)
    deps = _detect_dependencies(repo)
    pkg_mgrs = _detect_package_managers(repo)
    risk = _infer_risk_surfaces(frameworks, deps, repo)
    return RepoProfile(
        repo_path=str(repo),
        languages=languages,
        frameworks=frameworks,
        package_managers=pkg_mgrs,
        dependencies=deps,
        risk_surfaces=risk,
        changed_files=changed_files or [],
    )
```

### 5.3 code_index.py 设计

v0.1 切块策略：

| 语言 | 切块方式 | 实现 |
|------|----------|------|
| Python | `ast.parse` → function/class/async function | `ast.walk` |
| TypeScript | 正则 → function/class/export/component | 粗粒度 |
| 其他 | 文件 + 滑动窗口（50 行窗口，10 行步长） | fallback |

```python
def index_repo(repo_path: str, profile: RepoProfile,
               only_files: list[str] | None = None) -> list[CodeChunk]:
    repo = Path(repo_path).resolve()
    chunks: list[CodeChunk] = []
    target_files = only_files or _collect_code_files(repo, profile.languages)
    for f in target_files:
        lang = _language_for_suffix(f.suffix)
        text = f.read_text(encoding="utf-8", errors="replace")
        if lang == "Python":
            chunks.extend(_index_python(f, text))
        elif lang == "TypeScript":
            chunks.extend(_index_typescript(f, text))
        else:
            chunks.extend(_index_fallback(f, text))
    return chunks
```

### 5.4 pattern_match.py 三段式匹配

```python
def match(chunks: list[CodeChunk], patterns: list[Pattern],
          profile: RepoProfile) -> list[MatchResult]:
    results = []
    for pattern in patterns:
        # Stage 1: metadata 召回
        if not _metadata_recall(pattern, profile):
            continue
        for chunk in chunks:
            # Stage 2: static signal 匹配
            signal_hits = _match_signals(pattern.bad_code_signals, chunk)
            if not signal_hits:
                continue
            # Stage 3: trigger judge（v0.1 规则匹配）
            trigger_cov = _trigger_coverage(pattern.trigger_conditions, chunk)
            if trigger_cov == 0.0:
                continue
            score = _score(pattern, signal_hits, trigger_cov)
            results.append(MatchResult(pattern=pattern, chunk=chunk,
                                       signal_hits=signal_hits,
                                       trigger_coverage=trigger_cov, score=score))
    return results

def _score(pattern, signal_hits, trigger_cov) -> float:
    return (
        0.25 * pattern.confidence
      + 0.25 * min(1.0, len(signal_hits) / 2)       # code_match_confidence
      + 0.20 * _evidence_strength(pattern)            # evidence_strength
      + 0.15 * trigger_cov                            # trigger_condition_coverage
      + 0.15 * min(1.0, len(signal_hits) / 3)        # static_signal_strength
    )
```

### 5.5 review.py 硬规则过滤

```python
SEVERITY_THRESHOLD = {"low": 0.3, "medium": 0.5, "high": 0.7}

def build_findings(matches: list[MatchResult], threshold: str,
                   max_findings: int) -> tuple[list[Finding], list[Finding]]:
    findings, suppressed = [], []
    for m in matches:
        if m.score < SEVERITY_THRESHOLD[threshold]:
            continue
        f = _to_finding(m)
        # 硬规则：缺字段不输出
        if not f.file or not f.matched_pattern or not f.trigger_condition:
            suppressed.append(f); continue
        if f.confidence < SEVERITY_THRESHOLD[threshold]:
            suppressed.append(f); continue
        findings.append(f)
    findings.sort(key=lambda x: x.confidence, reverse=True)
    return findings[:max_findings], suppressed + findings[max_findings:]
```

### 5.6 Seed Patterns（3-5 个）

**Python FastAPI (3 个)**：
1. `py-fastapi-async-session-leak` — 异步 SQLAlchemy session 未在异常路径关闭
2. `py-fastapi-cors-wildcard` — CORS 配置为 `*` 且允许凭证
3. `py-fastapi-sync-in-async` — async 路由中调用同步阻塞 I/O

**TypeScript Express (2 个)**：
4. `ts-express-error-handling-missing` — Express async handler 未包装 try-catch
5. `ts-express-auth-bypass-path` — 认证中间件路径配置错误

每个 pattern 配 `examples/<id>.bad.py` 和 `examples/<id>.good.py`。

### 5.7 验收标准（Phase 1）

```bash
python3 scripts/issueoracle.py validate skills/detectoracle/packs
# → 5 patterns loaded, 0 errors

python3 scripts/issueoracle.py review . --emit markdown
# → 输出带 findings 的 Markdown 报告

python3 scripts/issueoracle.py review . --emit json
# → 结构化 JSON

python3 scripts/issueoracle.py review . --changed --base main --emit markdown
# → 只报告 changed files 的 findings

python3 -m pytest tests/test_profile.py tests/test_pack_loader.py \
    tests/test_code_index.py tests/test_pattern_match.py tests/test_review.py -q
# → 全绿
```

---

## 6. Phase 2：★ GitHub Mining（v0.1 核心交付）

这是与原 issueoracle.md 的最大差异点。mining 从 v0.2 提升到 v0.1。

### 6.1 目标产物

| # | 文件 | 职责 |
|---|------|------|
| 1 | `scripts/lib/github_search.py` | GitHub issue/PR 搜索（REST API + search syntax） |
| 2 | `scripts/lib/github_fetch.py` | Issue/PR/commit/timeline 内容获取 |
| 3 | `scripts/lib/issue_filter.py` | 排除非 bug issues（question/docs/feature/duplicate/wontfix/invalid） |
| 4 | `scripts/lib/evidence_linker.py` | 建立 issue → linked PR → commit 证据链 |
| 5 | `scripts/lib/pattern_extract.py` | 从 issue+PR 抽取 candidate pattern（root cause/signals/fix） |
| 6 | `scripts/lib/safety.py` | GitHub 内容安全处理（提示注入防护） |
| 7 | `issueoracle.py` 的 mine 命令 | 端到端 mining |
| 8 | `references/mining-workflow.md` | mining 流程文档 |
| 9 | 对应单元测试 | test_github_search/issue_filter/evidence_linker/pattern_extract/safety |

### 6.2 GitHub API 策略

**认证**：
- 有 `GITHUB_TOKEN`：5000 req/hour
- 无 token：60 req/hour（只能处理小批量，diagnose 时警告）

**搜索语法**（issue_filter 用）：
```
repo:fastapi/fastapi is:issue is:closed label:bug sort:updated-desc
```

排除标签（issue_filter）：
```python
EXCLUDE_LABELS = {
    "question", "documentation", "docs", "feature", "enhancement",
    "duplicate", "wontfix", "invalid", "wont-fix", "discussion",
    "good first issue", "help wanted",
}
```

**关键 API 端点**：
| 用途 | 端点 |
|------|------|
| 搜索 issues | `GET /search/issues?q=...` |
| Issue 详情 | `GET /repos/{owner}/{repo}/issues/{number}` |
| Issue timeline（找 linked PR） | `GET /repos/{owner}/{repo}/issues/{number}/timeline` |
| PR 详情 | `GET /repos/{owner}/{repo}/pulls/{number}` |
| PR files | `GET /repos/{owner}/{repo}/pulls/{number}/files` |
| Commit | `GET /repos/{owner}/{repo}/commits/{sha}` |

### 6.3 github_search.py 设计

```python
"""GitHub issue/PR search via REST API."""
from __future__ import annotations
import os, urllib.parse, urllib.request, json
from typing import Any
from lib import env, schema, safety

GITHUB_API = "https://api.github.com"

def _headers(token: str | None) -> dict[str, str]:
    h = {"Accept": "application/vnd.github+json",
         "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h

def _request(path: str, token: str | None, params: dict | None = None) -> Any:
    url = f"{GITHUB_API}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=_headers(token))
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def search_closed_issues(owner_repo: str, *, label: str = "bug",
                         max_results: int = 50,
                         token: str | None = None) -> list[schema.GitHubIssue]:
    q = f"repo:{owner_repo} is:issue is:closed label:{label} sort:updated-desc"
    data = _request("/search/issues", token, {"q": q, "per_page": min(max_results, 100)})
    issues = []
    for item in data.get("items", [])[:max_results]:
        # safety: 截断 body，不保留完整原文
        safe_body = safety.sanitize_issue_body(item.get("body") or "")
        issues.append(schema.GitHubIssue(
            number=item["number"],
            title=item["title"],
            state=item["state"],
            labels=[l["name"] for l in item.get("labels", [])],
            body=safe_body,
            url=item["html_url"],
            created_at=item["created_at"],
            closed_at=item.get("closed_at"),
            author=item.get("user", {}).get("login", ""),
        ))
    return issues

def check_rate_limit(token: str | None) -> dict:
    data = _request("/rate_limit", token)
    core = data["resources"]["core"]
    search = data["resources"]["search"]
    return {"core_remaining": core["remaining"], "core_limit": core["limit"],
            "search_remaining": search["remaining"], "search_limit": search["limit"]}
```

### 6.4 github_fetch.py 设计

```python
"""Fetch issue/PR/commit details and timelines."""
from __future__ import annotations
from lib import github_search, schema, safety

def fetch_timeline(owner_repo: str, issue_number: int,
                   token: str | None = None) -> list[dict]:
    """获取 issue timeline，找 cross-referenced PR（linked PR）。"""
    # timeline 含 cross-reference / referenced 事件，能找到链接的 PR
    data = github_search._request(
        f"/repos/{owner_repo}/issues/{issue_number}/timeline",
        token, {"per_page": 100}
    )
    return data if isinstance(data, list) else []

def find_linked_prs(owner_repo: str, issue_number: int,
                    token: str | None = None) -> list[int]:
    """从 timeline 提取 linked PR 编号。"""
    timeline = fetch_timeline(owner_repo, issue_number, token)
    pr_numbers = []
    for event in timeline:
        # cross-referenced 事件的 source 可能是 PR
        src = event.get("source", {}).get("issue", {})
        if src.get("pull_request") and src.get("number"):
            pr_numbers.append(src["number"])
        # 也检查 PR body 里的 closes/fixes 关键词（在 pattern_extract 里做）
    return list(dict.fromkeys(pr_numbers))  # 去重保序

def fetch_pr(owner_repo: str, pr_number: int,
             token: str | None = None) -> schema.LinkedPR | None:
    data = github_search._request(f"/repos/{owner_repo}/pulls/{pr_number}", token)
    return schema.LinkedPR(
        number=data["number"],
        title=data["title"],
        state=data["state"],
        merged=data.get("merged", False),
        url=data["html_url"],
        commit_sha=(data.get("merge_commit_sha") or "") or None,
        files_changed=[],  # 单独 fetch，避免无谓请求
    )

def fetch_pr_files(owner_repo: str, pr_number: int,
                   token: str | None = None) -> list[str]:
    """获取 PR 改了哪些文件（只保留文件名，不保留 diff 内容）。"""
    data = github_search._request(
        f"/repos/{owner_repo}/pulls/{pr_number}/files", token, {"per_page": 100}
    )
    return [f["filename"] for f in data] if isinstance(data, list) else []
```

### 6.5 issue_filter.py 设计

```python
"""Filter out non-bug issues."""
from __future__ import annotations
from lib import schema

EXCLUDE_LABELS = {
    "question", "documentation", "docs", "feature", "enhancement",
    "duplicate", "wontfix", "wont-fix", "invalid", "discussion",
    "good first issue", "help wanted", "support",
}

# title 关键词启发式：明显不是 bug 的
NON_BUG_TITLE_HINTS = (
    "how to", "question:", "[question]", "feature request",
    "proposal:", "rfc:", "discussion:",
)

def is_likely_bug(issue: schema.GitHubIssue) -> bool:
    labels_lower = {l.lower() for l in issue.labels}
    # 排除明显非 bug 标签
    if labels_lower & EXCLUDE_LABELS:
        return False
    # 排除非 bug 标题
    title_lower = issue.title.lower()
    if any(hint in title_lower for hint in NON_BUG_TITLE_HINTS):
        return False
    # bug 标签优先通过
    if "bug" in labels_lower:
        return True
    # 启发式：标题含 bug/crash/error/leak/exception/fail 等
    bug_words = ("bug", "crash", "error", "leak", "exception", "fail",
                 "broken", "wrong", "incorrect", "regression", "hang", "deadlock")
    if any(w in title_lower for w in bug_words):
        return True
    return False

def filter_issues(issues: list[schema.GitHubIssue]) -> list[schema.GitHubIssue]:
    return [i for i in issues if is_likely_bug(i)]
```

### 6.6 evidence_linker.py 设计

```python
"""Link issues to their fixing PRs/commits, building evidence chains."""
from __future__ import annotations
import re
from lib import github_fetch, schema

# PR body / commit message 里链接 issue 的关键词
CLOSE_KEYWORDS = re.compile(
    r"\b(close[sd]?|fix(es|ed)?|resolve[sd]?|resolves|fixed)\s+"
    r"(?:#?(\d+)|(?:[\w-]+/[\w-]+)?#(\d+))",
    re.IGNORECASE,
)

def link_issue_to_prs(issue: schema.GitHubIssue, owner_repo: str,
                      token: str | None = None) -> list[schema.LinkedPR]:
    prs: list[schema.LinkedPR] = []
    seen = set()
    # 1. timeline cross-reference
    for pr_num in github_fetch.find_linked_prs(owner_repo, issue.number, token):
        if pr_num in seen:
            continue
        pr = github_fetch.fetch_pr(owner_repo, pr_num, token)
        if pr and pr.merged:
            prs.append(pr); seen.add(pr_num)
    # 2. 反向：搜索引用了该 issue 的 PR（closes #N）
    # （可选，timeline 通常已覆盖；为节省 API 配额，v0.1 先只靠 timeline）
    return prs

def build_evidence(issue: schema.GitHubIssue, prs: list[schema.LinkedPR],
                   owner_repo: str) -> list[schema.OssEvidence]:
    """从 issue + linked PRs 构造 OssEvidence 列表。"""
    evidences = []
    for pr in prs:
        evidences.append(schema.OssEvidence(
            repo=owner_repo,
            issue=issue.number,
            pr=pr.number,
            commit=pr.commit_sha,
            url=issue.url,
            strength="high" if pr.merged else "medium",
        ))
    if not evidences:
        # 至少留一条 issue 级别的证据
        evidences.append(schema.OssEvidence(
            repo=owner_repo, issue=issue.number, url=issue.url, strength="low",
        ))
    return evidences
```

### 6.7 pattern_extract.py 设计

```python
"""Extract candidate bug patterns from issue + PR evidence."""
from __future__ import annotations
import re
from lib import schema, safety

def extract_candidate(issue: schema.GitHubIssue, prs: list[schema.LinkedPR],
                      owner_repo: str, language_hint: str = "") -> schema.CandidatePattern | None:
    """从 issue + PR 抽取候选 pattern。

    v0.1 策略：启发式抽取 + 结构化填充。不做 LLM 调用（local-only）。
    """
    # root_cause: 优先从 PR title/body 抽取（"fix: ..."），否则用 issue title
    root_cause = _extract_root_cause(issue, prs)
    if not root_cause:
        return None

    # bad_code_signals: 从 issue body 找代码块关键词
    signals = _extract_signals(issue.body)
    # fix_patterns: 从 PR title/body 找
    fixes = _extract_fixes(prs)
    # trigger_conditions: 从 issue symptoms 推断
    triggers = _infer_triggers(issue, signals)

    pid = f"mined-{owner_repo.replace('/', '-')}-{issue.number}"
    return schema.CandidatePattern(
        id=pid,
        title=issue.title,
        language=language_hint or _guess_language(owner_repo),
        frameworks=_guess_frameworks(owner_repo),
        bug_type=_classify_bug_type(issue.title, signals),
        severity_hint="medium",
        symptoms=_extract_symptoms(issue.body),
        root_cause=root_cause,
        trigger_conditions=triggers,
        bad_code_signals=signals,
        fix_patterns=fixes,
        evidence=safety.build_safe_evidence(issue, prs, owner_repo),
        confidence=0.5,  # 候选默认保守
        false_positive_boundary=(
            "This candidate was auto-extracted from a single OSS issue. "
            "Verify the trigger condition applies to your codebase before trusting it."
        ),
        source_issue=issue.number,
        source_repo=owner_repo,
        status="candidate",
    )

def _extract_root_cause(issue, prs) -> str:
    for pr in prs:
        # PR title 常是 "fix: <root cause>"
        if pr.title.lower().startswith(("fix", "fixes")):
            return pr.title.split(":", 1)[-1].strip()
    return issue.title

def _extract_signals(body: str) -> list[str]:
    """从 issue body 的代码块里抽取可能的 bad code signal。"""
    signals = []
    for block in re.findall(r"```(?:python|typescript|go|rust|js|ts)?\n(.*?)```", body, re.DOTALL):
        # 简单启发式：找 await/async/session/query/exec 等关键词
        for kw in ("await ", "async ", "session", "query(", "execute(", "fetch(",
                   ".all()", "commit()", "rollback()"):
            if kw in block:
                signals.append(kw.strip())
    return list(dict.fromkeys(signals))[:5]
```

### 6.8 safety.py 设计（提示注入防护）

```python
"""Safety handling for untrusted GitHub content."""
from __future__ import annotations
import re
from lib import schema

MAX_BODY_CHARS = 2000

# 危险模式：可能是 prompt injection
DANGEROUS_PATTERNS = [
    (re.compile(r"<system[^>]*>", re.IGNORECASE), "[redacted system tag]"),
    (re.compile(r"ignore\s+(?:previous|all|the above)\s+instructions", re.IGNORECASE),
     "[redacted injection attempt]"),
    (re.compile(r"```(?:bash|sh|shell|cmd|powershell)\n.*?```", re.DOTALL),
     "[redacted shell block]"),
]

def sanitize_issue_body(body: str) -> str:
    """截断 + 移除危险内容。绝不执行 issue 里的任何命令。"""
    if not body:
        return ""
    cleaned = body
    for pattern, replacement in DANGEROUS_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)
    if len(cleaned) > MAX_BODY_CHARS:
        cleaned = cleaned[:MAX_BODY_CHARS] + "\n...[truncated]"
    return cleaned

def build_safe_evidence(issue: schema.GitHubIssue, prs: list[schema.LinkedPR],
                        owner_repo: str) -> list[schema.OssEvidence]:
    """构造证据列表，只保留链接和元数据，不保留 issue/PR 原文。"""
    evidences = []
    for pr in prs:
        evidences.append(schema.OssEvidence(
            repo=owner_repo, issue=issue.number, pr=pr.number,
            commit=pr.commit_sha, url=issue.url,
            strength="high" if pr.merged else "medium",
        ))
    if not evidences:
        evidences.append(schema.OssEvidence(
            repo=owner_repo, issue=issue.number, url=issue.url, strength="low",
        ))
    return evidences
```

### 6.9 mine 命令端到端流程

```python
def cmd_mine(args) -> int:
    config = env.get_config()
    token = config["GITHUB_TOKEN"]
    repo = args.owner_repo

    log.info(f"Mining closed bug issues from {repo}...")

    # 1. 搜索 closed bug issues
    issues = github_search.search_closed_issues(
        repo, label=args.label, max_results=args.max_issues, token=token
    )
    log.info(f"Found {len(issues)} closed issues with label '{args.label}'")

    # 2. 过滤非 bug
    bug_issues = issue_filter.filter_issues(issues)
    log.info(f"After filter: {len(bug_issues)} likely-bug issues")

    # 3. 对每个 bug issue，找 linked PR + 抽取 candidate
    candidates = []
    issues_with_pr = 0
    language_hint = _guess_language_from_repo(repo, token)
    for issue in bug_issues:
        prs = evidence_linker.link_issue_to_prs(issue, repo, token)
        if prs:
            issues_with_pr += 1
        cand = pattern_extract.extract_candidate(issue, prs, repo, language_hint)
        if cand:
            candidates.append(cand)

    # 4. 落盘到 mining 目录（不自动入 packs/）
    result = schema.MiningResult(
        repo=repo, mined_at=datetime.now().isoformat(),
        issues_searched=len(issues), issues_kept=len(bug_issues),
        issues_with_pr=issues_with_pr, candidates=candidates,
        raw_dir=str(raw_dir), review_path=str(review_path),
    )
    mining_dir = store.save_mining(result.model_dump_json(indent=2),
                                   repo.replace("/", "_"))
    # 写候选 pattern 文件 + review.md
    _write_candidates(mining_dir, candidates)
    _write_review_md(mining_dir, result, candidates)

    log.info(f"Mining complete: {len(candidates)} candidates written to {mining_dir}")
    log.info(f"Review them at: {mining_dir / 'review.md'}")
    log.info(f"Approved candidates can be moved to packs/ after human review.")

    # 5. 输出
    rendered = render.render_mining(result, emit=args.emit)
    print(rendered)
    return 0
```

### 6.10 mining 输出结构

```
~/.issueoracle/mining/fastapi_fastapi_2026-06-16/
├── result.json                       # 完整 MiningResult
├── raw/
│   ├── issue-123.json                # 原始 issue 数据（已 sanitize）
│   └── pr-456.json                   # 原始 PR 数据
├── candidates/
│   ├── mined-fastapi-fastapi-123.candidate.yaml   # 候选 pattern
│   └── mined-fastapi-fastapi-456.candidate.yaml
└── review.md                         # 人工审阅用的 Markdown 摘要
```

`review.md` 格式：

```markdown
# Mining Report: fastapi/fastapi

Mined at: 2026-06-16
Issues searched: 50 | Kept (likely bug): 23 | With linked PR: 15
Candidates generated: 12

## Candidates

### 1. mined-fastapi-fastapi-123
- **Issue**: #123 Async session leak on exception path
- **PR**: #456 (merged)
- **Bug type**: resource_leak
- **Root cause**: Async session not closed in finally block
- **Bad signals**: `await`, `session`, `.all()`
- **Confidence**: 0.5 (candidate, needs review)
- **Evidence**: [fastapi/fastapi#123](url), [fastapi/fastapi#456](url)
- **False-positive boundary**: Auto-extracted from single issue. Verify trigger applies.

To approve: copy `candidates/mined-fastapi-fastapi-123.candidate.yaml` to
`packs/python/fastapi/patterns.yaml` (after merging/editing).
```

### 6.11 验收标准（Phase 2）

```bash
# 无 token 也能跑（小批量 + 低配额警告）
python3 scripts/issueoracle.py mine fastapi/fastapi --max-issues 10 --emit markdown
# → 输出 mining 报告，候选 pattern 落盘

# 有 token
GITHUB_TOKEN=xxx python3 scripts/issueoracle.py mine tiangolo/fastapi --max-issues 30 --emit json
# → 结构化 JSON

# 候选 pattern 能被 validate 加载
python3 scripts/issueoracle.py validate ~/.issueoracle/mining/fastapi_fastapi_2026-06-16/candidates
# → N candidates loaded, 0 errors

# rate limit 检查
python3 scripts/issueoracle.py diagnose
# → 输出 GitHub API 配额状态

python3 -m pytest tests/test_github_search.py tests/test_issue_filter.py \
    tests/test_evidence_linker.py tests/test_pattern_extract.py tests/test_safety.py -q
# → 全绿
```

---

## 7. Phase 3：Eval + 打磨

### 7.1 目标产物

| # | 文件 | 职责 |
|---|------|------|
| 1 | `evals/fixtures/` | 10 组 bad/good 代码 fixtures |
| 2 | `evals/golden/` | 每个 fixture 对应 expected.json |
| 3 | `evals/run_eval.py` | Eval runner CLI |
| 4 | `scripts/evaluate_patterns.py` | Pattern 质量评估 |
| 5 | `scripts/verify.py` | 验证 bundle（unit + smoke） |
| 6 | `references/pattern-schema.md` | Pattern schema 文档 |
| 7 | `references/review-report-format.md` | 报告格式文档 |
| 8 | `references/threat-model.md` | 威胁模型 |
| 9 | `nux-wizard.md` | 首次运行向导 |
| 10 | `tests/test_integration.py` | 端到端测试 |
| 11 | `README.md` 完善 | 安装 + 快速开始 |

### 7.2 Eval 设计

`evals/run_eval.py` CLI：
```bash
python3 evals/run_eval.py --fixtures evals/fixtures --golden evals/golden --emit json
```

测试类型：
1. **Positive fixture**: `bad/` 代码必须报出指定 pattern
2. **Negative fixture**: `good/` 代码不能报
3. **Schema fixture**: 所有 packs 通过 validate

指标：
- `precision_at_k`
- `false_positive_rate`（good fixtures 误报率）
- `evidence_coverage`（有 file/line 的 findings 比例）
- `line_evidence_coverage`

### 7.3 v0.1 最终发布门槛

- [ ] `npx skills add bzcsk2/issueoracle-skill -g` 或手动 symlink 可用
- [ ] `SKILL.md` 是运行时唯一真相源
- [ ] `diagnose` 可运行（含 GitHub 配额状态）
- [ ] `review .` 可输出 Markdown 和 JSON
- [ ] **`mine owner/repo` 可输出 candidate patterns 并落盘**（mining 核心）
- [ ] 内置 3-5 个 seed patterns
- [ ] 每个 finding 都有 file/line/confidence/pattern/trigger/false-positive-boundary
- [ ] 每个 candidate pattern 都有 OSS evidence link
- [ ] 默认 local-only（mining 的 LLM 抽取可选）
- [ ] 有 pack validate
- [ ] 有 eval fixtures（10 组 bad/good）
- [ ] 有 SECURITY.md（含 mining 安全规则）
- [ ] 有 CONTRIBUTING.md（含 pattern 合并标准）

---

## 8. 关键实现模式（从 last30days 学到并复用）

### 8.1 sys.path 注入模式
```python
# issueoracle.py 顶部
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))
from lib import schema, env, config, ...
```

### 8.2 conftest.py 路径模式
```python
# tests/conftest.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent
                        / "skills" / "issueoracle" / "scripts"))
```

### 8.3 unittest.TestCase + mock 模式
```python
class GithubSearchTests(unittest.TestCase):
    @mock.patch("lib.github_search._request")
    def test_search_closed_issues(self, mock_req):
        mock_req.return_value = {"items": [...]}
        issues = github_search.search_closed_issues("o/r", token="t")
        self.assertEqual(len(issues), 1)
```

### 8.4 stderr 日志 + stdout 输出分离
- 所有 `[issueoracle]` 日志写 stderr
- 仅最终报告写 stdout
- `ISSUEORACLE_DEBUG=1` 开启 debug 日志

### 8.5 Windows 兼容
```python
if os.name == "nt":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
```

### 8.6 GitHub API 测试不依赖网络
所有 `github_search._request` 在测试中 mock，绝不发真实网络请求。

### 8.7 CLAUDE.md 规则
- `lib/__init__.py` 必须是空包标记
- `npx skills add . -g -y` 安装测试
- Git remote: origin = public

---

## 9. 依赖清单

```toml
[project]
name = "issueoracle-skill"
version = "0.1.0"
description = "Mine bug patterns from GitHub issues and review local code with evidence."
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "pyyaml>=6.0",
]

[dependency-groups]
dev = [
    "pytest>=9.0.3,<10",
    "pytest-cov>=7,<8",
]
```

仅 2 个运行时依赖（pydantic + pyyaml）。GitHub API 用 stdlib `urllib`，无需额外 HTTP 库。

---

## 10. 实施顺序 checklist（给执行 Agent）

### Phase 0 — 骨架（1 天）

1. `pyproject.toml` ✅ + `uv sync`
2. `LICENSE` ✅
3. `CLAUDE.md` ✅ + `AGENTS.md` ✅
4. `SECURITY.md` ✅（补充 mining 安全规则）
5. `CHANGELOG.md` ✅
6. `CONTRIBUTING.md` ✅
7. `scripts/lib/__init__.py`（空）
8. `scripts/lib/log.py`
9. `scripts/lib/env.py`
10. `scripts/lib/config.py`
11. `scripts/lib/schema.py`（Pydantic 模型，含 Mining 层）
12. `scripts/lib/fs.py`
13. `scripts/lib/render.py`（基础 Markdown/JSON，含 mining render）
14. `scripts/store.py`
15. `scripts/issueoracle.py`（argparse CLI + diagnose + validate 骨架）
16. `SKILL.md`
17. `agents/default.yaml`
18. `scripts/build-skill.sh`
19. `scripts/verify.py`
20. `tests/conftest.py` + `tests/__init__.py`
21. `tests/test_schema.py`
22. `README.md`
23. **验收**：`issueoracle.py diagnose` 可运行

### Phase 1 — Review 基础管线（2-3 天）

24. `scripts/lib/git.py`
25. `scripts/lib/profile.py` + `tests/test_profile.py`
26. `scripts/lib/pack_loader.py` + `tests/test_pack_loader.py`
27. `scripts/lib/code_index.py` + `tests/test_code_index.py`
28. `scripts/lib/pattern_match.py` + `tests/test_pattern_match.py`
29. `scripts/lib/review.py` + `tests/test_review.py`
30. 5 个 seed patterns（3 Python + 2 TypeScript）+ examples
31. 完善 `issueoracle.py` review 命令
32. **验收**：review/validate 可用 + 5 patterns

### Phase 2 — ★ GitHub Mining（3-4 天）

33. `scripts/lib/github_search.py` + `tests/test_github_search.py`
34. `scripts/lib/github_fetch.py`
35. `scripts/lib/issue_filter.py` + `tests/test_issue_filter.py`
36. `scripts/lib/evidence_linker.py` + `tests/test_evidence_linker.py`
37. `scripts/lib/pattern_extract.py` + `tests/test_pattern_extract.py`
38. `scripts/lib/safety.py` + `tests/test_safety.py`
39. `references/mining-workflow.md`
40. 完善 `issueoracle.py` mine 命令 + diagnose 加 GitHub 配额
41. `tests/test_git.py` + `tests/test_store.py` + `tests/test_render.py`
42. **验收**：mine owner/repo 可用 + candidate 落盘 + 候选可被 validate

### Phase 3 — Eval + 打磨（2 天）

43. `evals/fixtures/`（10 组 bad/good）
44. `evals/golden/`（10 个 expected.json）
45. `evals/run_eval.py`
46. `scripts/evaluate_patterns.py`
47. `references/pattern-schema.md` + `review-report-format.md` + `threat-model.md`
48. `nux-wizard.md`
49. `tests/test_integration.py`
50. 完善 README.md + SKILL.md 边界 case
51. **验收**：v0.1 发布门槛全部满足

---

## 11. 文档变更说明

本计划相对原始 `issueoracle.md` 的主要变更：

1. **mining 前移**：原 v0.2 的 GitHub mining 提升为 v0.1 核心交付（§0、§3、§6）。
2. **schema 扩展**：新增 `MiningResult`、`CandidatePattern`、`GitHubIssue`、`LinkedPR` 模型（§4.4）。
3. **命令扩展**：v0.1 就实现 `mine` 命令，而非后置（§4.3、§6.9）。
4. **seed patterns 减少**：从 10 个减到 3-5 个（mining 产出补充，§5.6）。
5. **安全规则增强**：safety.py 专门处理 GitHub 内容的提示注入（§6.8）。
6. **Phase 重排**：Review 管线优先（Phase 1），mining 紧随（Phase 2），mining 依赖 review 的 schema/loader（§3）。
