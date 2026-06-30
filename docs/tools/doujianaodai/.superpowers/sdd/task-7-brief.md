### Task 7: README — Comprehensive Documentation

**Files:**
- Modify: `README.md` (full rewrite)

**Interfaces:**
- Consumes: nothing (documentation only)
- Produces: Complete README.md

- [ ] **Step 1: Write README.md**

```markdown
# 逗叽脑袋 (doujianaodai)

> 桌面宠物 Agent — 被动监控屏幕活动，记录你的学习与工作，随时对话回顾你的一天。

## ✨ 功能特性

### 🖥️ 被动屏幕监控
- 15 秒间隔截取前台窗口（macOS Quartz API）
- PaddleOCR 本地文字识别，无需联网
- 四状态行为状态机（IDLE → OBSERVING → ENGAGED → 生成摘要）
- 仅记录深度活动（≥75 秒停留），自动过滤快速浏览

### 🧠 智能活动记忆
- 本地 Ollama 小模型生成内容摘要（支持用户选择已安装模型）
- 三层记忆架构：活动记录 → 每日总结 → 周/月总结
- 全部以 Markdown 文件存储，无数据库依赖
- 三层读取策略：索引 → 详情 → OCR 原文（按需加载）

### 💬 AI 对话（流式输出）
- 通过 Claude Code CLI 桥接对话
- MCP Server 提供记忆读取工具
- 实时流式输出：思考过程、工具调用、回复文本
- 支持问"今天做了什么"、"这周学了什么"

### 📊 日志与统计
- 监控操作日志（状态转换、截图、摘要生成）
- 对话日志（消息、耗时、模型）
- 每日效果统计（专注度、活动时长）

## 📦 安装

### 前置条件

| 依赖 | 版本 | 说明 |
|------|------|------|
| macOS | 12+ | 依赖 Quartz、AppKit |
| Python | 3.11+ | 使用 match/case 等新语法 |
| Ollama | latest | 本地 LLM 推理引擎 |
| Claude Code | latest | AI 对话引擎 |

### 1. 安装 Ollama

```bash
brew install ollama
ollama serve              # 启动服务
ollama pull qwen3:8b      # 下载推荐模型（或其他模型）
```

### 2. 安装 Claude Code

```bash
npm install -g @anthropic-ai/claude-code
claude login              # 首次登录
```

### 3. 安装逗叽脑袋

```bash
pip install doujianaodai
```

或从源码安装：

```bash
git clone https://github.com/your-username/doujianaodai.git
cd doujianaodai
pip install -e ".[dev]"
```

## 🚀 快速开始

```bash
doujianaodai
```

首次运行会进行环境检查：

```
🔍 环境检查中...
[✓] Python 3.11.9
[✓] Ollama 运行中
    可用模型: qwen3:8b, llama3:8b, gemma2:9b
    ? 请选择用于活动摘要的模型 [qwen3:8b]:
[✓] 模型已配置: qwen3:8b
[✓] Claude Code v1.0.28
[✓] 屏幕录制权限正常
✅ 启动逗叽脑袋...
```

启动后：
1. 菜单栏出现 🧠 图标
2. 点击图标打开面板
3. 在「聊天」标签页与 AI 对话
4. 在「概览」查看今日统计
5. 在「日志」查看活动记录
6. 在「设置」调整参数

### 屏幕录制权限

macOS 需要授权屏幕录制权限：
系统设置 → 隐私与安全性 → 屏幕录制 → 允许终端/Python

## 🏗️ 架构

```
┌─────────────────────────────────────────────────┐
│                   用户 macOS 桌面                 │
└────────┬──────────────────────────┬──────────────┘
         │ 截图                      │ 对话
┌────────▼──────────┐    ┌──────────▼──────────────┐
│  monitor/          │    │  app/claude_client.py    │
│  screen_monitor.py │    │  (Popen + stream-json)   │
│  ├─ screenshot.py  │    └──────────┬──────────────┘
│  ├─ ocr.py         │               │
│  ├─ behavior_state │    ┌──────────▼──────────────┐
│  ├─ llm_client.py  │    │  pet_mcp_server.py      │
│  └─ scene_classifier   │  (stdio MCP Server)      │
└────────┬──────────┘    └──────────┬──────────────┘
         │ 写入                      │ 读取
┌────────▼──────────────────────────▼──────────────┐
│              ~/.pet-memory/                       │
│  ├─ activities/    活动 Markdown                  │
│  ├─ index/         每日索引                       │
│  ├─ summaries/     日/周/月总结                   │
│  ├─ screenshots/   截图文件                       │
│  ├─ ocr/           OCR 原始结果                   │
│  └─ logs/          监控/对话/统计日志             │
└──────────────────────────────────────────────────┘
```

### 模块说明

#### app/ — 应用核心
| 文件 | 职责 |
|------|------|
| `main.py` | 入口，编排监控/对话/UI，ChatWorker 流式消息分发 |
| `claude_client.py` | Claude Code CLI 桥接，支持 `send_message` 和 `send_message_stream` |
| `config.py` | YAML 配置加载，深度合并默认值 |
| `preflight.py` | 环境校验（Python/Ollama/Claude Code/屏幕权限），交互式模型选择 |
| `stream_parser.py` | Claude Code stream-json 事件解析器 |

#### monitor/ — 屏幕监控
| 文件 | 职责 |
|------|------|
| `screenshot.py` | macOS 前台窗口截图（Quartz CGWindowListCreateImage） |
| `ocr.py` | PaddleOCR 文字识别引擎 |
| `scene_classifier.py` | 场景分类（阅读/写作） |
| `behavior_state.py` | 四状态行为状态机（IDLE/OBSERVING/ENGAGED/BROWSING） |
| `text_similarity.py` | OCR 文本相似度（bigram Jaccard 系数） |
| `llm_client.py` | Ollama 摘要生成（含系统提示词） |
| `screen_monitor.py` | 监控主循环，协调截图→OCR→状态机→摘要 |
| `ocr_store.py` | OCR 结果持久化 |
| `idle_detector.py` | 用户空闲检测 |

#### memory/ — 记忆存储
| 文件 | 职责 |
|------|------|
| `activity_writer.py` | 活动 Markdown 写入 + 每日索引维护 |
| `summary_generator.py` | 日/周/月总结生成（Ollama 调用） |
| `screenshot_cleaner.py` | 截图/OCR/日志过期清理 |

#### logs/ — 日志系统
| 文件 | 职责 |
|------|------|
| `pet_logger.py` | MonitorLogger（操作日志）+ ChatLogger（对话日志）+ StatsCollector（统计） |

#### ui/ — 用户界面
| 文件 | 职责 |
|------|------|
| `tray_app.py` | 菜单栏应用（QSystemTrayIcon + 弹出面板） |
| `chat_widget.py` | 聊天面板（流式输出：思考/工具/文本分区展示） |
| `overview_widget.py` | 今日概览面板（截图数/活动数/时长统计） |
| `activity_log_widget.py` | 活动日志面板（日期选择 + 列表 + 详情展开） |
| `settings_widget.py` | 设置面板（模型/间隔/阈值/保留天数） |

#### pet_mcp_server.py — MCP Server
独立 stdio 服务，注册到 Claude Code 的 `settings.json`，提供 5 个工具：
- `read_activity_index` — 第1层索引
- `read_activity_detail` — 第2层详情（不含 OCR 原文）
- `read_activity_raw` — 第3层 OCR 原文
- `read_summary` — 日/周/月总结
- `list_available_dates` — 可用日期列表

### 数据目录结构

```
~/.pet-memory/
├── activities/
│   └── 2026-06-26/
│       ├── activity_001.md
│       └── activity_002.md
├── index/
│   └── 2026-06-26.md
├── summaries/
│   ├── daily/
│   ├── weekly/
│   └── monthly/
├── screenshots/
│   └── 2026-06-26/
├── ocr/
│   └── 2026-06-26/
│       └── 14-30-00.txt
└── logs/
    ├── monitor/
    │   └── 2026-06-26.md
    ├── chat/
    │   └── 2026-06-26.md
    └── stats/
        └── 2026-06-26.json
```

## ⚙️ 配置

编辑 `config.yaml`（或通过设置面板修改）：

```yaml
monitor:
  enabled: true
  interval_seconds: 15        # 截图间隔（10-60 秒）
  scenes: [reading, writing]  # 识别的场景类型
  idle_timeout_seconds: 120   # 空闲超时
  engage_threshold: 5         # 深度活动判定阈值（连续观察次数）

screenshots:
  quality: 75                 # JPEG 质量
  cleanup_similarity: 0.9     # 相似截图清理阈值
  retention_days: 7           # 截图保留天数

ocr:
  engine: paddleocr
  lang: ch                    # OCR 语言
  retention_days: 7           # OCR 结果保留天数

llm:
  local:
    provider: ollama
    model: qwen3:8b           # 由首次运行时交互选择
    base_url: http://localhost:11434

logs:
  retention_days: 30          # 日志保留天数

memory:
  base_dir: ~/.pet-memory
```

## 🧪 测试

```bash
# 运行全部测试
python -m pytest -v

# 运行单个模块测试
python -m pytest tests/test_behavior_state.py -v
python -m pytest tests/test_stream_parser.py -v
python -m pytest tests/test_ui.py -v
```

| 测试文件 | 覆盖模块 |
|----------|----------|
| `test_behavior_state.py` | 四状态行为状态机 |
| `test_text_similarity.py` | bigram Jaccard 相似度 |
| `test_ocr_store.py` | OCR 持久化 |
| `test_pet_logger.py` | 三层日志系统 |
| `test_stream_parser.py` | 流式事件解析器 |
| `test_claude_client.py` | Claude Code CLI 桥接 |
| `test_preflight.py` | 环境校验 |
| `test_ui.py` | UI 组件（菜单栏/聊天/概览/日志/设置） |
| `test_activity_writer.py` | 活动写入 + 索引 |
| `test_summary_generator.py` | 总结生成 |
| `test_screen_monitor.py` | 监控主循环 |
| `test_mcp_server.py` | MCP Server |
| `test_integration.py` | 端到端集成 |

## 🛠️ 开发

```bash
git clone https://github.com/your-username/doujianaodai.git
cd doujianaodai
pip install -e ".[dev]"
python -m pytest -v
```

### MCP Server 注册

将以下内容添加到 Claude Code 的 `~/.claude/settings.json`：

```json
{
  "mcpServers": {
    "pet-memory": {
      "command": "python",
      "args": ["/absolute/path/to/pet_mcp_server.py"]
    }
  }
}
```

## 📋 已知限制

- 仅支持 macOS（依赖 Quartz、AppKit 框架）
- 需要屏幕录制权限授权
- PaddleOCR 首次加载较慢（需下载模型文件）
- 截图仅限前台窗口，不支持多显示器
- 本地 LLM 摘要质量取决于模型能力

## 📄 License

MIT
```

- [ ] **Step 2: Verify README renders correctly**

```bash
python -c "from pathlib import Path; text = Path('README.md').read_text(); print(f'README: {len(text)} chars, {len(text.splitlines())} lines')"
```

- [ ] **Step 3: Run all tests (final check)**

Run: `cd /Users/zy/zytest/doujianaodai && python -m pytest -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: comprehensive README with architecture, modules, and usage guide"
```

---
