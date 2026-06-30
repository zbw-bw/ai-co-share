# UI + 打包分发 + README 文档设计

日期: 2026-06-26

## 概述

三个方向：
1. 将 PyQt6 窗口应用改造为 macOS 菜单栏应用（QSystemTrayIcon）
2. 用 pyproject.toml 打包发布到 PyPI，支持 `doujianaodai` 命令直接启动
3. 编写完整 README 文档，覆盖架构、模块、安装、测试、配置

## 一、CLI 入口与环境校验

### 启动命令

`doujianaodai` — 通过 pyproject.toml 的 `[project.scripts]` 注册。

### 首次运行交互式引导

启动时按顺序校验环境，所有检查通过后才启动 UI：

1. **Python 版本** — ≥ 3.11，否则报错退出
2. **Ollama** — 请求 `http://localhost:11434/api/tags`
   - 未安装 → 提示 `brew install ollama && ollama serve`
   - 已安装但未运行 → 提示 `ollama serve`
   - 运行中 → 列出已安装模型，让用户选择，写入 `config.yaml`
3. **Claude Code** — 运行 `claude --version`
   - 未找到 → 提示安装方式
   - 可用 → 显示版本号
4. **屏幕录制权限**（macOS）— 尝试截图
   - 失败 → 提示去系统设置授权

已有配置时跳过模型选择，直接验证模型是否仍然可用。

### 输出格式

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

## 二、菜单栏 UI

### 技术方案

用 PyQt6 `QSystemTrayIcon` 实现 macOS 菜单栏常驻应用。点击图标弹出主面板窗口。

### 菜单结构

```
[逗叽脑袋图标] (菜单栏常驻)
  ├── 左键点击 → 弹出主面板（QWidget 弹窗，固定在图标下方）
  │   ├── Tab 1: 💬 聊天
  │   ├── Tab 2: 📊 今日概览
  │   ├── Tab 3: 📋 活动日志
  │   └── Tab 4: ⚙️ 设置
  │
  └── 右键菜单（QMenu）
      ├── 监控: 运行中 ✓ （点击切换暂停/恢复）
      ├── Agent: 已连接 ✓
      ├── ──────────
      ├── 打开数据目录（Finder 打开 ~/.pet-memory/）
      └── 退出
```

### Tab 1: 聊天（流式对话）

#### 流式输出架构

当前 `ClaudeClient` 使用 `subprocess.run()` 阻塞等待。改为 `subprocess.Popen` + 逐行读取 stdout，配合 `--output-format stream-json --verbose` 参数实现流式输出。

**Claude Code stream-json 事件类型（已验证）：**

| 事件 JSON | 含义 | UI 处理 |
|-----------|------|---------|
| `type: "system", subtype: "init"` | 初始化，含 model/tools 信息 | 显示"已连接 {model}" |
| `type: "system", subtype: "thinking_tokens"` | 思考进度（token 计数递增） | 更新思考进度指示 |
| `type: "assistant", content[].type: "thinking"` | 思考内容文本 | 在折叠区域显示思考过程 |
| `type: "assistant", content[].type: "text"` | 回复文本（增量） | 实时追加到回复气泡 |
| `type: "assistant", content[].type: "tool_use"` | 工具调用（name + input） | 显示"🔧 正在调用: {tool_name}" |
| `type: "assistant", content[].type: "tool_result"` | 工具返回结果 | 显示工具结果摘要 |
| `type: "result"` | 最终结果 + session_id | 完成，记录 session_id |

#### ClaudeClient 改造

```python
class ClaudeClient:
    def send_message_stream(self, text: str) -> Generator[StreamEvent, None, None]:
        """流式发送消息，yield StreamEvent 对象。"""
        cmd = ["claude", "-p", text, "--output-format", "stream-json", "--verbose"]
        if self._session_id:
            cmd.extend(["--resume", self._session_id])
        
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in proc.stdout:
            event = parse_stream_event(line.strip())
            if event:
                yield event
```

```python
@dataclass
class StreamEvent:
    event_type: str      # "thinking" | "text" | "tool_use" | "tool_result" | "status" | "done"
    content: str         # 文本内容或工具名
    metadata: dict       # 额外信息（model, session_id, duration 等）
```

#### ChatWorker 改造

改为逐事件发 signal，UI 实时更新：

```python
class ChatWorker(QThread):
    stream_event = pyqtSignal(dict)   # 每个事件实时发射
    finished = pyqtSignal()

    def run(self):
        for event in self._client.send_message_stream(self._message):
            self.stream_event.emit(event.to_dict())
        self.finished.emit()
```

#### 聊天界面展示

```
╭──────────────────────────────────╮
│ 💬 聊天              [清空对话]  │
├──────────────────────────────────┤
│                                  │
│        ┌──────────────┐          │
│        │ 今天做了什么？ │  ← 用户  │
│        └──────────────┘          │
│                                  │
│  ┌─ 🧠 思考中... ──────────┐     │
│  │ 用户在问今天的活动，     │     │
│  │ 我需要读取活动索引...   │     │
│  └─────────────────────────┘     │
│                                  │
│  🔧 调用: read_activity_index    │
│     参数: date="today"           │
│  ✓ 返回 3 条活动记录             │
│                                  │
│  🔧 调用: read_activity_detail   │
│     参数: "activities/...001.md" │
│  ✓ 返回活动详情                  │
│                                  │
│  ┌──────────────────────────┐    │
│  │ 根据记录，你今天上午主要  │    │
│  │ 做了三件事：              │    │
│  │ 1. 阅读 K8s 调度策略文档 │    │
│  │ 2. ...（流式逐字显示）   │ ← 助手
│  └──────────────────────────┘    │
│                                  │
├──────────────────────────────────┤
│ [输入消息...            ] [发送] │
╰──────────────────────────────────╯
```

**展示规则：**
- **思考过程**：灰色折叠区域，默认展开，可点击收起。前缀 "🧠 思考中..."，完成后变 "🧠 思考完成"
- **工具调用**：蓝色小字，显示工具名和关键参数，结果用 ✓ 标记
- **回复文本**：正常气泡，逐字/逐句追加（每收到一个 text event 就 append）
- **状态指示**：输入框上方显示当前阶段（"思考中..." / "调用工具..." / "生成回复..."）

### Tab 2: 今日概览

读取 `~/.pet-memory/logs/stats/` 当日 JSON + `index/` 当日索引：

```
╭─────────────────────────╮
│  📊 今日概览            │
│                         │
│  截图次数    128        │
│  识别活动    6 条       │
│  深度学习    3 次       │
│  总学习时长  45 分钟    │
│  浏览时长    12 分钟    │
│  摘要生成    3 次       │
│                         │
│  ─ 专注度 ────────────  │
│  ENGAGED ████████░░ 78% │
│  BROWSING ██░░░░░░ 22%  │
╰─────────────────────────╯
```

### Tab 3: 活动日志

读取 `~/.pet-memory/index/` 当日索引文件：
- 列表视图，每行显示：时间 + 场景标签 + 一句话摘要
- 点击某条 → 展开显示内容要点和详细描述
- 顶部日期选择器切换日期
- 底部显示当日活动总数

### Tab 4: 设置

可视化编辑 `config.yaml`，保存后实时生效：

| 设置项 | 控件 | 说明 |
|--------|------|------|
| Ollama 模型 | 下拉框（动态拉取） | 从 Ollama API 获取已安装模型列表 |
| 截图间隔 | 滑块 10-60s | 默认 15s |
| 深度活动阈值 | 滑块 3-10 次 | 默认 5 次 |
| 截图保留天数 | 输入框 | 默认 7 天 |
| OCR 保留天数 | 输入框 | 默认 7 天 |
| 日志保留天数 | 输入框 | 默认 30 天 |
| 开机自启动 | 开关 | macOS LaunchAgent |

### 窗口行为

- 菜单栏图标使用简单的文字图标 "🧠" 或自定义 16x16 PNG
- 主面板固定 420x520 大小
- 点击面板外部自动隐藏
- 应用不在 Dock 显示（`LSUIElement = true`）
- 关闭窗口 = 隐藏，退出需通过右键菜单

## 三、PyPI 打包

### pyproject.toml

替代现有 `setup.py`：

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "doujianaodai"
version = "0.1.0"
description = "桌面宠物 Agent — 被动屏幕监控 + 活动记忆 + AI 对话"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
keywords = ["desktop-pet", "screen-monitor", "ai-agent", "ocr"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: MacOS X",
    "Programming Language :: Python :: 3.11",
    "Topic :: Utilities",
]
dependencies = [
    "PyQt6>=6.6.0",
    "pyobjc-framework-Quartz>=10.0; sys_platform=='darwin'",
    "pyobjc-framework-Cocoa>=10.0; sys_platform=='darwin'",
    "psutil>=5.9.0",
    "Pillow>=10.0.0",
    "paddleocr>=2.7.0",
    "paddlepaddle>=2.6.0",
    "scikit-image>=0.22.0",
    "numpy>=1.26.0",
    "PyYAML>=6.0",
    "requests>=2.31.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0"]

[project.scripts]
doujianaodai = "app.main:main"

[tool.setuptools.packages.find]
include = ["app*", "monitor*", "memory*", "logs*", "ui*"]

[tool.setuptools.package-data]
"" = ["config.yaml"]
```

### 需要清理的内容

- 删除 `setup.py`（被 pyproject.toml 替代）
- 删除 `doujianaodai.egg-info/`
- 从 requirements.txt 移除 `anthropic>=0.34.0`（不再使用 SDK）
- 添加 `MANIFEST.in` 包含 `config.yaml` 和 `pet_mcp_server.py`

### 发布流程

```bash
pip install build twine
python -m build
twine upload dist/*
```

## 四、README 文档

### 结构

```markdown
# 逗叽脑袋 (doujianaodai)

> 桌面宠物 Agent — 被动监控屏幕活动，记录你的学习与工作，随时对话回顾你的一天。

## ✨ 功能特性

### 🖥️ 被动屏幕监控
- 15 秒间隔截取前台窗口
- PaddleOCR 本地文字识别
- 四状态行为状态机（IDLE/OBSERVING/ENGAGED/BROWSING）
- 仅记录深度活动（≥75 秒停留），过滤快速浏览

### 🧠 智能活动记忆
- 本地 Ollama 小模型生成内容摘要
- 三层记忆：活动记录 → 每日总结 → 周/月总结
- 全部以 Markdown 文件存储，无数据库
- 三层读取策略：索引 → 详情 → OCR 原文

### 💬 AI 对话
- 通过 Claude Code CLI 桥接对话
- MCP Server 提供记忆读取工具
- 支持问"今天做了什么"、"这周学了什么"

### 📊 日志与统计
- 监控操作日志（状态转换、截图、摘要生成）
- 对话日志（消息、耗时、模型）
- 每日效果统计（专注度、活动时长、摘要命中率）

## 📦 安装

### 前置条件
- macOS 12+
- Python 3.11+
- Ollama（本地 LLM）
- Claude Code（AI 对话）

### 安装 Ollama
（brew install, 下载模型步骤）

### 安装 Claude Code
（安装步骤）

### 安装逗叽脑袋
pip install doujianaodai

## 🚀 快速开始
首次运行 doujianaodai，交互式引导
授权屏幕录制权限
开始使用

## 🏗️ 架构

### 整体架构图
ASCII 架构图

### 模块说明

#### app/ — 应用核心
- main.py: 入口，编排监控/对话/UI
- claude_client.py: Claude Code CLI 桥接
- config.py: 配置加载
- preflight.py: 环境校验

#### monitor/ — 屏幕监控
- screenshot.py: macOS 前台窗口截图（Quartz API）
- ocr.py: PaddleOCR 文字识别
- scene_classifier.py: 场景分类（阅读/写作）
- behavior_state.py: 四状态行为状态机
- text_similarity.py: OCR 文本相似度（bigram Jaccard）
- llm_client.py: Ollama 摘要生成
- screen_monitor.py: 监控主循环
- ocr_store.py: OCR 结果持久化
- idle_detector.py: 用户空闲检测

#### memory/ — 记忆存储
- activity_writer.py: 活动文档写入 + 索引维护
- summary_generator.py: 日/周/月总结
- screenshot_cleaner.py: 截图/OCR/日志清理

#### logs/ — 日志系统
- pet_logger.py: MonitorLogger + ChatLogger + StatsCollector

#### ui/ — 用户界面
- tray_app.py: 菜单栏应用（QSystemTrayIcon）
- chat_widget.py: 聊天面板
- overview_widget.py: 今日概览面板
- activity_log_widget.py: 活动日志面板
- settings_widget.py: 设置面板

#### pet_mcp_server.py — MCP Server
独立 stdio 服务，注册在 Claude Code settings.json

### 数据流图

### 记忆目录结构
~/.pet-memory/ 完整目录树

## ⚙️ 配置
config.yaml 各字段说明表

## 🧪 测试
pytest 命令
测试模块对照表

## 🛠️ 开发
本地开发环境搭建
代码结构
贡献指南

## 📋 已知限制
- 仅 macOS（依赖 Quartz、AppKit）
- 需要屏幕录制权限
- PaddleOCR 首次加载较慢（需下载模型）
- 截图仅限前台窗口

## 📄 License
MIT
```

## 五、受影响的文件

### 新增

| 文件 | 职责 |
|------|------|
| `pyproject.toml` | PyPI 打包配置 |
| `MANIFEST.in` | 包含非 Python 文件 |
| `LICENSE` | MIT 许可证 |
| `app/preflight.py` | 环境校验 + 交互式引导 |
| `app/stream_parser.py` | Claude Code stream-json 事件解析器（StreamEvent dataclass + parse_stream_event） |
| `ui/tray_app.py` | 菜单栏应用主类 |
| `ui/overview_widget.py` | 今日概览面板 |
| `ui/activity_log_widget.py` | 活动日志面板 |
| `ui/settings_widget.py` | 设置面板 |

### 修改

| 文件 | 改动 |
|------|------|
| `app/main.py` | 加入 preflight 校验，启动 tray_app 替代 MainWindow |
| `app/claude_client.py` | 新增 `send_message_stream()` 方法，用 Popen + stream-json |
| `ui/main_window.py` | 改为 Tab 面板容器 |
| `ui/chat_widget.py` | 支持流式消息（思考/工具/文本分区展示） |
| `README.md` | 全文重写 |
| `config.yaml` | 无改动，但 pyproject.toml 需要打包它 |
| `requirements.txt` | 移除 anthropic，与 pyproject.toml 同步 |

### 删除

| 文件 | 原因 |
|------|------|
| `setup.py` | 被 pyproject.toml 替代 |
| `doujianaodai.egg-info/` | 旧构建产物 |
| `test_pipeline.py` | 临时测试脚本 |
| `ui/status_bar.py` | 被菜单栏右键菜单替代 |

## 六、不变的部分

- monitor/ 全部模块不变
- memory/ 全部模块不变
- logs/ 不变
- pet_mcp_server.py 不变
- 所有现有测试不变
