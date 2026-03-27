# 合同审查风险Agent

基于大语言模型（MiniMax）的智能法律辅助工具，帮助企业法务人员、律师及中小企业主快速识别合同中的潜在风险点并生成修改建议。

## 功能特性

### 核心功能

- **合同解析**：支持 PDF、Word、图片（OCR）多种格式
- **风险识别**：自动识别违约金过高、保密条款不明确、争议解决不利等风险
- **风险分级**：红色（重大风险）、黄色（中等风险）、绿色（建议优化）
- **影响分析**：评估风险对甲方/乙方的具体影响
- **建议生成**：基于法律知识库生成专业修改建议
- **历史管理**：审查记录存档，支持检索和回溯
- **报告导出**：生成 Markdown/HTML 格式审查报告

### 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户交互层 (FastAPI)                   │
├─────────────────────────────────────────────────────────┤
│  合同上传 → 解析模块 → 风险识别 → RAG检索 → 建议生成 → 报告导出 │
├─────────────────────────────────────────────────────────┤
│  历史管理模块（SQLite + FAISS向量库）                      │
└─────────────────────────────────────────────────────────┘
```

## 安装部署

### 环境要求

- Python 3.10+
- Tesseract OCR（用于图片识别）

### 1. 克隆项目

```bash
git clone <repository-url>
cd contract_review_agent
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

**注意**：本项目使用 `langchain-anthropic` 调用 MiniMax 的 Anthropic API 兼容接口。

### 4. 安装 Tesseract OCR（Windows）

下载并安装 [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)，安装时选择中文语言包。

安装后，在代码中指定路径（如果非默认路径）：

```python
# parser/ocr_parser.py
ocr_parser = OCRParser(tesseract_cmd=r"C:\Program Files\Tesseract-OCR\tesseract.exe")
```

### 5. 配置 MiniMax API

编辑 `.env` 文件（项目根目录下，如果不存在请创建）：

```env
# MiniMax API配置
MINIMAX_API_KEY=your-api-key-here
MINIMAX_BASE_URL=https://api.minimaxi.com/anthropic
MINIMAX_MODEL=MiniMax-M2.7
```

**API Key 获取**：访问 [MiniMax Platform](https://platform.minimaxi.com) 注册后获取。

**支持的模型**：`MiniMax-M2.7`、`MiniMax-M2.7-highspeed`、`MiniMax-M2.5` 等。

## 快速开始

### 启动服务

```bash
python main.py
```

或使用 uvicorn：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API 接口

#### 1. 上传并审查合同

```bash
curl -X POST "http://localhost:8000/review" \
  -F "file=@contract.pdf"
```

#### 2. 直接审查文本

```bash
curl -X POST "http://localhost:8000/review/text" \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "合同.txt",
    "text": "甲方应在签订合同后3日内支付全额定金，如甲方违约，定金不予退还。",
    "file_type": "txt"
  }'
```

#### 3. 获取审查历史

```bash
curl "http://localhost:8000/history?limit=10"
```

#### 4. 搜索审查记录

```bash
curl "http://localhost:8000/history/search?q=租赁&risk_level=red"
```

#### 5. 生成审查报告

```bash
curl "http://localhost:8000/report/1?format=markdown" -o report.md
```

### Web 界面

启动服务后，访问 http://localhost:8000 查看可视化界面。

功能包括：
- **合同审查**：上传 PDF/Word/图片文件或直接粘贴文本
- **历史记录**：查看历史审查记录，支持搜索和详情查看
- **统计数据**：查看审查统计和风险分布
- **报告下载**：支持下载 Markdown 和 HTML 格式的审查报告

## 项目结构

```
contract_review_agent/
├── main.py                 # FastAPI入口
├── config.py               # 配置管理
├── requirements.txt        # 依赖清单
├── parser/                 # 合同解析模块
│   ├── base.py            # 解析器基类
│   ├── pdf_parser.py      # PDF解析器
│   ├── docx_parser.py     # Word解析器
│   └── ocr_parser.py      # OCR解析器
├── risk_analyzer/          # 风险识别模块
│   ├── detector.py        # 风险检测器
│   ├── classifier.py      # 风险分级器
│   └── impact_analyzer.py # 影响分析器
├── rag/                    # RAG增强模块
│   ├── vector_store.py    # FAISS向量库
│   ├── retriever.py       # 检索器
│   ├── prompt_builder.py  # 提示词构建
│   └── embedding.py       # 嵌入模型
├── generator/              # 建议生成模块
│   ├── clause_generator.py    # 修改建议生成
│   └── report_generator.py     # 报告生成
├── history/                # 历史管理模块
│   ├── db.py              # 数据库操作
│   └── search.py          # 检索接口
├── prompts/                # 提示词库
│   └── risk_prompts.py
└── knowledge_base/         # 法律知识库
    └── legal_clauses.json
```

## 使用示例

### Python SDK 用法

```python
from parser import PDFParser
from risk_analyzer import RiskDetector, RiskClassifier, ImpactAnalyzer
from generator import ClauseGenerator

# 1. 解析合同
parser = PDFParser()
doc = parser.parse("contract.pdf")

# 2. 检测风险
detector = RiskDetector()
risks = detector.detect(doc.text)

# 3. 分级风险
classifier = RiskClassifier()
for risk in risks:
    classification = classifier.classify(risk.risk_type, risk.clause_text)
    print(f"{risk.risk_type}: {classification.risk_level.value}")

# 4. 分析影响
impact_analyzer = ImpactAnalyzer()
for risk in risks:
    impact = impact_analyzer.analyze(risk.risk_type, risk.clause_text)
    print(f"受影响方: {impact.affected_party.value}")

# 5. 生成修改建议
generator = ClauseGenerator()
for risk in risks:
    suggestion = generator.generate_suggestion(risk.clause_text, risk.risk_type)
    print(suggestion.suggested_clause)
```

### 命令行用法

```python
# review.py
import asyncio
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

# 审查文件
with open("contract.pdf", "rb") as f:
    response = client.post("/review", files={"file": f})

print(response.json())
```

## 风险识别类型

| 风险类型 | 说明 | 法律依据 |
|---------|------|---------|
| 违约金过高 | 违约金金额或计算方式不合理 | 民法典第585条 |
| 保密条款不明确 | 保密范围、期限约定不清 | 民法典第501条 |
| 争议解决不利 | 管辖法院或仲裁机构选择不利 | 民事诉讼法第34条 |
| 责任边界模糊 | 责任范围、免责情形不明确 | 民法典第584条 |
| 终止条款不合理 | 单方解除权过大 | 民法典第562条 |
| 支付条款风险 | 预付款风险、付款期限不合理 | 民法典第628条 |

## 配置说明

### config.py 主要配置项

```python
# 风险等级阈值
RED_THRESHOLD = 0.8      # 红色风险阈值
YELLOW_THRESHOLD = 0.5   # 黄色风险阈值

# 向量库配置
EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_DIM = 1536

# 风险关键词
RISK_KEYWORDS = {
    "违约金": ["违约金", "滞纳金", "罚金"],
    "保密条款": ["保密", "机密", "泄露"],
    ...
}
```

## 数据库

审查记录存储在 SQLite 数据库中（`data/reviews.db`），包含以下字段：

- `file_name`: 文件名
- `file_type`: 文件类型
- `review_time`: 审查时间
- `overall_rating`: 整体评级
- `risk_summary`: 风险统计
- `risks_detail`: 风险详情
- `suggestions`: 修改建议

## 常见问题

### Q: MiniMax API 调用失败？

1. 检查 API Key 是否正确
2. 确认网络连接正常
3. 查看 API 配额是否用完

### Q: OCR 识别不准？

1. 确保图片清晰度足够
2. 检查 Tesseract 是否安装了中文语言包
3. 尝试使用更高质量的扫描件

### Q: 风险识别不准确？

1. 当前版本基于规则+LLM，可作为辅助工具
2. 重要合同建议咨询专业律师
3. 可以通过反馈不断优化模型

## 扩展开发

### 添加新的风险类型

```python
# risk_analyzer/detector.py
RISK_PATTERNS = {
    "新风险类型": [
        r"匹配正则表达式",
        ...
    ],
}
```

### 添加法律条款

编辑 `knowledge_base/legal_clauses.json`：

```json
{
  "clauses": [
    {
      "category": "新类别",
      "title": "条款标题",
      "content": "条款内容",
      "law_name": "法律法规名称",
      "article": "条款编号"
    }
  ]
}
```

### 更换嵌入模型

```python
# rag/embedding.py
class EmbeddingModel:
    def __init__(self):
        # 使用其他嵌入模型，如 m3e-base
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer('m3e-base')
```

## 免责声明

本工具仅供参考和学习使用，不能替代专业法律意见。对于重要合同，建议咨询专业律师进行审查。

## License

MIT License
