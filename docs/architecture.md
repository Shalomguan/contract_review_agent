# 架构说明

## 设计目标

- 先保证可运行、可测试、可扩展
- 将规则识别与结构化输出解耦
- 让解析、切分、分析、存储职责明确
- 为后续接入真实 LLM 和 RAG 预留接口，但 MVP 阶段不引入复杂依赖

## 核心流程

1. API 接收文本或文件
2. `DocumentParserFactory` 选择合适的解析器提取文本
3. `ContractSplitter` 将文本切分为条款
4. `RuleEngine` 识别明显风险
5. `RetrievalService` 提供静态法律知识提示
6. `PromptAnalyzer` 调用结构化 LLM 接口
7. `ReviewRepository` 将结果保存到 SQLite
8. API 返回统一 JSON

## 扩展点

### `services/analyzers/legal_knowledge_provider.py`

当前提供内置法律知识片段，后续可替换为：

- 法规知识库
- 案例库
- 向量数据库
- 知识图谱

### `services/analyzers/retrieval_service.py`

当前只做轻量封装，后续可扩展为：

- 召回排序
- 多路检索
- 重排序
- 引用片段裁剪

### `services/llm/base.py`

当前默认使用 `TemplateLLMClient` 返回稳定的结构化结果，后续可替换为：

- OpenAI
- Anthropic
- 企业内部模型

### `repositories/review_repository.py`

当前使用 SQLite，后续可以迁移到 PostgreSQL，而不影响 API 和服务层接口。
