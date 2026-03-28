"""Orchestration service for contract review workflows."""
from __future__ import annotations

from collections import Counter
from collections import defaultdict
from datetime import date, datetime, time, timezone
from pathlib import Path
from uuid import uuid4

from core.config import Settings
from models.review import ParsedDocument, Review, ReviewListFilters
from repositories.review_repository import ReviewRepository
from services.analyzers.risk_analyzer import RiskAnalyzer
from services.parsers.base import DocumentParseError
from services.parsers.factory import DocumentParserFactory
from services.splitters.contract_splitter import ContractSplitter


class ReviewService:
    """Coordinates parsing, clause splitting, analysis, and persistence."""

    def __init__(
        self,
        settings: Settings,
        parser_factory: DocumentParserFactory,
        splitter: ContractSplitter,
        risk_analyzer: RiskAnalyzer,
        review_repository: ReviewRepository,
    ) -> None:
        self.settings = settings
        self.parser_factory = parser_factory
        self.splitter = splitter
        self.risk_analyzer = risk_analyzer
        self.review_repository = review_repository
        self._document_name_counters: dict[str, int] = defaultdict(int)

    def analyze_upload(self, filename: str, content: bytes) -> Review:
        """Analyze an uploaded contract file."""
        parser_result = self.parser_factory.parse(filename=filename, content=content)
        generated_name = self._generate_document_name(filename)
        self._persist_upload(filename=generated_name, content=content)
        return self._analyze_document(
            document_name=generated_name,
            text=parser_result.text,
            content_type=parser_result.content_type,
            metadata={**parser_result.metadata, "original_filename": filename},
        )

    def analyze_text(self, document_name: str, text: str) -> Review:
        """Analyze contract text submitted directly by API callers."""
        generated_name = self._generate_document_name()
        return self._analyze_document(
            document_name=generated_name,
            text=text,
            content_type="text/plain",
            metadata={"submitted_name": document_name},
        )

    def get_review(self, review_id: str) -> Review | None:
        """Fetch a persisted review by ID."""
        return self.review_repository.get(review_id)

    def list_reviews(
        self,
        limit: int = 20,
        offset: int = 0,
        document_name: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        risk_level: str | None = None,
    ):
        """List persisted reviews for history pages."""
        filters = ReviewListFilters(
            document_name=document_name.strip() if document_name else None,
            date_from=self._start_of_day(date_from),
            date_to=self._end_of_day(date_to),
            risk_level=risk_level,
        )
        return self.review_repository.list(filters=filters, limit=limit, offset=offset)

    def delete_review(self, review_id: str) -> bool:
        """Delete one persisted review by ID."""
        return self.review_repository.delete(review_id)

    def _analyze_document(self, document_name: str, text: str, content_type: str, metadata: dict[str, str] | None = None) -> Review:
        normalized_text = text.strip()
        if not normalized_text:
            raise DocumentParseError("No text could be extracted from the document.")

        document = ParsedDocument(
            document_id=uuid4().hex,
            document_name=document_name,
            content_type=content_type,
            text=normalized_text,
            clauses=self.splitter.split(normalized_text),
            metadata=metadata or {},
        )

        risks = self.risk_analyzer.analyze(document)
        summary = self._build_summary(document=document, risk_count=len(risks), risks=risks)

        review = Review(
            review_id=uuid4().hex,
            document_id=document.document_id,
            document_name=document.document_name,
            summary=summary,
            document_text=document.text,
            risks=risks,
            created_at=datetime.now(timezone.utc),
        )
        self.review_repository.save(review)
        return review

    def _generate_document_name(self, original_name: str | None = None) -> str:
        """Generate a readable timestamp-based document name."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        base_name = f"contract{timestamp}"
        self._document_name_counters[base_name] += 1
        counter = self._document_name_counters[base_name]
        suffix = "" if counter == 1 else f"-{counter}"
        extension = Path(original_name).suffix.lower() if original_name else ""
        return f"{base_name}{suffix}{extension}"

    def _persist_upload(self, filename: str, content: bytes) -> None:
        """Store the original upload for traceability."""
        target = self.settings.upload_dir / f"{uuid4().hex}_{Path(filename).name}"
        target.write_bytes(content)

    def _build_summary(self, document: ParsedDocument, risk_count: int, risks) -> str:
        """Build a compact summary for list and detail views."""
        counts = Counter(risk.risk_level for risk in risks)
        if risk_count == 0:
            return (
                f"共拆分 {len(document.clauses)} 个条款，"
                + "当前规则集未命中明显风险，"
                + "建议仍由法务人员进行复核。"
            )

        return (
            f"共拆分 {len(document.clauses)} 个条款，"
            + f"识别出 {risk_count} 个风险点，"
            + f"其中 high {counts.get('high', 0)} 个，"
            + f"medium {counts.get('medium', 0)} 个，"
            + f"low {counts.get('low', 0)} 个。"
        )

    def _start_of_day(self, value: date | None) -> datetime | None:
        if value is None:
            return None
        return datetime.combine(value, time.min, tzinfo=timezone.utc)

    def _end_of_day(self, value: date | None) -> datetime | None:
        if value is None:
            return None
        return datetime.combine(value, time.max, tzinfo=timezone.utc)
