"""Pydantic request and response schemas."""
from datetime import datetime

from pydantic import BaseModel, Field

from models.review import Review, ReviewListItem, RiskAnalysis, RiskReference


class AnalyzeTextRequest(BaseModel):
    """Request body for text-based review analysis."""

    document_name: str = Field(..., min_length=1, max_length=255)
    text: str = Field(..., min_length=1)


class DeleteReviewResponse(BaseModel):
    """Delete operation result."""

    review_id: str
    deleted: bool


class RiskReferenceResponse(BaseModel):
    """Structured legal reference for API responses."""

    title: str
    source: str
    content: str
    category: str

    @classmethod
    def from_domain(cls, reference: RiskReference) -> "RiskReferenceResponse":
        return cls(
            title=reference.title,
            source=reference.source,
            content=reference.content,
            category=reference.category,
        )


class RiskItemResponse(BaseModel):
    """Structured risk item for API responses."""

    clause_id: str
    clause_title: str
    clause_text: str
    risk_type: str
    risk_level: str
    risk_reason: str
    impact_analysis: str
    suggestion: str
    replacement_text: str
    references: list[RiskReferenceResponse]

    @classmethod
    def from_domain(cls, risk: RiskAnalysis) -> "RiskItemResponse":
        return cls(
            clause_id=risk.clause_id,
            clause_title=risk.clause_title,
            clause_text=risk.clause_text,
            risk_type=risk.risk_type,
            risk_level=risk.risk_level,
            risk_reason=risk.risk_reason,
            impact_analysis=risk.impact_analysis,
            suggestion=risk.suggestion,
            replacement_text=risk.replacement_text,
            references=[RiskReferenceResponse.from_domain(item) for item in risk.references],
        )


class ReviewResponse(BaseModel):
    """Full review response."""

    review_id: str
    document_id: str
    document_name: str
    summary: str
    document_text: str
    risks: list[RiskItemResponse]
    created_at: datetime

    @classmethod
    def from_domain(cls, review: Review) -> "ReviewResponse":
        return cls(
            review_id=review.review_id,
            document_id=review.document_id,
            document_name=review.document_name,
            summary=review.summary,
            document_text=review.document_text,
            risks=[RiskItemResponse.from_domain(risk) for risk in review.risks],
            created_at=review.created_at,
        )


class ReviewListItemResponse(BaseModel):
    """Compact review item for history listing."""

    review_id: str
    document_id: str
    document_name: str
    summary: str
    created_at: datetime
    risk_counts: dict[str, int]

    @classmethod
    def from_domain(cls, item: ReviewListItem) -> "ReviewListItemResponse":
        return cls(
            review_id=item.review_id,
            document_id=item.document_id,
            document_name=item.document_name,
            summary=item.summary,
            created_at=item.created_at,
            risk_counts=item.risk_counts,
        )


class ReviewListResponse(BaseModel):
    """Paginated review list response."""

    items: list[ReviewListItemResponse]
    total: int
    limit: int
    offset: int

    @classmethod
    def from_domain(
        cls,
        items: list[ReviewListItem],
        total: int,
        limit: int,
        offset: int,
    ) -> "ReviewListResponse":
        return cls(
            items=[ReviewListItemResponse.from_domain(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )
