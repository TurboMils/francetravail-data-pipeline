# src/db/repository.py
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import Offre


class OfferRepository:
    """Repository basique pour la table offres."""

    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _map_api_offer(raw: dict) -> dict:
        """Mappe une offre API brute -> Dict de colonnes Offre."""
        lieu_travail_obj = raw.get("lieuTravail") or {}
        lieu_travail_libelle = lieu_travail_obj.get("libelle")
        departement = lieu_travail_libelle[:2] if lieu_travail_libelle and len(lieu_travail_libelle) >= 2 else None
        salaire = raw.get("salaire") or {}
        salaire_libelle = salaire.get("libelle") or salaire.get("commentaire") or None

        return {
            "id": raw.get("id") or raw.get("idOffre"),
            "intitule": raw.get("intitule"),
            "description": raw.get("description"),
            "date_creation": raw.get("dateCreation"),      
            "date_actualisation": raw.get("dateActualisation"),
            "lieu_travail": lieu_travail_libelle,
            "rome_code": raw.get("romeCode"),
            "rome_libelle": raw.get("romeLibelle"),
            "type_contrat": raw.get("typeContrat"),
            "type_contrat_libelle": raw.get("typeContratLibelle"),
            "entreprise_nom": raw.get("entreprise")["nom"] if raw.get("entreprise") else None,
            "experience_libelle": raw.get("experienceLibelle"),
            "experience_commentaire": raw.get("experienceCommentaire"),
            "salaire_libelle": salaire_libelle,
            "departement": departement,
            
        }

    def upsert_from_api(self, raw: dict) -> tuple[bool, Offre | None]:
        """Insère ou met à jour une offre. Retourne (created, instance)."""
        data = self._map_api_offer(raw)
        offre_id = data["id"]
        if not offre_id:
            return False, None

        stmt = select(Offre).where(Offre.id == offre_id)
        existing = self.session.execute(stmt).scalar_one_or_none()

        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            created = False
            instance = existing
        else:
            instance = Offre(**data)
            self.session.add(instance)
            created = True

        return created, instance

    def upsert_many_from_api(self, raws: Iterable[dict]) -> tuple[int, int]:
        created = 0
        updated = 0

        for raw in raws:
            c, _ = self.upsert_from_api(raw)
            if c:
                created += 1
            else:
                updated += 1

        self.session.commit()
        return created, updated

    def list_all(self) -> list[Offre]:
        stmt = select(Offre).order_by(Offre.date_creation.desc().nullslast())
        return list(self.session.execute(stmt).scalars().all())

    def get_by_id(self, offre_id: str) -> Offre | None:
        stmt = select(Offre).where(Offre.id == offre_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_paginated(self, page: int, size: int) -> tuple[list[Offre], int]:
        # Simple pagination avec total count
        if page < 1:
            page = 1
        if size < 1:
            size = 10

        # Get total count
        total = self.session.execute(select(func.count()).select_from(Offre)).scalar_one()

        offset = (page - 1) * size
        stmt = (
            select(Offre)
            .order_by(Offre.date_creation.desc().nullslast())
            .offset(offset)
            .limit(size)
        )
        items = list(self.session.execute(stmt).scalars().all())
        return items, total

    # Recherche paginée avec filtres
    def search_paginated(
        self,
        *,
        keyword: str | None,
        departement: str | None,
        rome_code: str | None,
        type_contrat: str | None,
        page: int,
        size: int,
    ) -> tuple[list[Offre], int]:
        """
        Recherche naïve :
        - keyword sur intitule / description (LIKE)
        - filtres exacts sur rome_code, type_contrat
        - departement :on ignore pour l’instant
        """
        if page < 1:
            page = 1
        if size < 1:
            size = 10

        stmt = select(Offre)

        if keyword:
            like_pattern = f"%{keyword}%"
            stmt = stmt.where(
                (Offre.intitule.ilike(like_pattern)) | (Offre.description.ilike(like_pattern))
            )

        if rome_code:
            stmt = stmt.where(Offre.rome_code == rome_code)

        if type_contrat:
            stmt = stmt.where(Offre.type_contrat == type_contrat)

        if departement:
            stmt = stmt.where(Offre.departement == departement)

        # total avant pagination
        total = self.session.execute(
            stmt.with_only_columns(func.count(Offre.id)).order_by(None)
        ).scalar_one()

        offset = (page - 1) * size
        stmt = stmt.order_by(Offre.date_creation.desc().nullslast()).offset(offset).limit(size)

        items = list(self.session.execute(stmt).scalars().all())
        return items, total
