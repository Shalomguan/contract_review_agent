"""SQLite-backed review repository."""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime

from models.review import Review, ReviewListItem, RiskAnalysis
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

    def list(self, limit: int = 20, offset: int = 0) -> list[ReviewListItem]:
        """List compact review records for history queries."""
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT review_id, document_id, document_name, summary, created_at, risk_counts
                FROM reviews
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()

        items: list[ReviewListItem] = []
        for row in rows:
            items.append(
                ReviewListItem(
                    review_id=row["review_id"],
                    document_id=row["document_id"],
                    document_name=row["document_name"],
                    summary=row["summary"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    risk_counts=json.loads(row["risk_counts"]),
                )
            )
        return items

    def _hydrate_review(self, payload: dict) -> Review:
        risks = [RiskAnalysis(**item) for item in payload["risks"]]
        return Review(
            review_id=payload["review_id"],
            document_id=payload["document_id"],
            document_name=payload["document_name"],
            summary=payload["summary"],
            risks=risks,
            created_at=datetime.fromisoformat(payload["created_at"]),
        )

    def _count_risks(self, risks: list[RiskAnalysis]) -> dict[str, int]:
        counts = {"high": 0, "medium": 0, "low": 0}
        for risk in risks:
            counts[risk.risk_level] += 1
        return counts

