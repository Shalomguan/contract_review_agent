"""SQLite-backed review repository."""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime

from models.review import Review, ReviewListFilters, ReviewListItem, RiskAnalysis, RiskReference
from services.storage.sqlite_db import SQLiteDatabase


class ReviewRepository:
    """Persist and query review aggregates."""

    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def save(self, review: Review) -> None:
        """Insert or replace a review record."""
        payload = {
            "review_id": review.review_id,
            "document_id": review.document_id,
            "document_name": review.document_name,
            "summary": review.summary,
            "document_text": review.document_text,
            "created_at": review.created_at.isoformat(),
            "risks": [asdict(risk) for risk in review.risks],
        }
        risk_counts = self._count_risks(review.risks)

        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO reviews (
                    review_id,
                    document_id,
                    document_name,
                    summary,
                    created_at,
                    risk_counts,
                    review_payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    review.review_id,
                    review.document_id,
                    review.document_name,
                    review.summary,
                    review.created_at.isoformat(),
                    json.dumps(risk_counts, ensure_ascii=False),
                    json.dumps(payload, ensure_ascii=False),
                ),
            )
            connection.commit()

    def get(self, review_id: str) -> Review | None:
        """Fetch one review by identifier."""
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT review_payload FROM reviews WHERE review_id = ?",
                (review_id,),
            ).fetchone()

        if row is None:
            return None
        return self._hydrate_review(json.loads(row["review_payload"]))

    def list(self, filters: ReviewListFilters | None = None, limit: int = 20, offset: int = 0) -> tuple[list[ReviewListItem], int]:
        """List compact review records for history queries."""
        filters = filters or ReviewListFilters()
        where_clause, params = self._build_list_filters(filters)

        query = [
            "SELECT review_id, document_id, document_name, summary, created_at, risk_counts, review_payload",
            "FROM reviews",
        ]
        if where_clause:
            query.append(where_clause)
        query.append("ORDER BY created_at DESC")
        query.append("LIMIT ? OFFSET ?")

        with self.database.connect() as connection:
            rows = connection.execute("\n".join(query), tuple([*params, limit, offset])).fetchall()
            total_row = connection.execute(
                "\n".join([
                    "SELECT COUNT(*) AS total",
                    "FROM reviews",
                    where_clause,
                ] if where_clause else [
                    "SELECT COUNT(*) AS total",
                    "FROM reviews",
                ]),
                tuple(params),
            ).fetchone()

        items: list[ReviewListItem] = []
        for row in rows:
            risk_counts = json.loads(row["risk_counts"])
            clause_title, clause_text = self._extract_history_clause(json.loads(row["review_payload"]))
            items.append(
                ReviewListItem(
                    review_id=row["review_id"],
                    document_id=row["document_id"],
                    document_name=row["document_name"],
                    summary=self._normalize_summary(row["summary"], risk_counts),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    risk_counts=risk_counts,
                    clause_title=clause_title,
                    clause_text=clause_text,
                )
            )
        return items, int(total_row["total"] if total_row else 0)

    def _build_list_filters(self, filters: ReviewListFilters) -> tuple[str, list[object]]:
        clauses: list[str] = []
        params: list[object] = []

        if filters.document_name:
            clauses.append("LOWER(document_name) LIKE ?")
            params.append(f"%{filters.document_name.lower()}%")

        if filters.date_from:
            clauses.append("created_at >= ?")
            params.append(filters.date_from.isoformat())

        if filters.date_to:
            clauses.append("created_at <= ?")
            params.append(filters.date_to.isoformat())

        if filters.risk_level:
            clauses.append("json_extract(risk_counts, '$." + filters.risk_level + "') > 0")

        if not clauses:
            return "", params
        return "WHERE " + " AND ".join(clauses), params

    def delete(self, review_id: str) -> bool:
        """Delete one review by identifier."""
        with self.database.connect() as connection:
            cursor = connection.execute(
                "DELETE FROM reviews WHERE review_id = ?",
                (review_id,),
            )
            connection.commit()
        return cursor.rowcount > 0

    def _hydrate_review(self, payload: dict) -> Review:
        risks = []
        for item in payload["risks"]:
            references = [RiskReference(**reference) for reference in item.get("references", [])]
            risks.append(
                RiskAnalysis(
                    clause_id=item["clause_id"],
                    clause_title=item["clause_title"],
                    clause_text=item["clause_text"],
                    risk_type=item["risk_type"],
                    risk_level=item["risk_level"],
                    risk_reason=item["risk_reason"],
                    impact_analysis=item["impact_analysis"],
                    suggestion=item["suggestion"],
                    replacement_text=item["replacement_text"],
                    references=references,
                )
            )
        return Review(
            review_id=payload["review_id"],
            document_id=payload["document_id"],
            document_name=payload["document_name"],
            summary=self._normalize_summary(payload["summary"], self._count_risks(risks)),
            document_text=payload.get("document_text", ""),
            risks=risks,
            created_at=datetime.fromisoformat(payload["created_at"]),
        )

    def _normalize_summary(self, summary: str, risk_counts: dict[str, int]) -> str:
        if not self._looks_garbled(summary):
            return summary

        risk_count = sum(risk_counts.values())
        if risk_count == 0:
            return "当前规则集未命中明显风险，建议仍由法务人员进行复核。"
        return (
            f"已识别出 {risk_count} 个风险点，"
            + f"其中 high {risk_counts.get('high', 0)} 个，"
            + f"medium {risk_counts.get('medium', 0)} 个，"
            + f"low {risk_counts.get('low', 0)} 个。"
        )

    def _extract_history_clause(self, payload: dict) -> tuple[str | None, str | None]:
        risks = payload.get("risks") or []
        if not risks:
            return None, None

        first_risk = risks[0]
        return first_risk.get("clause_title"), first_risk.get("clause_text")

    def _looks_garbled(self, summary: str) -> bool:
        if not summary:
            return True
        suspicious_markers = ("???", "�", "锛", "鈥")
        return any(marker in summary for marker in suspicious_markers)

    def _count_risks(self, risks: list[RiskAnalysis]) -> dict[str, int]:
        counts = {"high": 0, "medium": 0, "low": 0}
        for risk in risks:
            counts[risk.risk_level] += 1
        return counts
