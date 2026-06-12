---
title: SkVM：面向 Agent Skills 的语言虚拟机
date: 2026-06-12
author: SJTU-IPADS
tags: [agent, skills, 虚拟机, 编译器, LLM]
source: https://github.com/SJTU-IPADS/SkVM
---

## 摘要

SkVM（Skill Virtual Machine）是上海交通大学 IPADS 实验室开发的编译与运行时系统，旨在解决 LLM Agent Skills 在不同模型和运行环境之间的移植性问题。该系统通过 Profiling（能力画像）、AOT 编译（提前编译）、JIT 优化（即时优化）和 Benchmark（基准测试）四个核心模块，实现 Skills 的跨模型、跨平台复用。

SkVM 的工作流程是：首先对目标模型进行能力画像，识别其基础原语能力；然后通过 AOT 编译器将 Skills 编译为与模型无关的中间表示；接着利用 JIT 技术进行运行时优化和自动调优；最后通过基准测试评估优化效果。项目配套了包含 108 个 Skills、216 个任务的标准化数据集，为社区提供了可复现的评估基准。

## 核心要点

- **能力画像**：通过 Profiling 评估模型+harness 的基础原语能力，建立能力基线
- **AOT 编译**：多趟提前编译器将 Skills 编译为可移植的中间表示
- **JIT 优化**：运行时加速（JIT-boost）和内容优化（JIT-optimize）双重优化
- **标准化评测**：配套 108 个 Skills、216 个任务的基准数据集，支持跨模型对比
- **开源生态**：MIT 许可，支持 npm/curl 安装，已有 500+ stars
