"""
合同审查风险Agent - FastAPI入口
"""
import os
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings, ensure_directories
from parser import PDFParser, DocxParser, OCRParser, ParsedDocument
from risk_analyzer import RiskDetector, RiskClassifier, ImpactAnalyzer
from rag import Retriever, VectorStore
from generator import ClauseGenerator, ReportGenerator
from history import ReviewDatabase, ReviewRecord, ReviewSearch

# 确保目录存在
ensure_directories()

# 创建应用
app = FastAPI(
    title="合同审查风险Agent",
    description="基于大语言模型的智能法律辅助工具",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# 初始化组件
detector = RiskDetector()
classifier = RiskClassifier()
impact_analyzer = ImpactAnalyzer()
retriever = Retriever()
clause_generator = ClauseGenerator()
report_generator = ReportGenerator()
db = ReviewDatabase()
search = ReviewSearch(db)


# 数据模型
class RiskItem(BaseModel):
    clause_text: str
    risk_type: str
    level: str
    description: str
    impact_party: str
    legal_basis: Optional[str] = None


class ReviewRequest(BaseModel):
    file_name: str
    text: str
    file_type: str


class ReviewResponse(BaseModel):
    file_name: str
    overall_rating: str
    summary: dict
    risks: List[RiskItem]
    suggestions: List[dict]


@app.get("/", response_class=HTMLResponse)
async def root():
    """返回前端页面"""
    html_path = Path(__file__).parent / "static" / "index.html"
    with open(html_path, 'r', encoding='utf-8') as f:
        return f.read()


@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    # 初始化向量库
    try:
        vector_store = VectorStore()
        vector_store.initialize()
    except Exception as e:
        print(f"向量库初始化警告: {e}")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "合同审查风险Agent",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/review")
async def review_contract(
    file: UploadFile = File(...),
    contract_text: Optional[str] = Form(None)
):
    """
    上传并审查合同

    支持格式：PDF、Word、图片(OCR)
    """
    try:
        # 保存上传的文件
        file_path = settings.PROJECT_ROOT / "uploads" / file.filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 解析文档
        file_ext = Path(file.filename).suffix.lower()
        parsed_doc = parse_document(str(file_path), file_ext, contract_text)

        # 检测风险
        detected_risks = detector.detect(parsed_doc.text)

        # 分类和影响分析
        analyzed_risks = []
        for risk in detected_risks:
            classification = classifier.classify(risk.risk_type, risk.clause_text)
            impact = impact_analyzer.analyze(risk.risk_type, risk.clause_text)

            analyzed_risks.append({
                "clause_text": risk.clause_text[:300],
                "risk_type": risk.risk_type,
                "level": classification.risk_level.value,
                "description": classification.description,
                "impact_party": impact.affected_party.value,
                "legal_basis": classification.legal_basis,
                "confidence": risk.confidence
            })

        # 批量生成建议
        risk_items = [
            {"clause_text": r["clause_text"], "risk_type": r["risk_type"]}
            for r in analyzed_risks
        ]
        suggestions = clause_generator.generate_batch_suggestions(risk_items)

        # 统计
        summary = classifier.classify_batch([
            type('obj', (object,), {'risk_level': r['level']}) for r in analyzed_risks
        ])

        # 评级
        overall_rating = "建议签"
        if summary["red"] > 0:
            overall_rating = "建议修改后签"
        if summary["red"] >= 3:
            overall_rating = "不建议签"

        # 保存记录
        record_data = {
            "file_name": file.filename,
            "file_type": parsed_doc.file_type or file_ext[1:],
            "file_path": str(file_path),
            "overall_rating": overall_rating,
            "risk_summary": summary,
            "risks_detail": analyzed_risks,
            "suggestions": [
                {
                    "risk_type": s.risk_type,
                    "reason": s.reason,
                    "suggested_clause": s.suggested_clause,
                    "legal_basis": s.legal_basis
                }
                for s in suggestions
            ]
        }
        db.add_record(record_data)

        # 返回结果
        return ReviewResponse(
            file_name=file.filename,
            overall_rating=overall_rating,
            summary=summary,
            risks=[RiskItem(**r) for r in analyzed_risks],
            suggestions=[
                {
                    "risk_type": s.risk_type,
                    "reason": s.reason,
                    "suggested_clause": s.suggested_clause,
                    "legal_basis": s.legal_basis
                }
                for s in suggestions
            ]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/review/text")
async def review_text(request: ReviewRequest):
    """
    直接审查文本内容
    """
    try:
        # 检测风险
        detected_risks = detector.detect(request.text)

        # 分类和影响分析
        analyzed_risks = []
        for risk in detected_risks:
            classification = classifier.classify(risk.risk_type, risk.clause_text)
            impact = impact_analyzer.analyze(risk.risk_type, risk.clause_text)

            analyzed_risks.append({
                "clause_text": risk.clause_text[:300],
                "risk_type": risk.risk_type,
                "level": classification.risk_level.value,
                "description": classification.description,
                "impact_party": impact.affected_party.value,
                "legal_basis": classification.legal_basis,
                "confidence": risk.confidence
            })

        # 统计
        summary = classifier.classify_batch([
            type('obj', (object,), {'risk_level': r['level']}) for r in analyzed_risks
        ])

        # 评级
        overall_rating = "建议签"
        if summary["red"] > 0:
            overall_rating = "建议修改后签"

        return {
            "overall_rating": overall_rating,
            "summary": summary,
            "risks": analyzed_risks
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
async def get_history(limit: int = 20, offset: int = 0):
    """获取审查历史"""
    records = db.get_all_records(limit=limit, offset=offset)
    return {"records": [r.__dict__ for r in records]}


@app.get("/history/{record_id}")
async def get_history_detail(record_id: int):
    """获取审查详情"""
    record = db.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record.__dict__


@app.get("/history/search")
async def search_history(
    q: Optional[str] = None,
    file_type: Optional[str] = None,
    risk_level: Optional[str] = None
):
    """搜索审查记录"""
    filters = {}
    if file_type:
        filters['file_type'] = file_type
    if risk_level:
        filters['risk_level'] = risk_level

    records = search.search(q or "", filters)
    return {"records": [r.__dict__ for r in records]}


@app.get("/statistics")
async def get_statistics():
    """获取统计数据"""
    return db.get_statistics()


@app.post("/report/{record_id}")
async def generate_report(record_id: int, format: str = "markdown"):
    """生成审查报告"""
    record = db.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    # 创建报告
    report = report_generator.create_report(
        file_name=record.file_name,
        file_type=record.file_type,
        risks=record.risks_detail,
        suggestions=record.suggestions,
        summary=record.risk_summary,
        overall_rating=record.overall_rating
    )

    # 生成文件
    output_dir = settings.PROJECT_ROOT / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    if format == "markdown":
        output_path = output_dir / f"{record.file_name}_review.md"
        report_generator.generate_markdown_report(report, str(output_path))
    else:
        output_path = output_dir / f"{record.file_name}_review.html"
        report_generator.generate_html_report(report, str(output_path))

    return FileResponse(
        str(output_path),
        media_type="text/markdown" if format == "markdown" else "text/html",
        filename=output_path.name
    )


def parse_document(file_path: str, file_ext: str, text: Optional[str] = None) -> ParsedDocument:
    """解析文档"""
    if text:
        # 如果提供了文本，直接使用
        return ParsedDocument(text=text, file_type=file_ext[1:])

    if file_ext == '.pdf':
        parser = PDFParser()
    elif file_ext in ['.docx', '.doc']:
        parser = DocxParser()
    elif file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
        parser = OCRParser()
    else:
        raise ValueError(f"不支持的文件格式: {file_ext}")

    return parser.parse(file_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
