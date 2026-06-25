[English](README.md) | [中文](README.zh.md)

# DetectorOracle Skill

DetectorOracle 是一个 Agent Skill：它从 GitHub 已修复的 issue 中挖掘 bug 模式，再用具体的本地文件/行号证据审查代码。

DetectorOracle 不是通用 linter，也不是泛化的 AI review 工具。它的定位是一个 local-first 的 bug-pattern review 工具链，核心流程是 **scan → mine → review**。

## 改名状态

本仓库已从 IssueOracle 改名为 DetectorOracle。公开文档、安装命令、skill 名称和构建产物已经切换到 **DetectorOracle**。为了降低迁移风险，内部 Python 入口暂时仍保留为 `skills/detectoracle/scripts/issueoracle.py`。

## 安装

### 推荐：Agent Skills CLI

全局安装：

```bash
npx skills add bzcsk2/detectoracle-skill -g
```

项目级安装：

```bash
npx skills add bzcsk2/detectoracle-skill
```

更新：

```bash
npx skills update detectoracle
```

### Claude Code 市场

计划中。在 DetectorOracle 被收录进市场前，请使用 `npx skills add`。

### Claude Code 手动安装

```bash
git clone https://github.com/bzcsk2/detectoracle-skill.git
mkdir -p ~/.claude/skills
ln -s "$(pwd)/detectoracle-skill/skills/detectoracle" ~/.claude/skills/detectoracle
```

### Codex 手动安装

```bash
git clone https://github.com/bzcsk2/detectoracle-skill.git
mkdir -p ~/.codex/skills
ln -s "$(pwd)/detectoracle-skill/skills/detectoracle" ~/.codex/skills/detectoracle
```

### 构建本地 `.skill`

```bash
uv sync --all-groups
uv run python skills/detectoracle/scripts/build_skill.py
```

生成文件：

```text
dist/detectoracle.skill
```

## 快速开始

```bash
# 扫描项目 → 获取画像 + 同类 OSS 推荐
/detectoracle scan .

# 审查当前仓库
/detectoracle review .

# 从 GitHub 仓库挖掘 bug 模式（逗号分隔）
/detectoracle mine fastapi/fastapi,encode/starlette

# 使用生成的经验 JSON 审查
/detectoracle review . --experience ~/.detectoracle/bugplay/experience.json

# 校验模式包
/detectoracle validate packs
```

## 30 秒本地 demo

```bash
git clone https://github.com/bzcsk2/detectoracle-skill
cd detectoracle-skill
uv sync --all-groups
uv run python skills/detectoracle/scripts/issueoracle.py review skills/detectoracle/evals/fixtures/py-fastapi-cors-wildcard/bad --emit markdown
```

预期输出会包含：

```text
- 本地文件/行号证据
- 匹配的 pattern id
- 置信度
- 触发条件
- 修复建议
- 误报边界
```

## 流水线

```text
scan ./my-project                     → 项目画像 + 推荐仓库
mine owner1/repo1,owner2/repo2,...    → ~/.detectoracle/bugplay/experience.json + bug-experience.md
review ./my-project --experience ...  → 由内置模式 + 挖掘经验驱动的审查结果
```

## 用法

### 扫描项目

```bash
/detectoracle scan . --emit markdown
/detectoracle scan src/ --emit json --max-repos 3
```

输出包括：语言/框架检测、风险面分析、项目类型分类（`web_api` / `cli` / `library` / `frontend`），以及按 star 数排序的同类开源项目。

### 审查本地代码

```bash
# 全量审查
/detectoracle review .

# Diff 审查（仅变更文件）
/detectoracle review . --changed --base main

# JSON 输出
/detectoracle review src/ --emit json

# 经验驱动审查，优先使用 JSON 作为机器可读契约
/detectoracle review . --experience ~/.detectoracle/bugplay/experience.json
```

DetectorOracle 只有在同时具备匹配的 bug pattern、具体本地文件/行号证据、触发条件、置信度和误报边界时，才会报告 finding。

### 从 GitHub 挖掘 bug 模式

```bash
# 单个仓库
/detectoracle mine fastapi/fastapi

# 批量挖掘
/detectoracle mine fastapi/fastapi,encode/starlette,sqlalchemy/sqlalchemy --max-issues 30
```

挖掘结果会保存到 `~/.detectoracle/bugplay/experience.json`，供 review engine 使用；同时保存叙事型文档 `~/.detectoracle/bugplay/bug-experience.md`。

恢复被中断的挖掘任务：

```bash
/detectoracle mine fastapi/fastapi,encode/starlette --resume --max-issues 30
```

### 管理 bug 经验

```bash
# 列出所有 bug 经验（candidate + approved + rejected）
/detectoracle experience list

# 查看某条经验详情
/detectoracle experience show exp-missing-finally-1

# 批准候选经验进入 review
/detectoracle experience approve exp-missing-finally-1

# 拒绝误报经验
/detectoracle experience reject exp-missing-finally-1

# 导出已批准经验
/detectoracle experience export-approved
```

### 校验模式包

```bash
/detectoracle validate packs
/detectoracle validate packs --emit json
```

### 诊断

```bash
/detectoracle diagnose
```

### Doctor

```bash
/detectoracle doctor
```

## 开发

```bash
uv sync --all-groups
uv run ruff format --check .
uv run ruff check .
uv run pytest tests/ -q
uv run python skills/detectoracle/scripts/issueoracle.py diagnose
uv run python skills/detectoracle/evals/run_eval.py
uv run python skills/detectoracle/scripts/issueoracle.py validate skills/detectoracle/packs
uv run python skills/detectoracle/scripts/build_skill.py
```

## 工作原理

1. **Scan**：对本地项目画像，分类项目类型，推断 GitHub 搜索关键词，推荐同类开源项目。
2. **Mine**：批量搜索 GitHub 已关闭的 bug issue，过滤真实 bug，链接到修复 PR，提取候选 bug 模式，聚合成 bug 经验报告。
3. **Review**：加载内置种子模式 + 可选经验 JSON，索引本地代码，匹配信号，生成带证据的发现报告。

## 安全模型

- 本地代码默认留在本地。
- GitHub issue 和 PR 文本都按不可信输入处理。
- DetectorOracle 不会自动修复代码、创建提交或打开 PR。
- Pattern pack 只存储结构化证据链接和摘要，不保存大段源码。
- 只有显式设置 `DETECTORACLE_ALLOW_REMOTE_LLM=1` 后，才允许使用远程 LLM。

## 要求

- Python 3.12+
- `GITHUB_TOKEN` 可选，用于提高 GitHub API 频率限制

## 许可证

MIT
