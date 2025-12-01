from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import get_offer_repository
from api.schemas import Offer, OfferListResponse, OfferSearchRequest
from db.repository import OfferRepository

router = APIRouter()


@router.get("", response_model=OfferListResponse, tags=["offers"])
async def list_offers(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    repo: OfferRepository = Depends(get_offer_repository),
):
    items, total = repo.list_paginated(page=page, size=size)
    return OfferListResponse(items=items, total=total, page=page, size=size)


@router.get("/{offer_id}", response_model=Offer, tags=["offers"])
async def get_offer(
    offer_id: str,
    repo: OfferRepository = Depends(get_offer_repository),
):
    offer = repo.get_by_id(offer_id)
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
    return offer


@router.post("/search", response_model=OfferListResponse, tags=["offers"])
async def search_offers(
    payload: OfferSearchRequest,
    repo: OfferRepository = Depends(get_offer_repository),
):
    items, total = repo.search_paginated(
        keyword=payload.keyword,
        departement=payload.departement,
        rome_code=payload.rome_code,
        type_contrat=payload.type_contrat,
        page=payload.page,
        size=payload.size, 
    )
    return OfferListResponse(
        items=items,
        total=total,
        page=payload.page,
        size=payload.size,
    )
