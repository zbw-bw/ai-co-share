# 截图间隔与摘要规则引擎设计

日期: 2026-06-26

## 概述

重新设计桌面宠物 agent 的截图间隔策略和摘要生成规则引擎，解决两个核心问题：
1. 截图间隔从 30s 缩短到 15s，匹配人类信息获取节奏
2. 引入行为状态机，通过多次截图的特征序列判断用户是否真正在学习/工作，而非截一次图就生成摘要

同时增加：
3. 日志记录系统，覆盖监控操作、对话记录、效果统计三类
4. OCR 结果持久化存储，与截图对应，支持可配置的定时清除

## 截图间隔策略

**固定 15 秒间隔**，不做动态调整。

理由：
- 15s 匹配人类信息获取节奏（10-30s 扫一眼页面）
- 15s × 5 次 = 75s 作为最低深度活动阈值，体感合理
- 截图本身开销极低（macOS Quartz API < 50ms）
- PaddleOCR 是本地推理，4 次/分钟可接受

配置改动：`config.yaml` 中 `interval_seconds: 30` → `interval_seconds: 15`

## 行为状态机

### 状态定义

| 状态 | 含义 | 持有数据 |
|------|------|----------|
| `IDLE` | 无可追踪内容（未知应用/空闲） | 无 |
| `OBSERVING` | 检测到阅读/写作场景，积累证据中 | 截图序列、OCR 文本序列、计数器 |
| `ENGAGED` | 确认用户正在深度活动 | 活动上下文（合并后的 OCR 文本集） |
| `BROWSING` | 用户在快速切换浏览，不生成摘要 | 无 |

### 状态转换规则

```
IDLE
  ├── 检测到 reading/writing 场景 → OBSERVING（count=1）

OBSERVING
  ├── 同一活动连续出现 ≥5 次（OCR 相似或渐变） → ENGAGED
  ├── 内容突变（OCR 相似度 < 0.3）且 count < 5 → 重置 OBSERVING（新内容 count=1）
  ├── 连续 2 次内容突变 → BROWSING
  └── 场景变为 None → IDLE

ENGAGED
  ├── 同一活动继续（OCR 相似或渐变） → 留在 ENGAGED，持续收集 OCR
  ├── 内容突变或窗口切换 → ★触发摘要生成★ → OBSERVING 或 IDLE
  └── 用户空闲超时（120s） → ★触发摘要生成★ → IDLE

BROWSING
  ├── 同一内容连续 ≥5 次 → ENGAGED
  ├── 继续快速切换 → 留在 BROWSING
  └── 场景变为 None → IDLE
```

### OCR 文本相似度

使用字符级 bigram Jaccard 相似度（轻量，无需额外依赖）：

```python
def text_similarity(text_a: str, text_b: str) -> float:
    if not text_a or not text_b:
        return 0.0
    bigrams_a = set(zip(text_a, text_a[1:]))
    bigrams_b = set(zip(text_b, text_b[1:]))
    intersection = bigrams_a & bigrams_b
    union = bigrams_a | bigrams_b
    return len(intersection) / len(union) if union else 0.0
```

阈值：
- **相似**（同一页面未动）：> 0.7
- **渐变**（滚动阅读/持续编辑）：0.3 ~ 0.7
- **突变**（完全不同内容）：< 0.3

## 摘要生成规则

### 触发条件

摘要**仅**在从 `ENGAGED` 状态离开时生成，三种触发场景：
1. **内容突变** — OCR 相似度 < 0.3
2. **窗口切换** — 前台应用或窗口标题变化
3. **空闲超时** — 用户离开电脑（idle > 120s）

### 不生成摘要的情况

- `BROWSING` 状态离开 → 不生成（快速浏览）
- `OBSERVING` 直接回 `IDLE` → 不生成（未达深度阈值）
- 停留时间 < 75s → 不生成

### 传给小模型的数据

ENGAGED 期间收集的完整 OCR 文本序列（去重合并），而非单次截图：

```
输入:
- 应用名 + 窗口标题
- 场景类型（reading/writing）
- 停留时长（首次确认到离开的时间差）
- OCR 文本序列（去重后合并，截取前 3000 字）

输出:
- 摘要（20 字以内）
- 内容要点（3-5 条）
- 详细描述（100-200 字）
```

### 数据流对比

```
之前: 截图 → OCR → 2次确认 → 立即调 LLM → 写入
之后: 截图 → OCR → 保存OCR结果 → 状态机判断 → ENGAGED期间持续收集OCR
                                              → 离开ENGAGED → 合并OCR → 调LLM → 写入
```

## 日志记录系统

### 日志分类

三类日志全部存储在 `~/.pet-memory/logs/` 下，使用 markdown 格式按日期分文件。

#### 1. 监控操作日志 (`logs/monitor/YYYY-MM-DD.md`)

记录监控循环的关键事件，用于溯源和调试：

```markdown
# 2026-06-26 监控日志

- [10:00:15] SCREENSHOT app=Google Chrome title="K8s调度策略" ocr_len=856
- [10:00:16] STATE IDLE → OBSERVING reason="检测到reading场景"
- [10:00:30] SCREENSHOT app=Google Chrome title="K8s调度策略" ocr_len=823 similarity=0.82
- [10:00:31] STATE OBSERVING count=2/5
- [10:01:15] STATE OBSERVING → ENGAGED count=5 elapsed=60s
- [10:05:30] STATE ENGAGED → IDLE reason="窗口切换" duration=285s
- [10:05:31] SUMMARY_GENERATED activity=activity_003.md ocr_inputs=18 llm_time=3.2s
```

每条日志包含：时间戳、事件类型、关键参数。

#### 2. 对话日志 (`logs/chat/YYYY-MM-DD.md`)

记录用户与 Claude Code 的对话，用于溯源和评测：

```markdown
# 2026-06-26 对话日志

## 10:15:23 session=d146f243

**用户**: 我今天上午做了什么？

**助手**: 根据活动记录，你上午主要做了两件事...

- 耗时: 2.6s
- 模型: Qwen3.7-Max
- 使用工具: read_activity_index(today), read_activity_detail(activity_003.md)
```

每条对话包含：时间戳、session_id、用户消息、助手回复、耗时、调用的 MCP 工具。

#### 3. 效果统计 (`logs/stats/YYYY-MM-DD.json`)

每日自动汇总的量化指标，JSON 格式便于分析：

```json
{
  "date": "2026-06-26",
  "monitor": {
    "screenshots_total": 320,
    "ocr_total": 320,
    "state_transitions": {
      "idle_to_observing": 15,
      "observing_to_engaged": 8,
      "observing_to_browsing": 4,
      "engaged_exits": 8
    },
    "engaged_sessions": 8,
    "engaged_avg_duration_sec": 240,
    "browsing_sessions": 4,
    "summaries_generated": 8,
    "llm_calls_total": 8,
    "llm_avg_time_sec": 3.1
  },
  "chat": {
    "conversations": 5,
    "messages_total": 12,
    "avg_response_time_sec": 2.8,
    "tools_used": {
      "read_activity_index": 4,
      "read_activity_detail": 3,
      "read_activity_raw": 1
    }
  }
}
```

关键评测指标：
- **ENGAGED/BROWSING 比值**：越高说明用户专注度越好
- **摘要生成次数 vs 截图次数**：比值越低说明规则引擎过滤越有效
- **平均 ENGAGED 时长**：反映用户深度学习/工作的持续时间
- **第3层（raw）调用次数**：越多说明第2层摘要质量可能不够

### 日志清理

日志文件保留策略与 config.yaml 中其他清理配置一致，可配置保留天数，默认 30 天。

## OCR 结果持久化

### 存储结构

OCR 结果与截图一一对应，存储在 `~/.pet-memory/ocr/` 下：

```
~/.pet-memory/ocr/
└── 2026-06-26/
    ├── 10-00-15.txt    ← 对应 screenshots/2026-06-26/10-00-15.jpg
    ├── 10-00-30.txt
    └── ...
```

纯文本文件，文件名与截图时间戳对应。

### 用途

- 状态机在判断 OCR 相似度时可直接读取上一次的 OCR 结果，不需要重新 OCR
- 离开 ENGAGED 时合并 OCR 文本，从文件中批量读取
- MCP Server 的 `read_activity_raw` 工具可直接读取对应的 OCR 文件
- 调试和效果评测时可以回溯截图与 OCR 的对应关系

### 清理策略

在 config.yaml 中新增配置项：

```yaml
ocr:
  engine: paddleocr
  lang: ch
  retention_days: 7    # 新增：OCR结果保留天数，默认与截图一致
```

清理逻辑与截图清理（`cleanup_expired`）复用同一时机，在 app 关闭时执行。

## 受影响的文件

| 文件 | 改动 |
|------|------|
| `config.yaml` | interval_seconds 30→15，新增 ocr.retention_days 和 logs.retention_days |
| `monitor/screen_monitor.py` | 接入状态机，保存 OCR 结果，写监控日志 |
| `memory/activity_merger.py` | 重写为行为状态机 |
| `monitor/llm_client.py` | generate_summary 接收 OCR 文本列表而非单次文本 |
| `app/claude_client.py` | 发送/接收消息时写对话日志 |
| `app/main.py` | 关闭时生成效果统计、清理 OCR 文件和过期日志 |
| `memory/screenshot_cleaner.py` | 新增 OCR 文件和日志文件的清理 |

## 新增模块

| 文件 | 职责 |
|------|------|
| `monitor/text_similarity.py` | OCR 文本相似度计算 |
| `monitor/behavior_state.py` | 行为状态机实现 |
| `monitor/ocr_store.py` | OCR 结果保存与读取 |
| `logs/logger.py` | 统一日志记录（监控日志、对话日志、效果统计） |

## 不变的部分

- 截图捕获（screenshot.py）不变
- OCR 引擎（ocr.py）不变
- 活动写入（activity_writer.py）不变
- MCP Server 三层读取结构不变（read_activity_raw 改为从 ocr/ 目录读取）
- 日/周/月总结生成不变
