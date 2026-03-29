# 知识库扩充模板

这个模板用于扩充 [legal_knowledge_base.json](legal_knowledge_base.json)。

目标不是堆很多法规全文，而是围绕当前系统已有的 `risk_type`，补充高质量、可检索、可解释的审查知识条目。

## 一条知识条目的推荐结构

```json
{
  "id": "payment_imbalance_rule_001",
  "category": "review_rule",
  "risk_type": "payment_imbalance",
  "title": "付款节点应与验收或交付闭环匹配",
  "content": "如果合同要求对方在未完成交付、未达到里程碑或未通过验收前支付大部分价款，容易形成付款条件失衡风险。更合理的安排是将付款节点与交付成果、验收结果或明确的履约进度绑定。",
  "source": "通用合同审查规则",
  "keywords": ["付款", "预付款", "里程碑", "验收", "交付"],
  "jurisdiction": "CN",
  "updated_at": "2026-03-29"
}
```

## 字段说明

- `id`
  全局唯一，建议按 `risk_type + 类型 + 序号` 命名。
- `category`
  建议值：
  - `review_rule`
  - `drafting_guidance`
  - `balanced_clause`
  - `legal_basis`
- `risk_type`
  必须与当前系统已有风险类型一致。
- `title`
  一句话概括该知识条目的核心观点。
- `content`
  用完整、可读、可检索的自然语言描述风险逻辑或修改思路。
- `source`
  知识来源名称，例如“通用合同审查规则”“企业法务审查要点”“《中华人民共和国民法典》相关规则（概括）”。
- `keywords`
  便于词法兜底检索的关键词列表。
- `jurisdiction`
  可选，当前建议统一先用 `CN`。
- `updated_at`
  可选，建议使用 `YYYY-MM-DD`。

## 双层知识结构建议

当前知识库建议按两层组织，而不是只堆一类内容。

### 1. 审查规则层

适合直接支撑风险分析、修改建议和替代表达。

- `review_rule`
  用于表达风险识别逻辑和审查判断。
- `drafting_guidance`
  用于表达修改方向和起草要点。
- `balanced_clause`
  用于表达更平衡的条款写法。

### 2. 法律依据层

- `legal_basis`
  用于表达较稳定的法律原则、合同规则和效力边界。

注意：`legal_basis` 更适合写“法规原则的概括”和“合同法理的总结”，不要大段照搬法条全文。

### 推荐组合

同一个 `risk_type`，尽量同时具备：

1. 一条 `review_rule`
2. 一条 `drafting_guidance` 或 `balanced_clause`
3. 一条 `legal_basis`

这样检索结果既能给出审查经验，也能给出较稳定的法律依据。

## 推荐扩充顺序

优先按现有 `risk_type` 一类一类补，不要先引入大而杂的法规全文。

### 第一批建议优先扩充

- `payment_imbalance`
- `acceptance_unfairness`
- `confidentiality_imbalance`
- `unilateral_change_right`
- `termination_penalty_unfairness`
- `biased_dispute_resolution`

### 每个 risk_type 至少补 3 类内容

1. 审查规则
- 为什么这是风险
- 常见风险表现形式

2. 修改建议
- 应该往什么方向改
- 双方权利义务如何拉平

3. 平衡表达或法律依据
- 可接受的条款写法是什么样
- 或者该类条款背后的稳定法律原则

## 可直接复制的模板

```json
{
  "id": "<唯一ID>",
  "category": "review_rule",
  "risk_type": "<已有risk_type>",
  "title": "<一句话标题>",
  "content": "<完整知识内容，2-5句，适合检索和解释>",
  "source": "<来源名称>",
  "keywords": ["<关键词1>", "<关键词2>", "<关键词3>"],
  "jurisdiction": "CN",
  "updated_at": "2026-03-29"
}
```

### `legal_basis` 示例

```json
{
  "id": "unilateral_exemption_basis_001",
  "category": "legal_basis",
  "risk_type": "unilateral_exemption",
  "title": "格式条款免责需履行提示说明义务",
  "content": "以格式条款减轻或者免除提供方责任、加重对方责任或者限制对方主要权利的，应当进行合理提示和说明。未尽提示说明义务时，相关免责安排存在不被采纳的风险。",
  "source": "《中华人民共和国民法典》格式条款规则（概括）",
  "keywords": ["格式条款", "免责", "提示说明", "主要权利"],
  "jurisdiction": "CN",
  "updated_at": "2026-03-29"
}
```

## 编写原则

- 不要只写关键词，要写完整内容。
- 不要整段照搬法条全文，优先写“审查可用”的解释性内容。
- 一条知识只表达一个核心观点，不要把多个风险混在一起。
- `keywords` 要覆盖常见合同说法和变体表达。
- `title` 要短，`content` 要清楚，避免空泛表述。
- `legal_basis` 应优先写法律原则的概括，不要冒充精准逐条法条引用。

## 不建议的做法

- 直接塞整本法典或大量长篇案例。
- 一条知识里同时覆盖多个不相干风险。
- 只有结论，没有修改方向。
- 只有法规摘录，没有合同审查语境。

## 推荐工作流

1. 先选一个 `risk_type`
2. 为该类型补 3 到 5 条高质量知识
3. 至少覆盖“审查规则 + 法律依据”两个层面
4. 补充对应关键词
5. 本地重新启动服务或重建索引
6. 用真实合同样本验证 `references` 是否更相关
