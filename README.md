# 企业知识库 RAG + 工单客服 Agent

这是一个面向求职作品集的 AI Agent 项目，目标岗位包括 AI Agent 开发工程师、RAG 应用工程师、智能客服工程师、Prompt 工程师和 AI Agent 实施交付工程师。

## 项目为什么有价值

普通聊天机器人只能回答问题，但企业真实场景需要完整链路：

```text
文档上传 -> 文本切分 -> Embedding -> 向量检索 -> RAG 回答 -> 来源引用 -> 低置信度转工单 -> 后台记录 -> 效果评估
```

这个项目会围绕企业知识库客服场景，做一个能展示工程能力、RAG 理解能力和 Agent 工作流设计能力的完整作品。

## 功能亮点

- 文档上传：支持 `.txt`、`.md`、`.pdf`、`.docx` 企业知识库文档上传。
- 文本切分：支持配置切分长度和重叠长度，避免长文档直接检索效果差。
- Embedding + Chroma：将文本块写入向量库，支持基于问题的相似度检索。
- RAG 回答：返回答案、置信度和来源引用，避免黑盒式回答。
- 低置信度转工单：知识库无法可靠回答时自动创建人工客服工单。
- 候选片段提示：低置信度时展示候选片段，仅供人工处理参考。
- 后台记录：查看文档、问答、工单记录。
- 效果评估：统计文档数、问答数、工单数、平均置信度和转人工比例。
- 演示数据重置：一键清空文档记录、问答记录、工单和向量索引，方便录制演示。

## 架构与作品集材料

- 架构说明：[docs/architecture.md](docs/architecture.md)
- 作品集包装材料：[docs/portfolio_package.md](docs/portfolio_package.md)
- 最终收尾清单：[docs/final_checklist.md](docs/final_checklist.md)
- 功能截图目录：[docs/screenshots/](docs/screenshots/)

## 项目截图

### 1. 重置后的空首页

系统支持一键清空演示数据，方便每次从干净状态开始录制或演示。

![重置后的空首页](docs/screenshots/01-dashboard-empty.png)

### 2. 文档上传、切分、向量化

上传企业制度文档后，系统会自动完成保存文档、文本切分和 Chroma 向量写入。

![文档上传、切分、向量化成功](docs/screenshots/02-upload-success.png)

### 3. RAG 回答与来源引用

当知识库中存在可靠答案时，系统返回回答、置信度和来源片段。

![RAG 回答与来源引用](docs/screenshots/03-rag-answer-with-sources.png)

### 4. 低置信度自动转工单

当问题超出知识库范围时，系统不会强行回答，而是创建人工客服工单。候选片段只作为人工处理参考。

![低置信度自动转工单](docs/screenshots/04-low-confidence-ticket.png)

### 5. 后台问答记录

每次问答都会进入后台记录，便于后续审计、复盘和效果评估。

![后台问答记录](docs/screenshots/05-admin-qa-records.png)

### 6. 运营指标

系统统计文档数、问答数、工单数、低置信度数量、平均置信度和转人工比例。

![运营指标](docs/screenshots/06-metrics.png)

## 演示流程

1. 打开 `http://localhost:8000/`，点击“重置演示数据”，让系统回到空状态。
2. 上传企业制度文档，使用默认切分长度 `240`、重叠长度 `40`，点击“上传、切分、向量化”。
3. 提问文档内问题，例如“员工入职满10年但不满20年，每年可以享受多少天年假？”，观察答案、置信度和来源引用。
4. 提问文档外问题，例如“公司2024年的年度营收是多少？目前有多少名员工？”，观察低置信度转工单。
5. 查看后台“问答”和“工单”记录，确认每次问答和转人工都有记录。
6. 查看“运营指标”，观察问答数、工单数、平均置信度和转人工比例。

## 适合岗位

- AI Agent 开发工程师：项目覆盖 Agent 流程控制、低置信度兜底和后台记录。
- RAG 应用工程师：项目覆盖文档切分、Embedding、向量检索、来源引用和评估指标。
- 智能客服工程师：项目模拟企业客服知识库问答和转人工工单流程。
- Prompt 工程师 / AI Agent 产品研发：项目能展示如何设计可靠回答、拒答边界和可解释结果。
- AI Agent 实施交付工程师：项目包含可演示界面、后台记录、指标和重置演示数据能力。

## 项目亮点总结

- 完整链路：从文档入库到 RAG 回答，再到转工单和指标评估。
- 可解释：每次回答都返回来源片段和置信度。
- 不乱答：低置信度或事实缺失时自动转人工。
- 大模型增强：高置信度检索结果可交给 DeepSeek 生成更自然的客服回复。
- 可运营：后台能查看文档、问答、工单和评估指标。
- 可评测：提供批量评测脚本，统计关键词命中率、转人工准确率和平均置信度。
- 可展示：提供截图、架构说明、演示脚本和简历描述。

## 技术栈

- 后端：Python、FastAPI
- 数据库：SQLite，后续可升级 PostgreSQL
- 向量库：Chroma
- 大模型：DeepSeek API，默认模型 `deepseek-v4-flash`
- 文档解析：pypdf、python-docx
- 前端：HTML、CSS、JavaScript，后续可升级 React 或 Next.js
- 工程化：Docker、docker-compose

## 当前进度

第一天已完成的目标：

- 创建项目目录结构
- 创建最小 FastAPI 后端
- 实现 `/health` 健康检查接口
- 准备 SQLite 初始化能力
- 创建 `documents`、`qa_records`、`tickets` 三张核心表
- 编写后端自动化测试

第二天已完成的目标：

- 实现文档上传接口
- 支持上传 `.txt` 和 `.md` 企业知识库文档
- 支持上传 `.pdf` 和 `.docx` 企业知识库文档
- 将上传文件保存到 `backend/uploads/`
- 将文档文件名和路径写入 `documents` 表
- 为上传流程编写自动化测试

第三天已完成的目标：

- 实现文本切分函数
- 使用 `chunk_size` 控制每个文本块长度
- 使用 `chunk_overlap` 保留相邻文本块之间的重叠内容
- 新增 `document_chunks` 表保存切分结果
- 实现文档切分接口
- 为切分算法和切分接口编写自动化测试

第四天已完成的目标：

- 实现本地确定性 Embedding 函数
- 将 `document_chunks` 文本块写入 Chroma 向量库
- 实现文档向量化索引接口
- 实现基础向量检索接口
- 为 Embedding、Chroma 索引和检索编写自动化测试

第五天已完成的目标：

- 实现 RAG 问答接口
- 基于向量检索结果组织回答上下文
- 返回来源引用 `sources`
- 返回回答置信度 `confidence`
- 将问答记录写入 `qa_records` 表
- 为 RAG 主流程和低匹配场景编写自动化测试

第六天已完成的目标：

- 实现低置信度自动转工单
- RAG 响应返回 `escalated_to_ticket` 和 `ticket_id`
- 将低置信度问题写入 `tickets` 表
- 实现后台工单列表接口
- 为低置信度转工单和工单列表编写自动化测试

第七天已完成的目标：

- 实现后台文档列表接口
- 实现后台问答记录接口
- 实现评估指标接口
- 指标包含文档数、问答数、工单数、低置信度数量、平均置信度、转人工比例
- 为后台记录和空项目指标场景编写自动化测试

第八天已完成的目标：

- 实现可视化前端工作台
- 首页展示文档上传、自动切分、Embedding 写入、RAG 提问、来源引用、工单和指标
- FastAPI 直接托管前端静态文件
- 打开 `http://localhost:8000/` 即可使用界面
- 为前端首页和静态资源托管编写自动化测试

第九天已完成的目标：

- 新增演示数据重置接口
- 支持清空文档记录、问答记录、工单记录和 Chroma 向量索引
- 前端运营指标区域新增“重置演示数据”按钮
- 重置后自动刷新后台记录和评估指标
- 为重置接口和前端入口编写自动化测试

第十天已完成的目标：

- 完善架构说明和 Mermaid 架构图
- 新增功能截图清单
- 新增演示视频脚本
- 新增简历项目描述
- 强化 GitHub README 首页展示内容

增强阶段已完成的目标：

- 接入 DeepSeek Chat Completions API
- 默认使用 `deepseek-v4-flash` 作为 RAG 生成模型
- 保留无 API Key 时的本地来源拼接回退能力
- 低置信度或事实缺失时不调用大模型，直接转人工工单
- 更新 Docker 和环境变量配置，支持一键启动时传入 DeepSeek API Key
- 支持 PDF / Word 文档解析，企业制度文档可直接入库
- 新增批量评测脚本和 Markdown 评测报告

## 本地运行后端

进入后端目录：

```bash
cd backend
```

启动服务：

```bash
python -m uvicorn app.main:app --reload
```

访问健康检查：

```text
http://localhost:8000/health
```

预期返回：

```json
{"status":"ok"}
```

访问前端工作台：

```text
http://localhost:8000/
```

前端工作台包含：

- 文档上传
- 自动文本切分
- 自动写入 Chroma
- RAG 提问
- 来源引用展示
- 低置信度转工单提示
- 文档、问答、工单记录
- 评估指标面板

## Docker 一键启动

如果本机已安装 Docker Desktop，可以在项目根目录直接执行：

```bash
docker compose up --build
```

启动完成后访问：

```text
http://localhost:8000/
```

健康检查：

```text
http://localhost:8000/health
```

预期返回：

```json
{"status":"ok"}
```

Docker 启动时会自动完成：

- 使用 Python 3.11 创建运行环境。
- 安装 `backend/requirements.txt` 中的依赖。
- 复制后端代码和前端静态页面。
- 启动 FastAPI 服务。
- 将容器端口 `8000` 映射到本机 `localhost:8000`。

如需启用 DeepSeek 生成答案，在启动前设置环境变量：

```powershell
$env:DEEPSEEK_API_KEY="你的 DeepSeek API Key"
docker compose up --build
```

如果不设置 `DEEPSEEK_API_KEY`，系统仍然可以运行，会自动回退为本地来源拼接回答。

数据持久化目录：

- SQLite 数据库：`backend/data/app.db`
- Chroma 向量库：`backend/data/chroma`
- 上传文件：`backend/uploads`

停止服务：

```bash
docker compose down
```

## 运行测试

```bash
cd backend
python -m unittest discover -s tests -v
```

## 运行批量评测

先确保已经上传并向量化企业制度文档，然后在后端目录执行：

```bash
cd backend
python scripts/evaluate_rag.py
```

默认问题集：

```text
docs/evaluation/rag_eval_questions.json
```

默认输出报告：

```text
docs/evaluation/evaluation_report.md
```

评测脚本会统计：

- 总问题数
- 通过率
- 关键词命中率
- 低置信度转人工准确率
- 平均置信度
- 平均来源数量

## 文档上传接口

接口地址：

```text
POST /documents/upload
```

当前支持文件类型：

```text
.txt
.md
.pdf
.docx
```

使用 Windows PowerShell 测试上传：

```powershell
cd backend
Set-Content -Path sample_policy.txt -Value "Refunds are handled within 7 business days."
curl.exe -X POST -F "file=@sample_policy.txt;type=text/plain" http://localhost:8000/documents/upload
```

预期返回：

```json
{
  "id": 1,
  "filename": "sample_policy.txt",
  "file_path": "C:\\...\\backend\\uploads\\sample_policy.txt"
}
```

## 文本切分接口

接口地址：

```text
POST /documents/{document_id}/chunks
```

示例：

```powershell
curl.exe -X POST "http://localhost:8000/documents/1/chunks?chunk_size=40&chunk_overlap=10"
```

预期返回：

```json
{
  "document_id": 1,
  "chunk_count": 3,
  "chunks": [
    {
      "id": 1,
      "document_id": 1,
      "chunk_index": 0,
      "content": "..."
    }
  ]
}
```

为什么需要 `chunk_overlap`：

如果一句关键答案刚好跨越两个文本块，完全不重叠的切分会破坏语义。保留一小段重叠内容，可以提高后续向量检索命中的概率。

## Embedding 和向量检索接口

先把某个文档的文本块写入 Chroma：

```text
POST /documents/{document_id}/embeddings
```

示例：

```powershell
curl.exe -X POST "http://localhost:8000/documents/1/embeddings"
```

预期返回：

```json
{
  "document_id": 1,
  "indexed_count": 2
}
```

再用问题检索相关文本块：

```text
GET /search?query=refund%20days&top_k=1
```

示例：

```powershell
curl.exe "http://localhost:8000/search?query=refund%20days&top_k=1"
```

预期返回：

```json
{
  "results": [
    {
      "document_id": 1,
      "chunk_id": 1,
      "chunk_index": 0,
      "content": "...",
      "distance": 0.42
    }
  ]
}
```

当前版本使用本地确定性 Embedding，优点是不需要 API Key、不需要下载模型，适合先跑通工程链路。后续可以替换为 OpenAI Embedding、BGE 或其他真实语义向量模型。

## RAG 问答接口

接口地址：

```text
POST /rag/answer
```

示例：

```powershell
Set-Content -Path rag_request.json -Value "{\"question\":\"How long do refunds take?\",\"top_k\":2}"
curl.exe -X POST "http://localhost:8000/rag/answer" -H "Content-Type: application/json" --data-binary "@rag_request.json"
```

预期返回：

```json
{
  "id": 1,
  "question": "How long do refunds take?",
  "answer": "根据企业知识库内容，可以回答：...",
  "confidence": 0.42,
  "sources": [
    {
      "document_id": 1,
      "chunk_id": 1,
      "chunk_index": 0,
      "content": "Refunds are handled within 7 business da",
      "distance": 1.33
    }
  ]
}
```

为什么要返回来源引用：

企业 RAG 系统不能只给一个“看起来像真的”答案。面试官会重点看系统是否能说明答案来自哪份文档、哪个文本块，以及检索置信度如何。来源引用是 RAG 项目区别于普通聊天机器人的关键点。

## 低置信度转工单

当 RAG 置信度低于阈值时，系统会自动创建人工客服工单。

RAG 响应里会包含：

```json
{
  "confidence": 0.0,
  "escalated_to_ticket": true,
  "ticket_id": 1
}
```

查看工单列表：

```text
GET /tickets
```

示例：

```powershell
curl.exe "http://localhost:8000/tickets"
```

预期返回：

```json
{
  "tickets": [
    {
      "id": 1,
      "question": "What is the vacation policy?",
      "status": "open",
      "reason": "low confidence: 0.0",
      "created_at": "2026-07-06 12:00:00"
    }
  ]
}
```

为什么要做自动转工单：

企业客服系统不能在没有依据时强行回答。低置信度转工单体现了 Agent 的流程控制能力：能回答就自动回答，不能可靠回答就转人工处理。

## 后台记录和评估指标

查看文档记录：

```text
GET /admin/documents
```

查看问答记录：

```text
GET /admin/qa-records
```

查看评估指标：

```text
GET /admin/metrics
```

清空演示数据：

```text
POST /admin/reset-demo
```

示例：

```powershell
curl.exe "http://localhost:8000/admin/metrics"
```

预期返回：

```json
{
  "total_documents": 1,
  "total_qa_records": 2,
  "total_tickets": 1,
  "low_confidence_count": 1,
  "average_confidence": 0.36,
  "escalation_rate": 0.5,
  "low_confidence_rate": 0.5
}
```

为什么要做评估指标：

RAG 项目不能只展示“能回答”。企业落地更关心效果是否可观察，比如多少问题被回答、多少问题转人工、平均置信度如何。后台指标能体现你理解 RAG 系统的运营和评估闭环。

为什么要做演示数据重置：

作品集演示时经常需要重新录制流程。如果旧问答、旧工单和旧向量还在，页面会显得混乱，也容易召回过期内容。重置功能让你可以从干净状态开始：上传文档、提问、触发工单、观察指标，形成一条稳定可复现的演示路径。

## 项目结构

```text
.
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── db/
│   │   └── main.py
│   ├── tests/
│   ├── uploads/
│   ├── Dockerfile
│   └── requirements.txt
├── docs/
│   ├── architecture.md
│   ├── portfolio_package.md
│   └── screenshots/
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── scripts/
├── docker-compose.yml
└── README.md
```

## 下一阶段

下一步计划：继续优化回答质量，让文档内问题的回答更像真实客服话术，并接入真实 Embedding 或大模型 API。
