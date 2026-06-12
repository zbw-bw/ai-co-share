---
title: ECC — 跨平台 AI 编程助手性能增强系统
date: 2026-06-12
author: unknown
tags: [claude-code, agent, skills, hooks, 效率工具, 跨平台]
source: https://github.com/affaan-m/ECC
---

## 摘要

ECC（Agent Harness Performance Optimization System）是一个历经 10 个月高强度实战打磨的生产级 AI 编程助手增强系统。它并非针对单一工具，而是横跨 Claude Code、Cursor、Codex、OpenCode、Gemini、Zed、GitHub Copilot 等多个主流 AI 编程平台，提供统一的能力扩展层。

系统核心包含 262 个专项 Skill（覆盖 TDD、安全扫描、并行化开发等工作流）、64 个专业子 Agent（规划师、架构师、安全审查员、代码审查员等）和 84 个向后兼容的命令垫片。通过钩子机制（PreToolUse、PostToolUse、SessionStart 等事件触发），实现自动化记忆持久化和跨会话学习。

内置 AgentShield 安全审计器包含 102 条静态分析规则，可在代码操作前拦截潜在风险。独创的"本能学习 v2"系统能够从使用模式中提取规律，并以置信度评分的方式沉淀为可复用的经验。项目以 MIT 协议永久开源，支持 TypeScript、Python、Go、Swift、Java、Kotlin、Rust 等 12 个以上语言生态。对于重度使用多种 AI 编程工具的开发者，ECC 提供了一套可以跨平台复用的统一操作系统。

## 核心要点

- 支持 Claude Code、Cursor、Codex、Gemini 等 7+ 平台，通过 `ECC_AGENT_DATA_HOME` 环境变量实现多平台隔离
- 262 个专项 Skill + 64 个子 Agent，覆盖从需求规划到安全审查的完整开发生命周期
- AgentShield 内置 102 条静态分析规则，在工具调用前进行安全拦截
- 基于钩子事件的记忆持久化机制，实现跨会话的上下文延续
- 本能学习系统（Instinct v2）自动提取使用模式并以置信度评分持久化为经验
