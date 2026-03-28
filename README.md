# Contract Review Risk Agent MVP

## 项目简介

这是一个基于 FastAPI 的合同审查风险 Agent MVP。
目标是快速识别合同中的明显风险条款，并输出结构化 JSON 结果。

当前 MVP 已实现：
- 合同文件上传与解析
- 合同条款切分
- 规则风险识别
- 结构化风险分析输出
- SQLite 历史记录持久化
- 第一版轻量 RAG 检索增强

## 项目结构

```text
contract_review_agent/
- api/
- core/
- docs/
- models/
- repositories/
- schemas/
- services/
- static/
- tests/
- data/
- .env.example
- .dockerignore
- Dockerfile
- main.py
- pytest.ini
- requirements.txt
- README.md
```

## 目录职责

- `api/`
  负责 HTTP 路由和接口暴露。
- `core/`
  负责配置、依赖装配和全局初始化。
- `models/`
  定义 `Clause`、`ParsedDocument`、`RiskDetection`、`RiskAnalysis`、`Review` 等领域对象。
- `schemas/`
  定义 FastAPI 请求体与响应体的 Pydantic 模型。
- `services/parsers/`
  负责 PDF / DOCX / TXT / 图片文本抽取。
- `services/splitters/`
  负责按条款切分合同。
- `services/analyzers/`
  负责规则检测、检索增强和结构化风险分析。
- `services/llm/`
  当前使用确定性模板输出，后续可替换真实 LLM Provider。
- `repositories/`
  负责 SQLite 记录的存取。

更详细的架构说明见 [docs/architecture.md](docs/architecture.md)。

## 已实现风险类型

- `unilateral_exemption`
- `unilateral_termination`
- `excessive_liquidated_damages`
- `unilateral_interpretation`
- `one_sided_ip_assignment`
- `biased_dispute_resolution`

风险等级严格限定为：
- `high`
- `medium`
- `low`

## API

### `POST /api/review/upload`

上传合同文件并返回审查结果。

请求方式：`multipart/form-data`

字段：
- `file`

支持格式：
- `.pdf`
- `.docx`
- `.txt`
- 常见图片格式

### `POST /api/review/analyze`

直接提交合同文本并返回审查结果。

示例：

```json
{
  "document_name": "sample_contract.txt",
  "text": "??????"
}
```

### `GET /api/review/{review_id}`

获取单条审查记录详情。

### `GET /api/reviews`

获取审查历史列表。

支持参数：
- `limit`
- `offset`

## 返回结构

```json
{
  "review_id": "string",
  "document_id": "string",
  "document_name": "string",
  "summary": "string",
  "created_at": "2026-03-27T12:00:00+00:00",
  "risks": [
    {
      "clause_id": "clause_1",
      "clause_title": "??? ????",
      "clause_text": "...",
      "risk_type": "excessive_liquidated_damages",
      "risk_level": "high",
      "risk_reason": "...",
      "impact_analysis": "...",
      "suggestion": "...",
      "replacement_text": "..."
    }
  ]
}
```

## RAG 说明

当前版本已接入本地 Embedding RAG，并保留词法检索回退。

当前链路：
- `RuleEngine` 先识别风险类型
- `LegalKnowledgeProvider` 从 [docs/legal_knowledge_base.json](docs/legal_knowledge_base.json) 读取本地知识片段
- `SentenceTransformerEmbeddingProvider` 使用本地开源 embedding 模型生成向量
- `KnowledgeVectorIndex` 在 `data/rag/` 下持久化知识库索引
- `RetrievalService` 默认执行向量检索，并在 embedding 不可用时自动回退词法检索
- `PromptAnalyzer` 把检索到的知识片段注入风险分析

## 本地运行

安装依赖：

```bash
pip install -r requirements.txt
```

如果你的本机 `pip install -r requirements.txt` 被哈希校验或镜像策略拦截，也可以直接安装本地 embedding 关键依赖：

```bash
pip install numpy==1.26.4 sentence-transformers==3.0.1
```

如需本地环境变量文件：

```bash
copy .env.example .env
```

启动服务：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问地址：
- Swagger：`http://localhost:8000/docs`
- 前端页面：`http://localhost:8000/`
- Health Check：`http://localhost:8000/health`

## Docker

构建镜像：

```bash
docker build -t contract-review-agent .
```

启动容器：

```bash
docker run --rm -p 8000:8000 contract-review-agent
```

如需持久化 SQLite 数据，可以挂载 `data/` 目录：

```bash
docker run --rm -p 8000:8000 -v %cd%\data:/app/data contract-review-agent
```

## OCR 说明

如需解析图片合同，请在本机安装 Tesseract OCR。

Windows 下可以通过环境变量指定路径：

```bash
set CONTRACT_AGENT_TESSERACT_CMD=C:\Program Files\Tesseract-OCR	esseract.exe
```

## 测试

```bash
pytest -q
```

当前已覆盖：
- 文本分析
- 文件上传
- 历史记录查询
- 空文本请求
- 空文件上传
- 不支持的文件类型
- 不存在的记录查询
- 词法检索与向量检索回退
- 持久化索引构建与加载

当前回归结果：`43 passed`。

## Postman

已提供可直接导入的 Collection：
- [docs/postman_collection.json](docs/postman_collection.json)

建议在 Postman 中设置：
- `base_url = http://localhost:8000`
- `review_id` 由分析接口自动写入

## 样例与文档

- 样例合同：[docs/sample_contract.txt](docs/sample_contract.txt)
- 架构说明：[docs/architecture.md](docs/architecture.md)
- Postman Collection：[docs/postman_collection.json](docs/postman_collection.json)
- 本地知识库样本：[docs/legal_knowledge_base.json](docs/legal_knowledge_base.json)

## 后续迭代建议

- 把 `TemplateLLMClient` 替换成真实大模型调用
- 把当前 lexical retrieval 升级为 embedding + vector DB
- 为响应增加 `references` 字段
- 增加金额抽取、主体识别、期限抽取等能力
- 若需上线，再升级 PostgreSQL、对象存储和鉴权机制

## 本地 Embedding 说明

默认模型：`BAAI/bge-small-zh-v1.5`

新增环境变量：
- `CONTRACT_AGENT_RETRIEVAL_MODE=vector_with_lexical_fallback`
- `CONTRACT_AGENT_EMBEDDING_MODEL_NAME=BAAI/bge-small-zh-v1.5`
- `CONTRACT_AGENT_EMBEDDING_CACHE_DIR=data/embedding_cache`
- `CONTRACT_AGENT_RAG_INDEX_DIR=data/rag`
- `CONTRACT_AGENT_RAG_REBUILD_ON_START=false`
- `CONTRACT_AGENT_EMBEDDING_LOCAL_FILES_ONLY=true`

说明：
- 若本地已安装 `sentence-transformers` 且模型已缓存，系统会优先走向量检索。
- 默认 `CONTRACT_AGENT_EMBEDDING_LOCAL_FILES_ONLY=true`，避免首次启动时卡在联网下载模型。
- 若 embedding 依赖缺失或模型不可用，系统会自动回退到当前词法检索，不影响 API 可用性。
