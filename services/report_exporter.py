"""Review export rendering for markdown and HTML downloads."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from urllib.parse import quote

from models.review import Review


@dataclass(slots=True)
class ExportArtifact:
    filename: str
    media_type: str
    content: str


class ReviewExporter:
    """Render one review into downloadable markdown or HTML."""

    def export(self, review: Review, fmt: str) -> ExportArtifact:
        normalized = fmt.lower()
        if normalized == "markdown":
            return ExportArtifact(
                filename=self._build_filename(review.document_name, "md"),
                media_type="text/markdown; charset=utf-8",
                content=self._render_markdown(review),
            )
        if normalized == "html":
            return ExportArtifact(
                filename=self._build_filename(review.document_name, "html"),
                media_type="text/html; charset=utf-8",
                content=self._render_html(review),
            )
        raise ValueError("Unsupported export format.")

    def build_content_disposition(self, filename: str) -> str:
        return f"attachment; filename*=UTF-8''{quote(filename)}"

    def _build_filename(self, document_name: str, extension: str) -> str:
        stem = Path(document_name or "contract_review").stem or "contract_review"
        return f"{stem}-review.{extension}"

    def _render_markdown(self, review: Review) -> str:
        lines = [
            f"# 合同审查报告：{review.document_name}",
            "",
            "## 基本信息",
            "",
            f"- 审查记录 ID：{review.review_id}",
            f"- 文档 ID：{review.document_id}",
            f"- 创建时间：{review.created_at.isoformat()}",
            f"- 风险数量：{len(review.risks)}",
            "",
            "## 审查摘要",
            "",
            review.summary,
            "",
            "## 合同原文",
            "",
            review.document_text or "当前审查结果未提供合同原文。",
            "",
            "## 风险条目",
            "",
        ]
        if not review.risks:
            lines.extend(["当前未识别出明确风险条目。", ""])
            return "\n".join(lines)

        for index, risk in enumerate(review.risks, start=1):
            lines.extend([
                f"### {index}. {risk.clause_title}",
                "",
                f"- 风险类型：{risk.risk_type}",
                f"- 风险等级：{risk.risk_level}",
                f"- 条款编号：{risk.clause_id}",
                "",
                "**条款原文**",
                "",
                risk.clause_text or "无",
                "",
                "**风险原因**",
                "",
                risk.risk_reason or "无",
                "",
                "**影响分析**",
                "",
                risk.impact_analysis or "无",
                "",
                "**修改建议**",
                "",
                risk.suggestion or "无",
                "",
                "**替代文本**",
                "",
                risk.replacement_text or "无",
                "",
                "**参考依据**",
                "",
            ])
            if risk.references:
                for reference in risk.references:
                    lines.extend([
                        f"- {reference.title} | {reference.source}",
                        f"  - {reference.content}",
                    ])
            else:
                lines.append("- 当前没有命中的参考依据。")
            lines.append("")
        return "\n".join(lines)

    def _render_html(self, review: Review) -> str:
        risk_blocks: list[str] = []
        for index, risk in enumerate(review.risks, start=1):
            if risk.references:
                reference_items = "".join(
                    f"<li><strong>{escape(reference.title)}</strong> | {escape(reference.source)}<br>{escape(reference.content)}</li>"
                    for reference in risk.references
                )
            else:
                reference_items = "<li>当前没有命中的参考依据。</li>"
            risk_blocks.append(
                (
                    f'<section class="risk-card">'
                    f'<h3>{index}. {escape(risk.clause_title)}</h3>'
                    f'<div class="meta">{escape(risk.risk_level.upper())} | {escape(risk.risk_type)} | {escape(risk.clause_id)}</div>'
                    f'<div class="field"><h4>条款原文</h4><p>{escape(risk.clause_text).replace(chr(10), "<br>")}</p></div>'
                    f'<div class="field"><h4>风险原因</h4><p>{escape(risk.risk_reason).replace(chr(10), "<br>")}</p></div>'
                    f'<div class="field"><h4>影响分析</h4><p>{escape(risk.impact_analysis).replace(chr(10), "<br>")}</p></div>'
                    f'<div class="field"><h4>修改建议</h4><p>{escape(risk.suggestion).replace(chr(10), "<br>")}</p></div>'
                    f'<div class="field"><h4>替代文本</h4><p>{escape(risk.replacement_text).replace(chr(10), "<br>")}</p></div>'
                    f'<div class="field"><h4>参考依据</h4><ul>{reference_items}</ul></div>'
                    f'</section>'
                )
            )
        if not risk_blocks:
            risk_blocks.append('<section class="risk-card"><p>当前未识别出明确风险条目。</p></section>')

        return (
            '<!DOCTYPE html>'
            '<html lang="zh-CN">'
            '<head>'
            '<meta charset="UTF-8">'
            f'<title>合同审查报告 - {escape(review.document_name)}</title>'
            '<style>'
            'body { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; margin: 0; background: #f5f7fa; color: #15202b; }'
            '.page { max-width: 1080px; margin: 0 auto; padding: 32px 24px 48px; }'
            '.panel { background: #fff; border: 1px solid #d9e0e7; border-radius: 18px; padding: 24px; margin-bottom: 18px; }'
            'h1, h2, h3, h4 { margin: 0 0 12px; }'
            '.meta { color: #5d6b7a; font-size: 14px; margin-bottom: 12px; }'
            '.summary { line-height: 1.8; white-space: pre-wrap; }'
            '.document-text { white-space: pre-wrap; line-height: 1.8; background: #f8fafc; border: 1px solid #d9e0e7; border-radius: 14px; padding: 16px; }'
            '.risk-card { border: 1px solid #d9e0e7; border-radius: 16px; padding: 18px; margin-top: 16px; background: #fcfdff; }'
            '.field { margin-top: 14px; }'
            '.field p { margin: 0; line-height: 1.8; white-space: pre-wrap; }'
            'ul { margin: 0; padding-left: 20px; line-height: 1.8; }'
            '</style>'
            '</head>'
            '<body>'
            '<div class="page">'
            '<section class="panel">'
            f'<h1>合同审查报告：{escape(review.document_name)}</h1>'
            f'<div class="meta">审查记录 ID：{escape(review.review_id)} | 文档 ID：{escape(review.document_id)} | 创建时间：{escape(review.created_at.isoformat())}</div>'
            '</section>'
            '<section class="panel">'
            '<h2>审查摘要</h2>'
            f'<div class="summary">{escape(review.summary)}</div>'
            '</section>'
            '<section class="panel">'
            '<h2>合同原文</h2>'
            f'<div class="document-text">{escape(review.document_text or "当前审查结果未提供合同原文。")}</div>'
            '</section>'
            '<section class="panel">'
            '<h2>风险条目</h2>'
            + ''.join(risk_blocks) +
            '</section>'
            '</div>'
            '</body>'
            '</html>'
        )
