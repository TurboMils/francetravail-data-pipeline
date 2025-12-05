from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends

from api.dependencies import get_offer_repository
from api.schemas import GlobalStats, OffersFilterRequest
from db.repository import OfferRepository

router = APIRouter()


@router.post("/global", response_model=GlobalStats)
async def get_global_stats(
    payload: OffersFilterRequest,
    repo: OfferRepository = Depends(get_offer_repository),
) -> GlobalStats:
    return repo.get_global_stats(
        keyword=payload.keyword,
        departement=payload.departement,
        type_contrat=payload.type_contrat,
        experience=payload.experience,
        date_from=payload.date_from,
    )


@router.post("/contrats")
async def get_contrat_stats(
    payload: OffersFilterRequest,
    repo: OfferRepository = Depends(get_offer_repository),
) -> list[dict[str, Any]]:
    data = repo.get_contrat_stats(
        keyword=payload.keyword,
        departement=payload.departement,
        experience=payload.experience,
        type_contrat=payload.type_contrat,
        date_from=payload.date_from,
    )
    return cast(list[dict[str, Any]], data)


@router.post("/departements")
async def get_department_stats(
    payload: OffersFilterRequest,
    repo: OfferRepository = Depends(get_offer_repository),
) -> list[dict[str, Any]]:
    data = repo.get_department_stats(
        keyword=payload.keyword,
        departement=payload.departement,
        experience=payload.experience,
        type_contrat=payload.type_contrat,
        date_from=payload.date_from,
    )
    return cast(list[dict[str, Any]], data)


@router.post("/timeline")
async def get_timeline_stats(
    payload: OffersFilterRequest,
    repo: OfferRepository = Depends(get_offer_repository),
) -> list[dict[str, Any]]:
    data = repo.get_timeline_stats(
        keyword=payload.keyword,
        departement=payload.departement,
        experience=payload.experience,
        type_contrat=payload.type_contrat,
        date_from=payload.date_from,
    )
    return cast(list[dict[str, Any]], data)
