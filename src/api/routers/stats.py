from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_offer_repository
from api.schemas import (
    DepartmentStat,
    GlobalStats,
    TimelinePoint,
)
from db.repository import OfferRepository

router = APIRouter(
    prefix="/stats",
    tags=["stats"],
)


@router.get("/global", response_model=GlobalStats)
async def get_global_stats(
    repo: OfferRepository = Depends(get_offer_repository),
):
    return repo.get_global_stats()


@router.get("/timeline", response_model=list[TimelinePoint])
async def get_timeline_stats(
    days: int = Query(30, ge=1, le=365),
    repo: OfferRepository = Depends(get_offer_repository),
):
    return repo.get_timeline_stats(days=days)


@router.get("/departements", response_model=list[DepartmentStat])
async def get_department_stats(
    limit: int = Query(20, ge=1, le=200),
    repo: OfferRepository = Depends(get_offer_repository),
):
    return repo.get_department_stats(limit=limit)
