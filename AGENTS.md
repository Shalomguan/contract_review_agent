# AGENTS.md

## 项目说明 (Project Overview)

这是一个合同审查风险Agent，用于识别合同中的潜在法律风险并生成修改建议。

This project is a contract risk review agent that detects legal risks and generates revision suggestions.

---

## 输出规范 (Output Schema)

风险等级必须是：

- high
- medium
- low

Risk levels must be strictly one of:

- high
- medium
- low

---

## 编码规则 (Coding Rules)

- 使用 Python + FastAPI
- 不要破坏现有 API
- 所有输出必须结构化 JSON
- Use Python + FastAPI
- Do not break existing APIs
- All outputs must be structured JSON

---

## 语言要求 (Language Rules)

- 默认使用中文回答用户
- 代码注释使用英文
- API字段使用英文
- Respond to users in Chinese
- Use English for code comments
- Use English for API fields

---

## 风险识别规则 (Risk Detection Rules)

必须识别以下风险：

- 单方免责
- 单方解除权
- 违约金过高
- 知识产权不公平
- 仲裁/法院偏向一方

Must detect:

- unilateral liability exemption
- unilateral termination
- excessive penalties
- unfair IP ownership
- biased dispute resolution
