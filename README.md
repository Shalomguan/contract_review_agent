# Contract Review Risk Agent

## 项目简介

这是一个基于 FastAPI 的合同审查风险 Agent。

当前版本已经具备一条完整的可运行链路：

当前知识库已经升级为双层结构，当前共 56 条条目：

- 审查规则层：`review_rule`、`drafting_guidance`、`balanced_clause`
- 法律依据层：`legal_basis`

检索时会优先返回与风险类型最相关的知识条目，并在可能时同时带出审查规则和法律依据。前端会把 `references` 区分展示为“审查规则”或“法律依据”。


- 上传或粘贴合同文本
- 解析 PDF / DOCX / TXT / 图片
- 按条款切分合同
- 使用规则引擎识别风险
- 通过本地知识库和本地 embedding RAG 增强分析
- 输出结构化审查结果
- 保存历史记录并支持查询、筛选、删除

系统面向企业法务、律师和中小企业主，目标是快速完成初步合同风险审查，而不是替代正式法律意见。

## 当前能力

### 后端能力

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/review/upload`
- `POST /api/review/analyze`
- `GET /api/review/{review_id}`
- `GET /api/review/{review_id}/export`
- `DELETE /api/review/{review_id}`
- `GET /api/reviews`
- `GET /health`

### 文件支持

- PDF
- DOCX
- TXT
- 常见图片格式

### 历史记录能力

- 按文件名搜索
- 按风险等级筛选
- 按日期范围筛选
- 分页查询
- 单条删除

### 前端页面

- 登录页：`/login`
- 用户页：`/`
- 测试页：`/lab`

登录页用于注册和登录，用户页用于正常使用，测试页保留更完整的联调视图。

## 项目结构

```text
contract_review_agent/
├── api/
├── core/
├── docs/
├── models/
├── repositories/
├── schemas/
├── services/
├── static/
├── tests/
├── data/
├── .env.example
├── .dockerignore
├── Dockerfile
├── main.py
├── pytest.ini
├── requirements.txt
└── README.md
```

## 目录职责

- `api/`
  FastAPI 路由层，只处理协议和参数。
- `core/`
  配置、依赖装配、应用初始化。
- `models/`
  领域模型，例如 `Clause`、`RiskAnalysis`、`Review`。
- `schemas/`
  API 输入输出模型。
- `services/parsers/`
  文件解析。
- `services/splitters/`
  条款切分。
- `services/analyzers/`
  风险识别、知识检索、结构化分析。
- `services/llm/`
  Prompt 构建与当前模板化输出。
- `services/rag/`
  本地 embedding provider 和知识索引。
- `services/storage/`
  SQLite 基础存储支持。
- `repositories/`
  审查记录持久化和查询。
- `static/`
  用户页和测试页前端。
- `tests/`
  单元测试和 API 集成测试。

更详细的架构说明见 [docs/architecture.md](docs/architecture.md)。

## 已实现风险类型

### 高风险

- `unilateral_exemption`
- `unilateral_termination`
- `excessive_liquidated_damages`
- `unilateral_interpretation`
- `biased_dispute_resolution`
- `unilateral_change_right`
- `non_compete_or_exclusivity`

### 中风险

- `one_sided_ip_assignment`
- `payment_imbalance`
- `acceptance_unfairness`
- `confidentiality_imbalance`
- `delivery_or_notice_trap`
- `termination_penalty_unfairness`
- `liability_imbalance`

### 低风险

- `auto_renewal_trap`
- `missing_core_terms`

风险等级严格限定为：

- `high`
- `medium`
- `low`

## 鉴权与登录

当前版本已接入轻量用户鉴权，审查相关接口均要求 Bearer Token。

认证接口：

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

说明：

- 注册后会直接返回 `access_token`
- 登录成功后也会返回 `access_token`
- `/api/review/*` 和 `/api/reviews`、`DELETE /api/review/{review_id}` 都需要在请求头中携带：

```text
Authorization: Bearer <access_token>
```

前端页面：

- 登录页：`http://localhost:8000/login`
- 用户页：`http://localhost:8000/`
- 测试页：`http://localhost:8000/lab`

用户页未登录时会自动跳转到登录页；测试页仍保留内嵌登录区，便于联调。登录页注册时要求输入确认密码。

### 登录与审查完整流程

1. 打开登录页：`http://localhost:8000/login`
2. 首次使用时输入：
   - 用户名
   - 密码
   - 确认密码
3. 点击“注册并登录”，成功后会自动跳转到用户页 `/`
4. 后续使用可直接输入用户名和密码后点击“登录”
5. 登录成功后即可：
   - 在用户页提交合同文本
   - 上传文件进行审查
   - 查看和删除自己的历史记录
6. 如需通过 Postman 或脚本调用接口，先调用：
   - `POST /api/auth/login`
7. 从返回结果中取出 `access_token`，并在后续请求头中携带：

```text
Authorization: Bearer <access_token>
```

## API 说明

### `POST /api/review/upload`

上传合同文件并返回完整审查结果。

请求方式：

- `multipart/form-data`

字段：

- `file`

### `POST /api/review/analyze`

直接提交合同文本并返回完整审查结果。

示例：

```json
{
  "document_name": "input.txt",
  "text": "软件开发服务合同\n\n第一条 服务内容\n乙方负责为甲方开发内部管理系统。"
}
```

说明：

- `document_name` 仅作为提交来源字段使用
- 系统实际保存的名称会自动改写为时间戳格式，例如 `contract20260328-2238`

### `GET /api/review/{review_id}`

获取单条审查记录详情。

### `GET /api/review/{review_id}/export`

导出单条审查记录。

支持参数：

- `format=markdown`
- `format=html`

说明：

- 需要 Bearer Token
- 返回附件下载响应
- 可用于法务留档、邮件发送或二次加工

### `DELETE /api/review/{review_id}`

删除单条审查记录。

### `GET /api/reviews`

获取历史记录列表。

支持参数：

- `limit`
- `offset`
- `document_name`
- `date_from`
- `date_to`
- `risk_level`

### `GET /health`

用于查看服务状态和当前 RAG 模式。

返回示例：

```json
{
  "status": "ok",
  "rag_mode": "vector"
}
```

或：

```json
{
  "status": "ok",
  "rag_mode": "lexical_fallback"
}
```

## 返回结构

完整审查结果返回示例：

```json
{
  "review_id": "string",
  "document_id": "string",
  "document_name": "contract20260328-2238.txt",
  "summary": "共拆分 6 个条款，识别出 3 个风险点，其中 high 1 个，medium 1 个，low 1 个。",
  "document_text": "完整合同原文",
  "created_at": "2026-03-28T14:38:00+00:00",
  "risks": [
    {
      "clause_id": "clause_2",
      "clause_title": "第二条 付款安排",
      "clause_text": "甲方应在合同签订后三个工作日内支付全部预付款。",
      "risk_type": "payment_imbalance",
      "risk_level": "medium",
      "risk_reason": "付款安排明显偏向一方。",
      "impact_analysis": "可能导致对方承担不合理的现金流压力。",
      "suggestion": "将付款节点与里程碑或验收结果绑定。",
      "replacement_text": "甲方应在验收通过后五个工作日内支付对应阶段款项。",
      "references": [
        {
          "title": "付款条件合理性",
          "source": "通用合同审查规则",
          "content": "付款节点应与交付和验收闭环匹配。"
        }
      ]
    }
  ]
}
```

历史列表返回示例：

```json
{
  "items": [
    {
      "review_id": "string",
      "document_id": "string",
      "document_name": "contract20260328-2238.txt",
      "summary": "共拆分 6 个条款，识别出 3 个风险点，其中 high 1 个，medium 1 个，low 1 个。",
      "created_at": "2026-03-28T14:38:00+00:00",
      "risk_counts": {
        "high": 1,
        "medium": 1,
        "low": 1
      }
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

## RAG 说明

当前版本已经接入本地开源 embedding RAG，并保留词法检索回退。

当前链路：

1. `RuleEngine` 先识别风险类型
2. `LegalKnowledgeProvider` 从 [docs/legal_knowledge_base.json](docs/legal_knowledge_base.json) 读取本地知识条目
3. `SentenceTransformerEmbeddingProvider` 使用本地模型生成向量
4. `KnowledgeVectorIndex` 在 `data/rag/` 下持久化索引
5. `RetrievalService` 优先执行向量检索，不可用时回退词法检索
6. `PromptAnalyzer` 把检索到的依据注入结构化风险分析

默认模型：

- `BAAI/bge-small-zh-v1.5`

## 本地运行

安装依赖：

```bash
pip install -r requirements.txt
```

如需单独安装本地 embedding 与 PDF 解析关键依赖：

```bash
pip install numpy==1.26.4 sentence-transformers==3.0.1 pypdf==4.1.0
```

复制环境变量模板：

```bash
copy .env.example .env
```

启动服务：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问地址：

- 登录页：`http://localhost:8000/login`
- 用户页：`http://localhost:8000/`
- 测试页：`http://localhost:8000/lab`
- Swagger：`http://localhost:8000/docs`
- Health：`http://localhost:8000/health`

## 本地 Embedding 使用说明

默认配置：

- `CONTRACT_AGENT_RETRIEVAL_MODE=vector_with_lexical_fallback`
- `CONTRACT_AGENT_EMBEDDING_MODEL_NAME=BAAI/bge-small-zh-v1.5`
- `CONTRACT_AGENT_EMBEDDING_CACHE_DIR=data/embedding_cache`
- `CONTRACT_AGENT_RAG_INDEX_DIR=data/rag`
- `CONTRACT_AGENT_RAG_REBUILD_ON_START=false`
- `CONTRACT_AGENT_EMBEDDING_LOCAL_FILES_ONLY=true`

说明：

- 如果本地缓存中已有模型，系统会启用向量检索
- 如果模型不可用，系统会自动回退到词法检索
- 可以通过 `/health` 查看当前模式

预下载模型到本地缓存：

```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-zh-v1.5', cache_folder='data/embedding_cache')"
```

验证本地模型可用：

```bash
python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('BAAI/bge-small-zh-v1.5', cache_folder='data/embedding_cache', local_files_only=True); print('ok', model.get_sentence_embedding_dimension())"
```

## OCR 说明

如需解析图片合同，请先安装 Tesseract OCR。

Windows 下可通过环境变量指定路径：

```bash
set CONTRACT_AGENT_TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

## Docker

构建镜像：

```bash
docker build -t contract-review-agent .
```

启动容器：

```bash
docker run --rm -p 8000:8000 contract-review-agent
```

如需持久化数据：

```bash
docker run --rm -p 8000:8000 -v %cd%\data:/app/data contract-review-agent
```

## 测试

运行测试：

```bash
pytest -q
```

当前覆盖包括：

- parser 测试
- splitter 测试
- analyzer 测试
- retrieval 测试
- API 集成测试
- 历史记录筛选、分页、删除测试
- 本地索引构建与回退测试

当前回归结果：

- `56 passed`

## Postman

已提供可直接导入的 Collection：

- [docs/postman_collection.json](docs/postman_collection.json)

建议设置：

- `base_url = http://localhost:8000`
- `review_id` 由分析接口自动写入

## 样例与文档

- 样例合同：[docs/sample_contract.txt](docs/sample_contract.txt)
- 架构说明：[docs/architecture.md](docs/architecture.md)
- 本地知识库：[docs/legal_knowledge_base.json](docs/legal_knowledge_base.json)
- 知识库扩充模板：[docs/knowledge_base_template.md](docs/knowledge_base_template.md)
- Postman Collection：[docs/postman_collection.json](docs/postman_collection.json)

## 当前前端说明

### 登录页 `/login`

- 面向用户登录和注册
- 登录成功后自动跳转到用户页

### 用户页 `/`

- 面向正常使用
- 未登录时自动跳转到登录页
- 支持文本分析、文件上传、历史检索
- 展示审查摘要、合同原文、风险条目
- 风险条目采用“摘要卡片 + 展开详情”

### 测试页 `/lab`

- 面向内部排查和联调
- 保留更完整的测试视图和内嵌登录区

## 最近修复

- 历史日期筛选按 `Asia/Shanghai` 本地日界线解释
- 历史文件名搜索同时支持系统生成名和原始提交名
- 历史详情支持对旧记录回退显示命中条款拼接文本
- PDF 解析代码已切换为优先使用 `pypdf`，并保留兼容 fallback

## 后续迭代建议

- 扩充本地知识库质量和覆盖面
- 将 `TemplateLLMClient` 替换为真实模型调用
- 继续优化前端移动端体验
- 增加报告导出
- 如需上线，再考虑 PostgreSQL、对象存储、鉴权和审计日志
