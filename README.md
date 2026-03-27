# Contract Review Risk Agent MVP

一个可运行、可扩展、可测试的合同审查风险 Agent 最小版本。

当前版本聚焦四件事：
- 文件上传与文本解析
- 条款切分与规则识别
- 结构化风险输出
- 历史审查记录持久化

当前实现采用“规则 + 结构化模板”的 MVP 方案：
- 规则层负责识别明显高风险条款
- 分析层负责输出统一结构字段
- RAG 只保留扩展接口，不引入复杂依赖

## 项目结构

```text
contract_review_agent/
- api/                # FastAPI 应用与路由
- core/               # 配置与依赖装配
- docs/               # 架构说明、样例合同、Postman collection
- models/             # 领域模型
- repositories/       # 数据访问层
- schemas/            # API 输入输出模型
- services/           # 解析、切分、分析、存储
- static/             # 最小前端页面
- tests/              # 单元测试与接口测试
- data/               # 运行期 SQLite 数据
- .env.example        # 环境变量模板
- .dockerignore       # Docker 构建忽略文件
- Dockerfile          # 容器构建文件
- pytest.ini          # pytest 配置
- main.py             # 应用入口
- requirements.txt
- README.md
```

## 架构分层

- `api/`
  只暴露 REST API，不承载业务逻辑。
- `core/`
  管理配置和依赖装配。
- `models/`
  定义 `Clause`、`ParsedDocument`、`RiskAnalysis`、`Review` 等领域对象。
- `schemas/`
  定义 Pydantic 请求和响应模型。
- `services/parsers/`
  负责 `PDF / DOCX / TXT / 图片` 文本抽取。
- `services/splitters/`
  负责合同条款切分。
- `services/analyzers/`
  负责规则识别、法律知识获取、风险分析编排。
- `services/llm/`
  当前使用模板化稳定输出，后续可替换为真实 LLM Provider。
- `services/storage/`
  负责 SQLite 初始化。
- `repositories/`
  负责审查记录持久化与查询。

更详细说明见 [docs/architecture.md](docs/architecture.md)。

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

上传合同文件并返回结构化审查结果。

请求类型：
- `multipart/form-data`

字段：
- `file`

支持文件类型：
- `.pdf`
- `.docx`
- `.txt`
- 常见图片格式

### `POST /api/review/analyze`

直接提交合同文本并返回结构化审查结果。

请求体示例：

```json
{
  "document_name": "sample_contract.txt",
  "text": "合同文本内容"
}
```

### `GET /api/review/{review_id}`

获取单条历史审查记录。

### `GET /api/reviews`

获取历史审查列表。

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
      "clause_title": "第一条 付款安排",
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

## 本地运行

安装依赖：

```bash
pip install -r requirements.txt
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
- Swagger: `http://localhost:8000/docs`
- 最小前端：`http://localhost:8000/`
- 健康检查：`http://localhost:8000/health`

## OCR 说明

如果需要解析图片合同，请安装 Tesseract OCR。

Windows 可通过环境变量指定路径：

```bash
set CONTRACT_AGENT_TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

## 测试

运行全部测试：

```bash
pytest
```

或：

```bash
pytest -q
```

当前已覆盖：
- 正常文本分析
- 正常文件上传
- 历史记录查询
- 空文本请求
- 空文件上传
- 不支持的文件类型
- 查询不存在的记录

## Postman

仓库已提供可直接导入的 collection：
- `docs/postman_collection.json`

建议在 Postman 中配置：
- `base_url = http://localhost:8000`
- `review_id` 由分析接口自动写入

## Docker

构建镜像：

```bash
docker build -t contract-review-agent .
```

启动容器：

```bash
docker run --rm -p 8000:8000 contract-review-agent
```

如需保留 SQLite 数据文件，可挂载 `data/` 目录：

```bash
docker run --rm -p 8000:8000 -v %cd%\data:/app/data contract-review-agent
```

## 样例与文档

- 样例合同：`docs/sample_contract.txt`
- 架构说明：`docs/architecture.md`
- Postman collection：`docs/postman_collection.json`

## 后续扩展

- 将 `TemplateLLMClient` 替换为真实模型调用
- 将 `StaticLegalKnowledgeProvider` 升级为法规库或 RAG 检索层
- 增加主体识别、金额抽取、期限抽取
- 增加 PostgreSQL 和对象存储支持
