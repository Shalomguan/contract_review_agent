"""
提示词库
"""

RISK_DETECTION_PROMPT = """你是一位专业的中国法律顾问。请分析以下合同条款，识别潜在的法律风险：

---
{clause_text}
---

请以JSON格式返回分析结果：
{{
  "risk_type": "风险类型（如：违约金过高、保密条款不明确等）",
  "risk_level": "red/yellow/green",
  "description": "风险描述",
  "impact_party": "甲方/乙方/双方",
  "confidence": 0.0-1.0之间的置信度
}}

风险类型包括：
- 违约金过高
- 保密条款不明确
- 争议解决不利
- 责任边界模糊
- 终止条款不合理
- 支付条款风险
- 不可抗力条款不合理
- 格式条款无效风险

如果条款没有明显风险，请返回：
{{
  "risk_type": "无",
  "risk_level": "green",
  "description": "该条款未发现明显法律风险",
  "impact_party": "中立",
  "confidence": 1.0
}}"""


SUGGESTION_GENERATION_PROMPT = """基于以下合同条款和相关法律条文，请生成专业的修改建议：

---
合同条款：
{clause_text}
---

风险类型：{risk_type}
{found_parties}
相关法律条文：
{retrieved_laws}

请提供一个符合中国法律规定的修改建议，回复格式如下：

**修改理由**：{{简要说明为什么需要修改}}

**示范条款**：
{{可直接使用的修改后条款文本}}

**法律依据**：{{引用的法律条款}}"""


OVERALL_REVIEW_PROMPT = """请对以下合同审查结果进行总结：

风险统计：
- 红色（重大风险）：{red_count} 项
- 黄色（中等风险）：{yellow_count} 项
- 绿色（建议优化）：{green_count} 项

风险详情：
{risks_detail}

请提供：
1. 整体风险评估概述（一段话）
2. 需要重点关注的重大风险（按优先级列出，最多3项）
3. 修改优先级建议（高/中/低）
4. 合同整体可签性评估（建议签/建议改后签/不建议签）"""


CLAUSE_CATEGORIZATION_PROMPT = """请将以下合同条款分类：

---
{clause_text}
---

可选类别：
- 甲方权利义务
- 乙方权利义务
- 违约金/赔偿
- 保密义务
- 知识产权
- 争议解决
- 不可抗力
- 合同变更/终止
- 付款条件
- 其他

请返回JSON格式：
{{"category": "类别名称", "confidence": 0.0-1.0}}"""
