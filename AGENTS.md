# AGENTS.md

## Project Overview

本项目是一个基于大语言模型（LLM）的合同审查风险 Agent，用于：

- 自动解析合同文本
- 识别潜在法律风险条款
- 对风险进行分级（high / medium / low）
- 生成风险分析与修改建议
- 输出结构化审查报告
- 支持历史审查记录管理

This project is a contract risk review agent powered by LLMs.

---

## Core Objectives

系统必须具备以下核心能力：

1. 文件解析（PDF / DOCX / TXT / 图片）
2. 条款切分（Clause Segmentation）
3. 风险识别（Rule + LLM）
4. 风险分级（high / medium / low）
5. 修改建议生成
6. 结构化输出
7. 审查记录存储与检索

---

## Architecture Rules

### 强制分层结构

- api/                 FastAPI 路由
- core/                配置、常量
- models/              数据库模型
- schemas/             Pydantic模型
- services/
  - parsers/           文件解析
  - splitters/         条款切分
  - analyzers/         风险识别
  - llm/               Prompt 和 LLM调用
  - rag/               检索增强（预留）
  - storage/           审查记录
- repositories/        数据访问层
- tests/
- docs/

### 禁止行为

- 不允许把所有逻辑写在一个文件里
- 不允许在 API 层写业务逻辑
- 不允许直接返回非结构化文本
- 不允许硬编码风险结果

---

## Output Schema (STRICT)

所有风险输出必须严格遵循以下结构：

{
  "document_id": "string",
  "document_name": "string",
  "summary": "string",
  "risks": [
    {
      "clause_id": "string",
      "clause_title": "string",
      "clause_text": "string",
      "risk_type": "string",
      "risk_level": "high | medium | low",
      "risk_reason": "string",
      "impact_analysis": "string",
      "suggestion": "string",
      "replacement_text": "string"
    }
  ]
}

### 强约束

- risk_level 只能是：

  - high
  - medium
  - low
- 不允许输出其他等级

---

## Risk Detection Rules

系统必须优先识别以下风险：

### 高风险（必须识别）

- 单方免责
- 单方解除权
- 违约金极高（例如超过20%或每日比例异常）
- 知识产权完全归一方
- 解释权归一方
- 仲裁或法院严重偏向一方
- 一方单独决定是否付款

### 中风险

- 违约责任不对等
- 保密条款无限期
- 提前解约成本过高
- 权利义务不对等

### 低风险

- 表述模糊
- 缺乏定义
- 条款不完整

---

## LLM Prompt Rules

- 输出必须为结构化 JSON
- 不允许只输出自然语言
- 每个风险必须单独分析
- 不允许遗漏 clause_text
- 必须基于原文分析，不允许编造

---

## RAG Extension

预留接口：

- legal_knowledge_provider
- retrieval_service
- reranker

MVP 阶段：

- 不实现复杂 RAG
- 保留扩展能力

---

## API Design Rules

必须实现以下接口：

- POST /api/review/upload
- POST /api/review/analyze
- GET /api/review/{id}
- GET /api/reviews

要求：

- 使用 schema 定义输入输出
- 返回结构必须一致
- 错误必须标准化

---

## Testing Rules

必须包含：

- parser 测试
- splitter 测试
- analyzer 测试
- API 基础测试

评测重点：

- 风险识别召回率
- 误报率
- 分级准确性

---

## Coding Rules

- 使用 Python + FastAPI
- 使用 Pydantic
- 函数职责单一
- 命名清晰
- 避免超大函数
- 必要时写英文注释

禁止：

- 伪代码
- 未实现函数
- 吞异常
- 魔法字符串

---

## Language Rules

- 用户交互使用中文
- 代码使用英文
- 注释使用英文
- API字段使用英文

---

## Agent Behavior Rules

当修改代码时：

1. 先分析项目结构
2. 只修改相关模块
3. 不要重写整个项目
4. 输出修改文件清单
5. 说明修改原因
6. 提供运行验证方法

如果代码混乱：

优先重建模块，而不是修补

---

## MVP Priority

优先实现：

1. 文件解析
2. 条款切分
3. 风险识别
4. JSON输出
5. API跑通
6. 基础测试

后续再实现：

- RAG
- 前端
- 性能优化

---

## Final Rule

始终优先保证简单、正确、可运行，而不是复杂设计
