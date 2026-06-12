---
title: code-review-graph：基于知识图谱的 AI 代码审查工具
date: 2026-06-13
author: tirth8205
tags: [MCP, code-review, tree-sitter, AI-tool, token-optimization]
source: https://github.com/tirth8205/code-review-graph
---

## 摘要

code-review-graph 是一个 AI 代码审查增强工具，通过构建代码知识图谱来优化 AI 助手的代码审查效率。它使用 Tree-sitter 解析代码结构，将仓库转化为包含函数、类、调用关系的图结构，并通过 MCP 协议为 AI 助手提供精确的上下文信息。该工具的核心价值在于大幅减少 AI 审查代码时的 token 消耗（中位数约 82 倍，最高可达 528 倍），同时提供爆炸半径分析、增量更新、社区检测等高级功能。支持 Python、JavaScript/TypeScript、Go、Rust 等 30+ 种语言，兼容 Claude Code、Cursor、Gemini CLI 等主流 AI 编程平台。

## 核心要点

- **知识图谱驱动**：使用 Tree-sitter 解析代码 AST，构建包含函数、类、调用关系的图结构，通过 MCP 协议为 AI 助手提供精确上下文
- **爆炸半径分析**：当文件变更时，自动追踪所有受影响的调用者、依赖者和测试，AI 只需读取相关文件而非扫描整个项目
- **大幅节省 Token**：中位数减少约 82 倍 token 消耗，最高可达 528 倍，显著降低 AI 代码审查成本
- **增量更新**：支持 watch 模式和 hook 集成，文件变更后自动增量更新图谱，2900+ 文件项目更新耗时 < 2 秒
- **广泛平台支持**：兼容 Claude Code、Cursor、Windsurf、Gemini CLI、GitHub Copilot 等 13+ 个 AI 编程平台
