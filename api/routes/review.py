"""Review API routes."""
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile
from fastapi.security import HTTPAuthorizationCredentials

from api.dependencies import bearer_scheme, get_current_user
from models.user import User
from schemas.review import AnalyzeTextRequest, DeleteReviewResponse, ReviewListResponse, ReviewResponse
from services.parsers.base import DocumentParseError, UnsupportedDocumentError

router = APIRouter(prefix="/api", tags=["review"])


def _get_review_service(request: Request):
    return request.app.state.container.review_service


@router.post("/review/upload", response_model=ReviewResponse)
async def review_upload(
    request: Request,
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> ReviewResponse:
    """Upload a contract file, analyze it, and persist the review result."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must include a filename.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    current_user = get_current_user(request, credentials)
    service = _get_review_service(request)
    try:
        review = service.analyze_upload(current_user.user_id, file.filename, content)
    except UnsupportedDocumentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DocumentParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return ReviewResponse.from_domain(review)


@router.post("/review/analyze", response_model=ReviewResponse)
async def review_analyze(
    request: Request,
    payload: AnalyzeTextRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> ReviewResponse:
    """Analyze raw contract text and persist the review result."""
    current_user = get_current_user(request, credentials)
    review = _get_review_service(request).analyze_text(
        user_id=current_user.user_id,
        document_name=payload.document_name,
        text=payload.text,
    )
    return ReviewResponse.from_domain(review)


@router.get("/review/{review_id}", response_model=ReviewResponse)
async def get_review(
    request: Request,
    review_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> ReviewResponse:
    """Fetch a persisted review by its identifier."""
    current_user = get_current_user(request, credentials)
    review = _get_review_service(request).get_review(current_user.user_id, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found.")
    return ReviewResponse.from_domain(review)


@router.get("/review/{review_id}/export")
async def export_review(
    request: Request,
    review_id: str,
    format: str = Query(..., pattern="^(markdown|html)$"),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Response:
    """Export one persisted review as markdown or HTML."""
    current_user = get_current_user(request, credentials)
    artifact = _get_review_service(request).export_review(current_user.user_id, review_id, format)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Review not found.")
    response = Response(content=artifact.content, media_type=artifact.media_type)
    response.headers["Content-Disposition"] = request.app.state.container.review_service.review_exporter.build_content_disposition(artifact.filename)
    return response


@router.delete("/review/{review_id}", response_model=DeleteReviewResponse)
async def delete_review(
    request: Request,
    review_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> DeleteReviewResponse:
    """Delete one persisted review by its identifier."""
    current_user = get_current_user(request, credentials)
    deleted = _get_review_service(request).delete_review(current_user.user_id, review_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Review not found.")
    return DeleteReviewResponse(review_id=review_id, deleted=True)


@router.get("/reviews", response_model=ReviewListResponse)
async def list_reviews(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    document_name: str | None = Query(default=None, min_length=1),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    risk_level: str | None = Query(default=None, pattern="^(high|medium|low)$"),
) -> ReviewListResponse:
    """List persisted reviews for history display."""
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must be earlier than or equal to date_to.")

    current_user = get_current_user(request, credentials)
    items, total = _get_review_service(request).list_reviews(
        user_id=current_user.user_id,
        limit=limit,
        offset=offset,
        document_name=document_name,
        date_from=date_from,
        date_to=date_to,
        risk_level=risk_level,
    )
    return ReviewListResponse.from_domain(items, total=total, limit=limit, offset=offset)
