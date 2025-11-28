from fastapi import FastAPI

from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
)


@app.on_event("startup")
def on_startup():
    logger.info("API starting up (env=%s)", settings.environment)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "environment": settings.environment}
