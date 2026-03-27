"""Review API routes."""
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile

from schemas.review import AnalyzeTextRequest, ReviewListResponse, ReviewResponse
from services.parsers.base import DocumentParseError, UnsupportedDocumentError

router = APIRouter(prefix="/api", tags=["review"])


def _get_review_service(request: Request):
    return request.app.state.container.review_service


@router.post("/review/upload", response_model=ReviewResponse)
async def review_upload(request: Request, file: UploadFile = File(...)) -> ReviewResponse:
    """Upload a contract file, analyze it, and persist the review result."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must include a filename.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    service = _get_review_service(request)
    try:
        review = service.analyze_upload(file.filename, content)
    except UnsupportedDocumentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DocumentParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return ReviewResponse.from_domain(review)


@router.post("/review/analyze", response_model=ReviewResponse)
async def review_analyze(request: Request, payload: AnalyzeTextRequest) -> ReviewResponse:
    """Analyze raw contract text and persist the review result."""
    review = _get_review_service(request).analyze_text(
        document_name=payload.document_name,
        text=payload.text,
    )
    return ReviewResponse.from_domain(review)


@router.get("/review/{review_id}", response_model=ReviewResponse)
async def get_review(request: Request, review_id: str) -> ReviewResponse:
    """Fetch a persisted review by its identifier."""
    review = _get_review_service(request).get_review(review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found.")
    return ReviewResponse.from_domain(review)


@router.get("/reviews", response_model=ReviewListResponse)
async def list_reviews(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ReviewListResponse:
    """List persisted reviews for history display."""
    items = _get_review_service(request).list_reviews(limit=limit, offset=offset)
    return ReviewListResponse.from_domain(items)

