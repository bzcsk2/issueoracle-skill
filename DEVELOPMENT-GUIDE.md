# IssueOracle v0.2 改造计划：scan / mine / review 三命令架构

> 本文档是 `PLAN2.md` 的整理版，作为 IssueOracle 后续开发（v0.2）的正式指导。
> 整理原则：合并原文两版内容（详细版 + 精简迭代版），统一术语，修正代码块/表格格式，去重，不增删技术决策。

---

## 目录

1. [决策摘要](#一决策摘要)
2. [三命令总体流程](#二三命令总体流程)
3. [现有代码复用评估](#三现有代码复用评估)
4. [命令详细设计](#四命令详细设计)
5. [实施步骤（按依赖顺序）](#五实施步骤按依赖顺序)
6. [关键实现细节](#六关键实现细节)
7. [不改动的部分（明确边界）](#七不改动的部分明确边界)
8. [验收标准](#八验收标准)
9. [产出文档](#九产出文档)

---

## 一、决策摘要

| 决策点 | 选择 |
|---|---|
| 改造方式 | 基于现有项目改造，**不推倒重来** |
| 命令架构 | `scan`（画像 + 发现）/ `mine`（批量挖 issue + 出经验文档）/ `review`（回扫本地代码） |
| scan 职责 | 仅画像 + 推荐 5 个相似成功项目，**不做端到端** |
| 相似项目发现 | GitHub `/search/repositories` + topic + 语言 + stars 降序 |
| mine 批量化 | 支持多个 `owner/repo`（逗号分隔） |
| bug 经验文档 | 叙事型 markdown（按 bug 类别组织，人类 + agent 可读） |

---

## 二、三命令总体流程

```text
① scan：扫描我的项目
   issueoracle.py scan ./my-project
   → 项目画像（语言 / 框架 / 功能 / 风险面）
   → 推荐 5 个同类型成功项目（GitHub topic + stars）
   → 输出 scan-report.md + 推荐项目清单

② mine：批量挖取 bug 经验
   issueoracle.py mine owner1/repo1,owner2/repo2,...   # 可从 scan 结果复制
   → 对每个项目：搜 closed bug issues → 过滤 → 找 linked PR → 抽取 bug 经验
   → 汇总成一份「叙事型 bug 经验 markdown」
   → 落盘 ~/.issueoracle/bugplay/bug-experience.md

③ review：回扫本地代码
   issueoracle.py review ./my-project --experience ~/.issueoracle/bugplay/bug-experience.md
   → agent 读取 bug 经验文档 → 提取 bad_code_signals → 匹配本地代码
   → 输出带 file/line/confidence/evidence 的 finding 报告
```

三步串成一条流水线：**scan 产出推荐项目 → mine 把推荐项目变成经验文档 → review 用经验文档回扫本地代码**。

---

## 三、现有代码复用评估

### ✅ 直接复用（不改）

| 模块 | 复用点 |
|---|---|
| `code_index.py` | Python AST / TS 正则 / fallback 切块，完整可用 |
| `pattern_match.py` | 三段式匹配 + 评分公式，完整可用 |
| `review.py` | `build_findings` 硬规则过滤，完整可用 |
| `issue_filter.py` | bug issue 过滤逻辑，完整可用 |
| `evidence_linker.py` | issue → PR 证据链，完整可用 |
| `git.py` | changed files / diff，完整可用 |
| `safety.py` | GitHub 内容安全处理，完整可用（小幅增强） |
| `pack_loader.py` | 内置 seed patterns 加载，完整可用 |
| `store.py` | 文件系统存储，完整可用（加新目录） |

### 🔧 需扩展（小改）

| 模块 | 改动 |
|---|---|
| `profile.py` | 新增项目类型分类（web/api/cli/library）+ 丰富框架检测。现有只检测语言/框架，没有「功能类型」——而 scan 要靠它推断 GitHub topic |
| `github_search.py` | 新增 `search_similar_repos()`（调用 `/search/repositories`）。现有只有 issue 搜索，完全没有仓库搜索 |
| `github_fetch.py` | 加分页支持（现有硬上限 100 条） |
| `pattern_extract.py` | 增强 signals 抽取（不再只依赖 issue body 代码块，加 issue 标题 + PR diff 关键词） |
| `render.py` | 新增 `render_scan()`（项目画像 + 推荐清单）和 `render_bug_experience()`（叙事型经验文档） |
| `schema.py` | 新增 `ProjectProfile`（带 type/domain/recommended_topics）、`RepoCandidate`、`BugExperience`、`ExperienceReport` 模型 |
| `issueoracle.py` | 新增 `cmd_scan`，改造 `cmd_mine`（批量化 + 叙事文档），改造 `cmd_review`（支持 `--experience` 加载经验文档作为 patterns） |

### ❌ 新建

| 模块 | 用途 |
|---|---|
| `experience.py` | bug 经验文档的读写：从 candidate patterns 聚合成叙事 markdown，并能从 markdown/json 反向解析出 `bad_code_signals` 供 review 使用 |

---

## 四、命令详细设计

### 命令 1：scan —— 项目画像 + 相似项目发现

**CLI：**

```bash
issueoracle.py scan <repo_path> [--emit markdown|json] [--max-repos 5] [--save-dir] [--debug]
```

**流程：**

```text
1. profile_repo() 现有逻辑 → 语言 / 框架 / 依赖 / 风险面
2. 新增 classify_project_type() → web_api / cli / frontend / library
   - 推断规则：有 fastapi/flask/django/express/next 路由 → web_api
              有 click/typer/commander/yargs → cli
              无入口框架 + 主要是 lib 结构 → library
3. 新增 infer_search_topics() → GitHub topic 关键词
   - 例：Python+FastAPI+web → ["fastapi", "web-framework"]
        TypeScript+Express+api → ["express", "rest-api"]
4. github_search.search_similar_repos(language, topics, max=5)
   - 调 /search/repositories?q=language:Python topic:fastapi sort:stars
   - 过滤掉用户自己的项目、archived、<100 stars
   - 返回 RepoCandidate 列表（owner/repo, stars, description, topics）
5. 输出 scan-report.md（画像 + 推荐项目清单）
```

**输出 `scan-report.md`：**

````markdown
# IssueOracle Scan Report: my-project

## Project Profile
- **Languages**: Python
- **Frameworks**: FastAPI, SQLAlchemy
- **Project type**: web api
- **Risk surfaces**: web, database, auth
- **Dependencies**: fastapi, sqlalchemy, uvicorn, pydantic

## Recommended Similar Projects (5)
Based on language=Python, topics=[fastapi, web-framework], sorted by stars:

| # | Repo | Stars | Description |
|---|------|-------|-------------|
| 1 | [tiangolo/fastapi](url) | 75k | Modern Fast web framework... |
| 2 | [encode/starlette](url) | 10k | ... |
| ... |

## Next Step
Run mining on these projects to extract bug experience:
issueoracle.py mine tiangolo/fastapi,encode/starlette,...
````

---

### 命令 2：mine —— 批量挖取 + 叙事型 bug 经验文档

**CLI：**

```bash
issueoracle.py mine <owner/repo,...> [--max-issues 30] [--emit markdown|json] [--save-dir] [--debug]
# 支持逗号分隔多个仓库
```

**流程（每个仓库循环）：**

```text
1. github_search.search_closed_issues(repo) → issues
2. issue_filter.filter_issues(issues) → bug_issues
3. 对每个 bug_issue:
   - evidence_linker.link_issue_to_prs() → prs
   - pattern_extract.extract_candidate() → candidate（增强版）
4. 汇总所有仓库的所有 candidates
5. experience.aggregate() → 按 bug_type 分组的叙事 markdown
6. 落盘 ~/.issueoracle/bugplay/bug-experience.md + experience.json
```

**关键产出：叙事型 bug 经验文档（`render_bug_experience`）**

每个 bug 经验包含**六要素**：症状 → 根因 → 触发条件 → 坏代码信号 → 修复方式 → 证据链接。
agent 读完后知道「什么场景警惕什么 bug」；review 时直接用这些 `bad_code_signals` 去匹配本地代码。

````markdown
# Bug Experience Report
Mined from: tiangolo/fastapi, encode/starlette
Date: 2026-06-16
Total issues analyzed: 45 | Bug issues: 23 | With fix PR: 15

## 🧹 Resource Leaks (4 bugs)

### Async session leak on exception path
- **Symptom**: connection pool exhaustion under concurrent requests
- **Root cause**: Async SQLAlchemy session not closed when exception raised before commit
- **Trigger condition**: async request handler + DB session + exception path
- **Bad code signals**: `await`, `session`, missing `async with` / `finally`
- **Fix**: use request-scoped dependency + `async with` context manager
- **Evidence**: [fastapi/fastapi#123](url), fixed by [PR #456](url)

### ... (more)

## 🔐 Security / Auth (3 bugs)
...

## 💥 Error Handling (2 bugs)
...
````

按 bug 类别（资源泄漏 / 安全 / 错误处理…）组织。

---

### 命令 3：review —— 用 bug 经验回扫本地代码

**CLI（新增 `--experience` 参数）：**

```bash
issueoracle.py review <repo_path> [--experience <path>] [--changed] [--base main] [--emit markdown|json] [--debug]
```

**关键改动：** review 现在能从**两个来源**加载 patterns：

1. 内置 `packs/` 的 seed patterns（现状）
2. `--experience` 指向的 bug 经验文档（新增）

**`--experience` 加载逻辑（新增 `experience.load_as_patterns()`）：**

```text
1. 读取 bug-experience.md（或 experience.json）
2. 把每个 bug 经验转成 Pattern 对象：
   - id, language, frameworks 从经验文档元数据来
   - bad_code_signals 直接用经验里的（已增强）
   - trigger_conditions 用经验里的
   - confidence 用经验里的（candidate 默认 0.5）
   - evidence 用经验里的 OSS 链接
3. 与内置 packs 合并 → 统一 pattern 集合
4. 走现有 pattern_match.match() + review.build_findings() 管线
```

**不改匹配引擎**，只是多了一个 pattern 来源。经验文档里的 bug 模式能直接驱动现有三段式匹配。

---

## 五、实施步骤（按依赖顺序）

### Step 1 — schema 扩展（基础）

- `schema.py` 新增：`ProjectProfile`（含 type/domain/recommended_topics）、`RepoCandidate`（owner/repo, stars, description, topics, url）、`BugExperience`（单个 bug 经验六要素）、`ExperienceReport`（汇总）
- 新增测试 `test_schema.py` 补充

### Step 2 — scan 命令核心

- `profile.py` 新增 `classify_project_type()` + `infer_search_topics()`
- `github_search.py` 新增 `search_similar_repos(language, topics, token, max)`，调 `/search/repositories`
- `render.py` 新增 `render_scan()`
- `issueoracle.py` 新增 `cmd_scan()` + 注册到 argparse + main dispatch
- 新增测试 `test_profile.py`（类型分类）、`test_github_search.py`（仓库搜索 mock）

### Step 3 — mine 批量化 + 经验文档

- `issueoracle.py` 改造 `cmd_mine()`：解析逗号分隔、循环每个仓库
- `pattern_extract.py` 增强 `_extract_signals()`：加 issue 标题 + PR 标题关键词（不只依赖 body 代码块）
- 新建 `experience.py`：`aggregate(candidates) → ExperienceReport`、`to_markdown(report) → str`
- `render.py` 新增 `render_bug_experience()`
- `store.py` 加 `bugplay/` 目录
- 新增测试 `test_experience.py`、增强 `test_pattern_extract.py`

### Step 4 — review 支持 `--experience`

- 新建 `experience.load_as_patterns(path) → list[Pattern]`（从经验 markdown/json 反向解析）
- `issueoracle.py` 改造 `cmd_review()`：读取 `--experience`，与 packs 合并
- 新增测试 `test_experience.py`（`load_as_patterns` round-trip）

### Step 5 — 收尾

- `SKILL.md` 更新命令文档（scan/mine/review 三命令流程）
- `evals/` 补充：经验文档驱动的 review 测试
- `README.md` 更新三命令使用说明
- 跑全量测试确保不回归

---

## 六、关键实现细节

### 1. GitHub 仓库搜索 API（`search_similar_repos`）

```python
def search_similar_repos(language: str, topics: list[str], *,
                         token: str | None = None, max_results: int = 5) -> list[schema.RepoCandidate]:
    # 构造 query: language:Python topic:fastapi topic:web-framework stars:>100
    q_parts = [f"language:{language}"]
    q_parts += [f"topic:{t}" for t in topics[:3]]
    q_parts.append("stars:>100")
    q = " ".join(q_parts)
    data = _request("/search/repositories", token, {
        "q": q, "sort": "stars", "order": "desc", "per_page": max_results
    })
    candidates = []
    for item in data.get("items", [])[:max_results]:
        candidates.append(schema.RepoCandidate(
            owner_repo=item["full_name"],
            stars=item["stargazers_count"],
            description=item.get("description", ""),
            url=item["html_url"],
            topics=item.get("topics", []),
        ))
    return candidates
```

### 2. 项目类型分类（`classify_project_type`）

返回值统一为：`web_api` / `cli` / `frontend` / `library`。

```python
def classify_project_type(profile: RepoProfile) -> str:
    fw = {f.lower() for f in profile.frameworks}
    deps = {d.lower() for d in profile.dependencies}
    all_kw = fw | deps
    if any(k in all_kw for k in ("fastapi", "flask", "django", "express", "next", "koa", "starlette")):
        return "web_api"
    if any(k in all_kw for k in ("click", "typer", "commander", "yargs", "cobra", "clap")):
        return "cli"
    if any(k in all_kw for k in ("react", "vue", "angular", "svelte")) and \
       not any(k in all_kw for k in ("express", "fastapi")):
        return "frontend"
    if profile.risk_surfaces and "web" in profile.risk_surfaces:
        return "web_api"
    return "library"
```

### 3. 经验文档 ↔ Pattern 双向转换

| 方向 | 函数 | 说明 |
|---|---|---|
| mine → 文档 | `experience.to_markdown(ExperienceReport)` | 生成叙事 md |
| review ← 文档 | `experience.load_as_patterns(path)` | 解析 md/json 回 Pattern 列表 |

为保证可靠解析，**同时落盘一份 `experience.json`（结构化）**：

- `bug-experience.md`：叙事型，给人 / agent 读
- `experience.json`：结构化，给 review 引擎用

review **优先读 json** 保证解析可靠。

---

## 七、不改动的部分（明确边界）

- 现有 **7 个 seed patterns** 保留
- 现有 `validate` / `diagnose` 命令保留
- 现有 eval fixtures 保留（可能补充经验驱动测试）
- **三段式匹配引擎**（metadata → signal → trigger）不动
- **评分公式**不动
- Pydantic + PyYAML + urllib 依赖不动
- 现有 **89 个测试不能回归**

---

## 八、验收标准

```bash
# scan：输出项目画像 + 5 个推荐项目
issueoracle.py scan ./my-project --emit markdown

# mine：批量挖 + 出叙事经验文档
issueoracle.py mine owner1/repo1,owner2/repo2 --max-issues 20 --emit markdown
# → 生成 ~/.issueoracle/bugplay/bug-experience.md（叙事型）

# review：用经验文档回扫
issueoracle.py review ./my-project --experience ~/.issueoracle/bugplay/bug-experience.md --emit markdown
# → finding 报告，含 file/line/confidence/evidence

# 端到端三步走通
issueoracle.py scan . → 得到推荐项目
issueoracle.py mine <推荐项目列表> → 得到经验文档
issueoracle.py review . --experience <经验文档> → 得到 finding

# 测试不回归
python -m pytest tests/ -q   # 全绿
```

---

## 九、产出文档

本计划确定后，同步更新 `IMPLEMENTATION_PLAN.md`，把三命令架构作为 **v0.2 的正式方案**。
