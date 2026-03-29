"""FastAPI application factory."""
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes.auth import router as auth_router
from api.routes.review import router as review_router
from core.config import Settings, get_settings
from core.container import build_container


logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create a configured FastAPI application instance."""
    settings = settings or get_settings()
    container = build_container(settings)
    logger.info(container.review_service.risk_analyzer.retrieval_service.status_message)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Minimal, testable contract review risk agent MVP.",
    )
    app.state.container = container
    app.include_router(auth_router)
    app.include_router(review_router)

    static_dir = Path(__file__).resolve().parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", include_in_schema=False, response_model=None)
    async def index():
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"name": settings.app_name, "version": settings.app_version}

    @app.get("/login", include_in_schema=False, response_model=None)
    async def login_page():
        login_file = static_dir / "login.html"
        if login_file.exists():
            return FileResponse(login_file)
        return {"name": settings.app_name, "mode": "login"}

    @app.get("/lab", include_in_schema=False, response_model=None)
    async def lab():
        lab_file = static_dir / "lab.html"
        if lab_file.exists():
            return FileResponse(lab_file)
        return {"name": settings.app_name, "mode": "lab"}

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        retrieval_service = container.review_service.risk_analyzer.retrieval_service
        rag_mode = "vector" if retrieval_service.using_vector_retrieval else "lexical_fallback"
        return {"status": "ok", "rag_mode": rag_mode}

    return app


app = create_app()


