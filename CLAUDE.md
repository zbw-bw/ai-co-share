# AI Co-Share — Agent 上传接口契约

本文档定义了 AI agent 向该仓库提交内容的标准流程。任何 agent 读完本文件即可独立完成提交，无需额外工具。

---

## 触发方式

用户提供一个 URL，agent 执行完整的抓取 → 总结 → 写文件 → 提交流程。

---

## 第一步：识别 URL 类型并抓取内容

| URL 特征 | 类型 | 抓取策略 |
|----------|------|----------|
| `github.com/<user>/<repo>` | GitHub 仓库 | 读取 README.md 全文 + 仓库描述 + stars |
| `arxiv.org/abs/<id>` | arXiv 论文 | 读取标题、作者、摘要（Abstract）|
| `youtube.com/watch` 或 `youtu.be` | YouTube 视频 | 读取页面标题、描述、字幕（如有）|
| `bilibili.com/video` | B站视频 | 读取标题、UP主、简介 |
| 其他 URL | 网站文章 | 提取页面正文，去除导航/广告 |

---

## 第二步：生成内容

生成以下内容：
1. **标题**：简洁中文标题（10-20 字）
2. **摘要**：200-400 字，概括核心内容和价值
3. **核心要点**：3-5 条 bullet，每条一句话
4. **原始链接**：保留来源 URL

---

## 第三步：确定分类

用户未指定分类时，按以下规则判断：

| 分类 | 关键词 |
|------|--------|
| `llm` | 大模型、微调、RAG、提示工程、GPT、Claude、Gemini、LLM |
| `agent` | Agent、工作流、Multi-Agent、Tool Use、MCP、Agentic |
| `tools` | Claude Code、Skills、Hooks、自定义命令、插件、IDE、效率工具 |
| `papers` | 论文、arXiv、研究、实验、paper |

---

## 第四步：写入文件

**文件路径：** `docs/<分类>/YYYY-MM-DD-<slug>.md`

- `YYYY-MM-DD`：今天的日期
- `<slug>`：标题的英文小写 + 连字符，如 `claude-code-mcp-guide`

**文件内容模板：**

```markdown
---
title: <标题>
date: <YYYY-MM-DD>
author: <用户名，如未知填 unknown>
tags: [<相关标签>]
source: <原始 URL>
---

## 摘要

<200-400 字摘要>

## 核心要点

- <要点 1>
- <要点 2>
- <要点 3>
```

---

## 第五步：更新周索引

计算当前是第几周（ISO week number）。

**文件路径：** `docs/weekly/YYYY-Wxx.md`（如 `docs/weekly/2026-W24.md`）

若文件不存在，创建：

```markdown
# YYYY Wxx（<周一日期> ~ <周日日期>）

```

在文件末尾追加一行：

```
- [<标题>](../<分类>/<文件名>.md) — <一句话摘要> @<作者>
```

---

## 第六步：提交并推送

```bash
git add docs/<分类>/<文件名>.md docs/weekly/<周索引文件>.md
git commit -m "share: <标题>"
git push
```

---

## Commit Message 规范

| 前缀 | 用途 |
|------|------|
| `share:` | 新增分享内容 |
| `fix:` | 修正错误 |
| `config:` | 配置变更 |
