# 架构说明

## 设计目标

- 先保证可运行、可测试、可扩展
- 规则识别与结构化输出分离
- 解析、切分、分析、存储职责明确
- 为真实 LLM 和 RAG 留接口，但 MVP 不引入复杂依赖

## 核心流程

1. API 接收文本或文件
2. `DocumentParserFactory` 选择合适解析器提取文本
3. `ContractSplitter` 切分为结构化条款
4. `RuleEngine` 识别明显风险
5. `RetrievalService` 获取静态法律知识提示
6. `PromptAnalyzer` 调用 `StructuredLLMClient`
7. `ReviewRepository` 将结构化结果保存到 SQLite
8. API 返回统一 JSON

## 扩展点

- `services/analyzers/legal_knowledge_provider.py`
  用于替换为法规库、案例库、知识图谱或向量召回结果

- `services/analyzers/retrieval_service.py`
  当前只做代理封装，后续可加入召回排序和多路检索

- `services/llm/base.py`
  当前 `TemplateLLMClient` 提供确定性结构化输出，后续可以替换成 OpenAI、Anthropic 或企业内部模型

- `repositories/review_repository.py`
  当前使用 SQLite，后续可迁移到 PostgreSQL 而不影响上层接口

