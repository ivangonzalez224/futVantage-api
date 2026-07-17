"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.api.routes.events import router as events_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    """Application factory. Keeps app construction testable and import-safe."""
    settings = get_settings()

    app = FastAPI(title=settings.app_name)
    app.include_router(health_router, prefix=settings.api_v1_prefix)
    app.include_router(events_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
