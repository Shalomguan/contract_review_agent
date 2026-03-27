"""FastAPI application factory."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes.review import router as review_router
from core.config import Settings, get_settings
from core.container import build_container


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create a configured FastAPI application instance."""
    settings = settings or get_settings()
    container = build_container(settings)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Minimal, testable contract review risk agent MVP.",
    )
    app.state.container = container
    app.include_router(review_router)

    static_dir = Path(__file__).resolve().parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse | dict[str, str]:
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"name": settings.app_name, "version": settings.app_version}

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

