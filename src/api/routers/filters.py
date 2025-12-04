from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import get_offer_repository
from api.schemas import FiltersResponse
from db.repository import OfferRepository

router = APIRouter(
    prefix="/filters",
    tags=["filters"],
)


@router.get("", response_model=FiltersResponse)
async def get_filters(
    repo: OfferRepository = Depends(get_offer_repository),
) -> FiltersResponse:
    data = repo.get_filter_values()
    return FiltersResponse(**data)
