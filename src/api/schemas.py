# src/api/schemas.py
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class Offer(BaseModel):
    """Schéma Pydantic pour une offre d'emploi."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    intitule: str
    description: str | None
    date_creation: str | None
    date_actualisation: str | None
    lieu_travail: str | None
    rome_libelle: str | None
    type_contrat: str | None
    type_contrat_libelle: str | None
    entreprise_nom: str | None
    experience_libelle: str | None
    experience_commentaire: str | None
    experience: str | None
    salaire_libelle: str | None
    departement: str | None


class OfferListResponse(BaseModel):
    """Schéma Pydantic pour la réponse de liste d'offres."""

    items: list[Offer]
    total: int
    page: int
    size: int


class OffersFilterRequest(BaseModel):
    keyword: list[str] | None = None
    departement: list[str] | None = None
    experience: list[str] | None = None
    type_contrat: list[str] | None = None
    date_from: str | None = None


class OfferSearchRequest(OffersFilterRequest):
    page: int = Field(1, ge=1)
    size: int = Field(50, ge=1, le=1000)


class ContractStats(BaseModel):
    type_contrat: str | None
    count: int


class GlobalStats(BaseModel):
    total_offers: int
    total_departments: int
    total_companies: int
    last_date: str


class TimelinePoint(BaseModel):
    date: date
    count: int


class DepartmentStat(BaseModel):
    departement: str
    count: int


class FiltersResponse(BaseModel):
    contrat: list[str]
    experience: list[str]
    departements: list[str]
