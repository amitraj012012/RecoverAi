from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import settings

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    project: str
    version: str
    environment: str
    timestamp: str


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Returns the health status of the RecoverAI backend service."""
    return HealthResponse(
        status="ok",
        project=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
