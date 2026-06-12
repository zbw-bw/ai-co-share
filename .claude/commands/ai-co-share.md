---
description: 抓取 URL 内容，自动总结并提交到 ai-co-share 仓库
argument-hint: <URL> [分类: llm/agent/tools/papers]
---

你是 ai-co-share 仓库的内容提交助手。用户提供了一个 URL（以及可选的分类）：

**输入：** $ARGUMENTS

**执行步骤（严格按顺序）：**

1. **解析参数**
   - 提取 URL（第一个参数）
   - 提取分类（第二个参数，可选：llm/agent/tools/papers）

2. **读取 CLAUDE.md 获取完整接口契约**
   - 路径：`CLAUDE.md`（仓库根目录）
   - 按照 CLAUDE.md 中定义的六步流程执行

3. **抓取 URL 内容**
   - 使用 WebFetch 工具读取 URL
   - 根据 URL 类型选择对应抓取策略（见 CLAUDE.md 第一步）

4. **生成内容**
   - 按 CLAUDE.md 第二步生成标题、摘要、要点

5. **确定分类**
   - 用户已指定则直接使用
   - 未指定则按 CLAUDE.md 第三步的规则自动判断

6. **写入文件**
   - 按 CLAUDE.md 第四步的模板和命名规范创建文件

7. **更新周索引**
   - 按 CLAUDE.md 第五步更新或创建对应 weekly 文件

8. **提交并推送**
   - 按 CLAUDE.md 第六步执行 git add/commit/push

**完成后输出：**

✅ 已提交：<标题>
📁 文件：docs/<分类>/<文件名>.md
📅 周索引：docs/weekly/<周文件>.md
