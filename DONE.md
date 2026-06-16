# Done

## 完成内容

### Phase 0 — 骨架搭建
- `scripts/lib/__init__.py` — 空包标记
- `scripts/lib/log.py` — DEBUG 日志（stderr 输出，ISSUEORACLE_DEBUG 控制）
- `scripts/lib/env.py` — 环境变量 + TOML 配置加载（三层优先级）
- `scripts/lib/config.py` — Pydantic 配置模型
- `scripts/lib/schema.py` — 完整 Pydantic 数据模型（Pattern/CandidatePattern/MiningResult/ReviewReport 等）
- `scripts/lib/fs.py` — 文件系统工具（find_project_root/find_files/safe_read）
- `scripts/lib/render.py` — Markdown/JSON/compact 三种输出格式
- `scripts/store.py` — 文件系统存储（reports/cache/mining 落盘）
- `scripts/issueoracle.py` — 核心 CLI（review/mine/validate/diagnose 四个子命令）
- `SKILL.md` — 运行时唯一真相源（合约 + frontmatter + 命令规范）
- `agents/default.yaml` — Agent manifest
- `scripts/build-skill.sh` — .skill 打包脚本
- `scripts/verify.py` — Bundle 验证

### Phase 1 — Review 管线
- `scripts/lib/git.py` — Git diff/changed files 获取
- `scripts/lib/profile.py` — Repo 语言/框架/依赖/风险面识别
- `scripts/lib/pack_loader.py` — Pattern pack YAML 加载 + Pydantic 校验
- `scripts/lib/code_index.py` — 代码切块（Python ast / TypeScript 正则 / 滑动窗口 fallback）
- `scripts/lib/pattern_match.py` — 三段式匹配（metadata 召回 → signal 匹配 → trigger 判断）+ 评分
- `scripts/lib/review.py` — Finding 生成 + 硬规则过滤
- 5 个 seed patterns（3 Python FastAPI + 2 TypeScript Express）+ 各配 bad/good example
- 对应单元测试（test_git/test_profile/test_pack_loader/test_code_index/test_pattern_match/test_review）

### Phase 2 — GitHub Mining（v0.1 核心）
- `scripts/lib/github_search.py` — GitHub issue/PR REST API 搜索 + rate limit 检查
- `scripts/lib/github_fetch.py` — Issue timeline/PR/commit 内容获取
- `scripts/lib/issue_filter.py` — 排除非 bug issues（标签 + 标题启发式）
- `scripts/lib/evidence_linker.py` — issue → linked PR → commit 证据链
- `scripts/lib/pattern_extract.py` — 候选 pattern 抽取（root cause/signals/fix/triggers）
- `scripts/lib/safety.py` — GitHub 内容安全处理（提示注入防护、shell 代码块截断）
- `references/mining-workflow.md` — mining 流程文档
- 对应单元测试（test_github_search/test_issue_filter/test_evidence_linker/test_pattern_extract/test_safety）
- `test_store.py` / `test_render.py`

### Phase 3 — Eval + 打磨
- `evals/fixtures/` — 10 组 bad/good 代码 fixtures
- `evals/golden/` — 每个 fixture 对应 expected.json
- `evals/run_eval.py` — Eval runner CLI
- `scripts/evaluate_patterns.py` — Pattern 质量评估
- `references/pattern-schema.md` / `review-report-format.md` / `threat-model.md`
- `nux-wizard.md` — 首次运行向导
- `tests/test_integration.py` — 端到端集成测试
- README.md 完善

### Phase 4 — v0.2: scan/mine/review 三命令架构
- `schema.py` — 新增 `ProjectProfile`、`RepoCandidate`、`BugExperience`、`ExperienceReport` 4 个模型
- `profile.py` — 新增 `classify_project_type()`（web_api/cli/library/frontend）+ `infer_search_topics()`
- `github_search.py` — 新增 `search_similar_repos()` 仓库搜索（language + topic + stars 降序）
- `pattern_extract.py` — 增强 `_extract_signals()` 使用 issue 标题 + PR 标题关键词；新增 `_extract_signals_from_text()`
- `render.py` — 新增 `render_scan()`（项目画像 + 推荐清单）+ `render_bug_experience()`（叙事型经验文档）
- `store.py` — 新增 `bugplay/` 目录 + `save_experience()`
- `issueoracle.py` — 新增 `scan` 命令；`mine` 支持逗号分隔多仓库批量挖；`review` 支持 `--experience` 加载经验文档
- `lib/experience.py`（新建）— `aggregate()` 候选聚合、`to_markdown()` 叙事型 markdown 生成、`load_as_patterns()` 经验文档 → Pattern 反向解析
- `SKILL.md` — 更新为 v0.2.0，新增 `scan`/`REVIEW_WITH_EXPERIENCE` 命令，三命令流水线说明
- `evals/` — 新增 `py-missing-finally` 经验驱动 fixture；`run_eval.py` 支持自动加载 fixture 下 `experience.json`
- `github_fetch.py` — 新增 `_paginated_get()` 分页循环支持（上限 3 页 × 100 条）
- `tests/test_profile.py` — 新增 `ClassifyProjectTypeTests`（8 个测试）+ `InferSearchTopicsTests`（3 个测试）
- `tests/test_github_search.py` — 新增 `test_search_similar_repos` / `test_search_similar_repos_empty` mock 测试
- `profile.infer_search_topics()` — 修复：同时检查 `frameworks` + `dependencies`

## 验证数据
- 单元测试: **131 个全部通过**
- Eval 套件: **22/22 通过**
- Seed patterns: **7 个**（5 Python + 2 TypeScript）
- `diagnose`/`validate`/`review`/`mine`/`scan` 全部命令可用
- Python 3.14 / Windows 兼容
