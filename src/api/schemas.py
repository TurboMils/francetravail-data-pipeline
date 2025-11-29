# src/api/schemas.py
from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class Offer(BaseModel):
    """Schéma Pydantic pour une offre d'emploi."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    intitule: str
    description: Optional[str]
    date_creation: Optional[str]
    date_actualisation: Optional[str]
    lieu_travail: Optional[str]
    rome_code: Optional[str]
    rome_libelle: Optional[str]
    type_contrat: Optional[str]
    salaire_libelle: Optional[str]
    departement: Optional[str]


class OfferListResponse(BaseModel):
    """Schéma Pydantic pour la réponse de liste d'offres."""

    items: List[Offer]
    total: int
    page: int
    size: int


class OfferSearchRequest(BaseModel):
    """Schéma Pydantic pour la requête de recherche d'offres."""

    keyword: Optional[str] = None
    departement: Optional[str] = None  # pour plus tard
    rome_code: Optional[str] = None
    type_contrat: Optional[str] = None
    page: int = 1
    size: int = 50
