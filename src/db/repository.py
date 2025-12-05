# src/db/repository.py
from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta
from typing import Any

from sqlalchemy import func, or_, select
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
        departement = (
            lieu_travail_libelle[:2]
            if lieu_travail_libelle and len(lieu_travail_libelle) >= 2
            else None
        )

        return {
            "id": raw.get("id") or raw.get("idOffre"),
            "intitule": raw.get("intitule"),
            "description": raw.get("description"),
            "date_creation": raw.get("dateCreation"),
            "date_actualisation": raw.get("dateActualisation"),
            "lieu_travail": raw.get("lieuTravail", {}).get("libelle"),
            "rome_code": raw.get("romeCode"),
            "rome_libelle": raw.get("romeLibelle"),
            "type_contrat": raw.get("typeContrat"),
            "type_contrat_libelle": raw.get("typeContratLibelle"),
            "entreprise_nom": raw.get("entreprise", {}).get("nom"),
            "experience_libelle": raw.get("experienceLibelle"),
            "experience_commentaire": raw.get("experienceCommentaire"),
            "experience": raw.get("experienceExige"),
            "salaire_libelle": raw.get("salaire", {}).get("libelle")
            or raw.get("salaire", {}).get("commentaire"),
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

    def search_paginated(
        self,
        *,
        keyword: list[str] | None,
        departement: list[str] | None,
        experience: list[str] | None,
        type_contrat: list[str] | None,
        page: int,
        size: int,
        date_from: str | None = None,
    ) -> tuple[list[Offre], int]:
        if page < 1:
            page = 1
        if size < 1:
            size = 10

        stmt = select(Offre)

        # Filtre mots-clés (OR sur tous les mots)
        if keyword:
            like_clauses: list[Any] = []
            for kw in keyword:
                kw = kw.strip()
                if not kw:
                    continue
                pattern = f"%{kw}%"
                like_clauses.append(Offre.intitule.ilike(pattern))
                like_clauses.append(Offre.description.ilike(pattern))
            if like_clauses:
                stmt = stmt.where(or_(*like_clauses))

        if experience:
            stmt = stmt.where(Offre.experience.in_(experience))

        if type_contrat:
            stmt = stmt.where(Offre.type_contrat.in_(type_contrat))

        if departement:
            stmt = stmt.where(Offre.departement.in_(departement))
        if date_from:
            stmt = stmt.where(Offre.date_creation >= date_from)

        # total avant pagination
        total = self.session.execute(
            stmt.with_only_columns(func.count(Offre.id)).order_by(None)
        ).scalar_one()

        offset = (page - 1) * size
        stmt = stmt.order_by(Offre.date_creation.desc().nullslast()).offset(offset).limit(size)

        items = list(self.session.execute(stmt).scalars().all())
        return items, total

    def get_global_stats(self) -> dict[str, Any]:
        total_offers = self.session.execute(select(func.count(Offre.id))).scalar_one()

        total_companies = self.session.execute(
            select(func.count(func.distinct(Offre.entreprise_nom)))
        ).scalar_one()

        first_date, last_date = self.session.execute(
            select(func.min(Offre.date_creation), func.max(Offre.date_creation))
        ).one()

        by_type_rows = self.session.execute(
            select(Offre.type_contrat, func.count(Offre.id).label("count"))
            .group_by(Offre.type_contrat)
            .order_by(func.count(Offre.id).desc())
        ).all()

        by_type_contrat = [
            {"type_contrat": type_contrat, "count": count} for type_contrat, count in by_type_rows
        ]

        return {
            "total_offers": total_offers,
            "total_companies": total_companies,
            "first_date": first_date,
            "last_date": last_date,
            "by_type_contrat": by_type_contrat,
        }

    def get_timeline_stats(self, days: int = 30) -> list[dict[str, Any]]:
        """
        Timeline du nombre d'offres par jour sur les N derniers jours.
        Retourne une liste de {date, count}.
        """
        if days <= 0:
            days = 30

        start_date = date.today() - timedelta(days=days - 1)

        rows = self.session.execute(
            select(
                func.date(Offre.date_creation).label("date"),
                func.count(Offre.id).label("count"),
            )
            .where(Offre.date_creation >= start_date)
            .group_by(func.date(Offre.date_creation))
            .order_by(func.date(Offre.date_creation))
        ).all()

        return [{"date": row.date, "count": row.count} for row in rows]

    def get_department_stats(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        Top départements par nombre d'offres.
        Retourne une liste de {departement, count}.
        """
        if limit <= 0:
            limit = 20

        rows = self.session.execute(
            select(
                Offre.departement,
                func.count(Offre.id).label("count"),
            )
            .where(Offre.departement.isnot(None))
            .group_by(Offre.departement)
            .order_by(func.count(Offre.id).desc())
            .limit(limit)
        ).all()

        return [{"departement": dep, "count": count} for dep, count in rows]

    def get_filter_values(self) -> dict[str, list[str]]:
        """Retourne les valeurs disponibles pour les filtres."""

        contrat_type = (
            self.session.execute(
                select(Offre.type_contrat)
                .where(Offre.type_contrat.isnot(None))
                .distinct()
                .order_by(Offre.type_contrat)
            )
            .scalars()
            .all()
        )

        departements = (
            self.session.execute(
                select(Offre.departement)
                .where(Offre.departement.isnot(None))
                .distinct()
                .order_by(Offre.departement)
            )
            .scalars()
            .all()
        )

        experience = (
            self.session.execute(
                select(Offre.experience)
                .where(Offre.experience.isnot(None))
                .distinct()
                .order_by(Offre.experience)
            )
            .scalars()
            .all()
        )

        # Nettoyage pour s'assurer qu'on renvoie des str
        contrat_list = [str(r) for r in contrat_type if r is not None]
        deps_list = [str(d) for d in departements if d is not None]
        experience_list = [str(e) for e in experience if e is not None]

        return {
            "contrat": contrat_list,
            "experience": experience_list,
            "departements": deps_list,
        }
