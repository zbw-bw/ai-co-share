# AI Co-Share

> 团队 AI 技术学习分享仓库，聚焦 LLM、Agent、AI 工具新用法。

## 分类

| 分类 | 内容 |
|------|------|
| [LLM](docs/llm/) | 大模型原理、微调、RAG、提示工程 |
| [Agent](docs/agent/) | Agent 框架、工作流、Multi-Agent |
| [Tools](docs/tools/) | Claude Code、Skills、Hooks、效率工具 |
| [Papers](docs/papers/) | 论文精读、前沿研究 |
| [周索引](docs/weekly/) | 每周新增内容汇总 |

## 快速分享

在仓库目录内打开 Claude Code，输入：

```
/ai-co-share <URL>
```

支持 GitHub 仓库、网站文章、YouTube/B站视频、arXiv 论文。自动总结 + 分类 + 提交。

## 贡献规范

- 直接 push main
- 文件命名：`YYYY-MM-DD-<slug>.md`
- Commit 格式：`share: <标题>` / `fix: <说明>` / `config: <说明>`
- 每篇文章需包含 frontmatter（title、date、author、tags、source）
