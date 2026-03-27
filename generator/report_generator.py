"""
审查报告生成器
"""
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
import markdown
from datetime import datetime


@dataclass
class ReviewReport:
    """审查报告"""
    title: str
    file_name: str
    file_type: str
    summary: dict  # 统计摘要
    risks: List[dict]  # 风险列表
    suggestions: List[dict]  # 建议列表
    overall_rating: str  # 整体评级
    created_at: str


class ReportGenerator:
    """审查报告生成器"""

    def __init__(self):
        pass

    def generate_markdown_report(self, report: ReviewReport, output_path: str):
        """生成Markdown格式报告"""
        md_content = self._build_markdown(report)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

    def generate_html_report(self, report: ReviewReport, output_path: str):
        """生成HTML格式报告"""
        md_content = self._build_markdown(report)
        html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])

        # 添加样式
        styled_html = self._add_html_styles(html_content)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(styled_html)

    def generate_text_summary(self, report: ReviewReport) -> str:
        """生成文本摘要"""
        summary_parts = [
            f"合同审查报告摘要",
            f"=" * 40,
            f"",
            f"文件名：{report.title}",
            f"文件类型：{report.file_type}",
            f"生成时间：{report.created_at}",
            f"",
            f"风险统计：",
            f"  - 重大风险（红色）：{report.summary.get('red', 0)} 项",
            f"  - 中等风险（黄色）：{report.summary.get('yellow', 0)} 项",
            f"  - 建议优化（绿色）：{report.summary.get('green', 0)} 项",
            f"",
            f"整体评级：{report.overall_rating}",
        ]

        return "\n".join(summary_parts)

    def _build_markdown(self, report: ReviewReport) -> str:
        """构建Markdown报告内容"""
        md_lines = [
            f"# 合同风险审查报告",
            f"",
            f"**文件名**：{report.title}",
            f"**文件类型**：{report.file_type}",
            f"**生成时间**：{report.created_at}",
            f"",
            f"---",
            f"",
            f"## 风险统计",
            f"",
            f"| 风险等级 | 数量 |",
            f"|----------|------|",
            f"| 🔴 重大风险 | {report.summary.get('red', 0)} |",
            f"| 🟡 中等风险 | {report.summary.get('yellow', 0)} |",
            f"| 🟢 建议优化 | {report.summary.get('green', 0)} |",
            f"",
            f"**整体评级**：{report.overall_rating}",
            f"",
            f"---",
            f"",
            f"## 风险详情",
            f"",
        ]

        # 添加风险详情
        for i, risk in enumerate(report.risks, 1):
            level_emoji = {"red": "🔴", "yellow": "🟡", "green": "🟢"}.get(risk.get('level', 'green'), "🟢")
            md_lines.append(f"### {i}. {level_emoji} {risk.get('risk_type', '未知风险')}")
            md_lines.append(f"")
            md_lines.append(f"**风险等级**：{risk.get('level', 'green').upper()}")
            md_lines.append(f"")
            md_lines.append(f"**条款原文**：")
            md_lines.append(f"```")
            md_lines.append(f"{risk.get('clause_text', '')[:200]}...")
            md_lines.append(f"```")
            md_lines.append(f"")
            md_lines.append(f"**风险描述**：{risk.get('description', '')}")
            md_lines.append(f"")

            if risk.get('impact_party'):
                md_lines.append(f"**受影响方**：{risk.get('impact_party')}")
                md_lines.append(f"")

            if risk.get('legal_basis'):
                md_lines.append(f"**法律依据**：{risk.get('legal_basis')}")
                md_lines.append(f"")

        # 添加修改建议
        if report.suggestions:
            md_lines.append(f"---")
            md_lines.append(f"")
            md_lines.append(f"## 修改建议")
            md_lines.append(f"")

            for i, suggestion in enumerate(report.suggestions, 1):
                md_lines.append(f"### {i}. {suggestion.get('risk_type', '')}")
                md_lines.append(f"")
                md_lines.append(f"**修改理由**：{suggestion.get('reason', '')}")
                md_lines.append(f"")
                md_lines.append(f"**建议条款**：")
                md_lines.append(f"```")
                md_lines.append(f"{suggestion.get('suggested_clause', '')}")
                md_lines.append(f"```")
                md_lines.append(f"")

        # 添加页脚
        md_lines.append(f"---")
        md_lines.append(f"")
        md_lines.append(f"*本报告由合同审查风险Agent自动生成，仅供参考。如有法律问题，请咨询专业律师。*")

        return "\n".join(md_lines)

    def _add_html_styles(self, html_content: str) -> str:
        """为HTML添加样式"""
        styles = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>合同风险审查报告</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 { color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        h3 { color: #666; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f8f9fa; }
        pre { background: #f8f8f8; padding: 15px; border-radius: 5px; overflow-x: auto; }
        .red { color: #dc3545; font-weight: bold; }
        .yellow { color: #ffc107; font-weight: bold; }
        .green { color: #28a745; font-weight: bold; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #888; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        {content}
        <div class="footer">
            <p>本报告由合同审查风险Agent自动生成，仅供参考。如有法律问题，请咨询专业律师。</p>
        </div>
    </div>
</body>
</html>
"""
        return styles.format(content=html_content)

    def create_report(self, file_name: str, file_type: str,
                      risks: List[dict], suggestions: List[dict],
                      summary: dict, overall_rating: str) -> ReviewReport:
        """创建报告对象"""
        return ReviewReport(
            title=file_name,
            file_name=file_name,
            file_type=file_type,
            summary=summary,
            risks=risks,
            suggestions=suggestions,
            overall_rating=overall_rating,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
