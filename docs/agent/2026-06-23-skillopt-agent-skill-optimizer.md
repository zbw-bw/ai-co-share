---
title: SkillOpt：像训练神经网络一样训练 Agent Skills
date: 2026-06-23
author: microsoft
tags: [agent-skills, LLM, training, optimization, self-evolving, MCP]
source: https://github.com/microsoft/SkillOpt
---

## 摘要

SkillOpt 是微软推出的 Agent Skill 训练框架，它将 Agent Skill 视为可训练的文本状态，像训练神经网络一样（epoch、batchsize、learning rate、validation gate）对其进行系统化训练，而无需修改底层模型权重。通过 trajectory-driven 编辑、validation-gated 更新和 deployable best_skill.md 产物的完整训练循环，SkillOpt 在 6 个基准测试、7 个目标模型和 3 个执行框架上，全部 52 个（模型、基准、框架）评估单元格中达到最佳或并列最佳。在 GPT-5.5 上，分别将无 skill 基线准确率提升了 +23.5 分（直接对话）、+24.8 分（Codex agentic loop）、+19.1 分（Claude Code）。优化后的 skill 产物可跨模型规模、跨执行框架迁移，无需重新优化。

## 核心要点

- **文本空间优化**：将自然语言 Skill 文档视为可训练状态，通过 add/delete/replace 编辑更新，部署产物仅为 300-2000 token 的 best_skill.md
- **系统化训练循环**：完整的 roll-out → reflect → aggregate → select → update → evaluate 流程，包含 validation gate 和 rejected-edit buffer，确保每次迭代都有提升
- **跨模型、跨框架泛化**：支持 OpenAI / Claude / Qwen / MiniMax 等后端，skill 可在 Codex CLI 和 Claude Code CLI 之间迁移
- **零推理开销**：训练完成后，最佳 skill 直接在冻结模型上运行，无需增加任何推理时模型调用
- **丰富的生态系统**：已有 gbrain、darwin-skill 等项目集成，提供 WebUI 监控仪表盘和 SkillOpt-Sleep 夜间离线自进化模式
