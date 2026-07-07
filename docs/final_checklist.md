# 最终项目收尾清单

## 当前结论

项目已经具备作品集展示的基础条件：功能链路完整、前端可演示、README 有截图、Docker 可一键启动、自动化测试覆盖核心流程。

## 必备项检查

| 检查项 | 状态 | 说明 |
| --- | --- | --- |
| README 项目介绍 | 已完成 | 已包含项目价值、功能亮点、截图、演示流程、技术栈和 Docker 启动说明 |
| 架构图 | 已完成 | `docs/architecture.md` 中包含 Mermaid 架构图和核心流程 |
| 功能截图 | 已完成 | `docs/screenshots/` 中已有 6 张截图和说明 |
| 演示视频脚本 | 已完成 | `docs/portfolio_package.md` 中已有 2-3 分钟脚本 |
| 简历项目描述 | 已完成 | `docs/portfolio_package.md` 中已有一句话版本和项目经历版本 |
| Docker 一键启动 | 已完成 | `docker compose up --build` 已能构建并启动项目 |
| 自动化测试 | 已完成 | 当前全量测试 26 个用例通过 |
| `.gitignore` | 已完成 | 已忽略数据库、上传文件、缓存、虚拟环境 |
| `.dockerignore` | 已完成 | 已避免把数据库、上传文件、缓存打进镜像 |

## GitHub 上传前建议

1. 不上传运行数据：
   - `backend/data/`
   - `backend/uploads/`
   - `*.db`
   - `__pycache__/`

2. 可以保留的作品集材料：
   - `README.md`
   - `docs/architecture.md`
   - `docs/portfolio_package.md`
   - `docs/final_checklist.md`
   - `docs/screenshots/`

3. 已删除的临时手工测试文件：
   - `backend/sample_policy.txt`
   - `backend/rag_request.json`
   - `backend/low_confidence_request.json`
   - `backend/invoice_request.json`
   - `backend/vacation_request.json`

这些文件曾用于手工 curl 测试，正式上传 GitHub 前已清理。

## 面试前演示顺序

1. 展示 README 首页，说明项目不是普通聊天机器人，而是完整 RAG + 工单 Agent。
2. 展示架构图，说明文档入库、向量检索、RAG 回答、低置信度转工单和后台指标。
3. 使用 Docker 一键启动：

```bash
docker compose up --build
```

4. 打开 `http://localhost:8000/`，点击“重置演示数据”。
5. 上传企业制度文档，展示上传、切分、向量化。
6. 提问文档内问题，展示答案、置信度和来源引用。
7. 提问文档外问题，展示低置信度转工单。
8. 展示后台问答记录、工单记录和运营指标。

## 后续优化方向

1. 接入真实 Embedding 模型，例如 OpenAI Embedding、BGE 或 Qwen Embedding。
2. 接入 LLM 生成更自然的客服话术，而不是直接拼接来源文本。
3. 增加工单状态流转，例如 `open`、`processing`、`resolved`。
4. 增加人工标注反馈，用于评估 RAG 回答质量。
5. 将 SQLite 升级为 PostgreSQL，贴近真实企业部署。
