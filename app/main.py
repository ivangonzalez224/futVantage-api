"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.events import router as events_router
from app.api.routes.health import router as health_router
from app.api.routes.matches import router as matches_router
from app.api.routes.players import router as players_router
from app.api.routes.possession import router as possession_router
from app.api.routes.teams import router as teams_router
from app.core.config import get_settings
from app.core.logging_config import configure_logging


def create_app() -> FastAPI:
    """Application factory. Keeps app construction testable and import-safe."""
    configure_logging()
    settings = get_settings()

    app = FastAPI(title=settings.app_name)

    # Allows the frontend (a different origin: localhost:3000 vs this
    # API's localhost:8000) to call this API from the browser.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix=settings.api_v1_prefix)
    app.include_router(auth_router, prefix=settings.api_v1_prefix)
    app.include_router(events_router, prefix=settings.api_v1_prefix)
    app.include_router(players_router, prefix=settings.api_v1_prefix)
    app.include_router(possession_router, prefix=settings.api_v1_prefix)
    app.include_router(matches_router, prefix=settings.api_v1_prefix)
    app.include_router(teams_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
