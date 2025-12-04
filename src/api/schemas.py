# src/api/schemas.py
from __future__ import annotations
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class Offer(BaseModel):
    """Schéma Pydantic pour une offre d'emploi."""

    model_config = ConfigDict(from_attributes=True)
            
    id: str
    intitule: str
    description: str | None
    date_creation: str | None
    date_actualisation: str | None
    lieu_travail: str | None
    rome_code: str | None
    rome_libelle: str | None
    type_contrat: str | None
    type_contrat_libelle: str | None
    entreprise_nom: str | None
    experience_libelle: str | None
    experience_commentaire: str | None
    salaire_libelle: str | None
    departement: str | None
    


class OfferListResponse(BaseModel):
    """Schéma Pydantic pour la réponse de liste d'offres."""

    items: list[Offer]
    total: int
    page: int
    size: int


class OfferSearchRequest(BaseModel):
    """Schéma Pydantic pour la requête de recherche d'offres."""

    keyword: str | None = None
    departement: str | None = None
    rome_code: str | None = None
    type_contrat: str | None = None
    page: int = 1
    size: int = 50
    date_from: str | None = None 

class ContractStats(BaseModel):
    type_contrat: Optional[str]
    count: int


class GlobalStats(BaseModel):
    total_offers: int
    total_companies: int
    first_date: Optional[date]
    last_date: Optional[date]
    by_type_contrat: List[ContractStats]


class TimelinePoint(BaseModel):
    date: date
    count: int


class DepartmentStat(BaseModel):
    departement: str
    count: int