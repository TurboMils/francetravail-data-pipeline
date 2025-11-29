from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import offers
from config.logging_config import get_logger
from config.settings import settings
from db.sessions import init_db

logger = get_logger(__name__)

init_db()

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=settings.api_cors_allow_credentials,
    allow_methods=settings.api_cors_allow_methods,
    allow_headers=settings.api_cors_allow_headers,
)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}


app.include_router(offers.router, prefix="/offers", tags=["offers"])
