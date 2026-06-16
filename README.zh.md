[English](README.md) | [中文](README.zh.md)

# IssueOracle Skill

从 GitHub 已修复的 issue 中挖掘 bug 模式，再用具体证据审查本地代码。

## 安装

### 推荐：Agent Skills CLI

全局安装：

```bash
npx skills add bzcsk2/issueoracle-skill -g
```

项目级安装：

```bash
npx skills add bzcsk2/issueoracle-skill
```

更新：

```bash
npx skills update issueoracle
```

### Claude Code 市场

计划中。在 IssueOracle 被收录进市场前，请使用 `npx skills add`。

### Claude Code 手动安装

```bash
git clone https://github.com/bzcsk2/issueoracle-skill.git
mkdir -p ~/.claude/skills
ln -s "$(pwd)/issueoracle-skill/skills/issueoracle" ~/.claude/skills/issueoracle
```

### Codex 手动安装

```bash
git clone https://github.com/bzcsk2/issueoracle-skill.git
mkdir -p ~/.codex/skills
ln -s "$(pwd)/issueoracle-skill/skills/issueoracle" ~/.codex/skills/issueoracle
```

### 构建本地 .skill

```bash
uv sync --all-groups
uv run python skills/issueoracle/scripts/build_skill.py
```

生成文件：`dist/issueoracle.skill`

## 快速开始

```bash
# 扫描项目 → 获取画像 + 同类 OSS 推荐
/issueoracle scan .

# 审查当前仓库
/issueoracle review .

# 用 bug 经验文档审查
/issueoracle review . --experience ~/.issueoracle/bugplay/bug-experience.md

# 从 GitHub 仓库挖掘 bug 模式（逗号分隔）
/issueoracle mine fastapi/fastapi,encode/starlette

# 校验模式包
/issueoracle validate packs
```

## 流水线

```text
scan ./my-project                     → 项目画像 + 5 个推荐仓库
mine owner1/repo1,owner2/repo2,...    → ~/.issueoracle/bugplay/bug-experience.md
review ./my-project --experience ...  → 由挖掘经验驱动的审查结果
```

## 用法

### 扫描项目

```bash
/issueoracle scan . --emit markdown
/issueoracle scan src/ --emit json --max-repos 3
```

输出包括：语言/框架检测、风险面分析、项目类型分类（`web_api` / `cli` / `library` / `frontend`），以及按 star 数排序的 5 个同类开源项目。

### 审查本地代码

```bash
# 全量审查
/issueoracle review .
# Diff 审查（仅变更文件）
/issueoracle review . --changed --base main
# JSON 输出
/issueoracle review src/ --emit json
# 经验驱动审查
/issueoracle review . --experience ~/.issueoracle/bugplay/bug-experience.md
```

### 从 GitHub 挖掘 bug 模式

```bash
# 单个仓库
/issueoracle mine fastapi/fastapi
# 批量挖掘
/issueoracle mine fastapi/fastapi,encode/starlette,sqlalchemy/sqlalchemy --max-issues 30
```

挖掘结果保存到 `~/.issueoracle/bugplay/bug-experience.md`。

### 校验模式包

```bash
/issueoracle validate packs
/issueoracle validate packs --emit json
```

### 诊断

```bash
/issueoracle diagnose
```

### Doctor

```bash
/issueoracle doctor
```

## 工作原理

1. **Scan**：对本地项目画像，分类项目类型，推断 GitHub 搜索关键词，推荐 5 个同类开源项目。
2. **Mine**：批量搜索 GitHub 已关闭的 bug issue，过滤真实 bug，链接到修复 PR，提取候选 bug 模式，聚合成叙事型 bug 经验文档。
3. **Review**：加载种子模式 + 可选经验文档，索引本地代码，匹配信号，生成带证据的发现报告。

## 开发

```bash
uv sync
uv run pytest tests/ -q
uv run python skills/issueoracle/scripts/issueoracle.py diagnose
uv run python skills/issueoracle/evals/run_eval.py
```

## 要求

- Python 3.12+
- `GITHUB_TOKEN`（可选，用于更高 API 频率限制）

## 许可证

MIT
