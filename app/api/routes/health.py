"""Health check endpoint, used for uptime monitoring and CI smoke tests."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health() -> dict[str, str]:
    """Returns a simple liveness signal. Does not check the database yet."""
    return {"status": "ok"}
