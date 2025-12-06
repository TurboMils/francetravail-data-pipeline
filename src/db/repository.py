# src/db/repository.py
from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

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
            "entreprise_url": raw.get("entreprise", {}).get("url"),
            "contact_url": raw.get("contact", {}).get("urlRecruteur"),
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

        base_stmt = self._build_filtered_query(
            keyword=keyword,
            departement=departement,
            experience=experience,
            type_contrat=type_contrat,
            date_from=date_from,
        )

        total = self.session.execute(
            base_stmt.with_only_columns(func.count(Offre.id)).order_by(None)
        ).scalar_one()

        offset = (page - 1) * size
        stmt = base_stmt.order_by(Offre.date_creation.desc().nullslast()).offset(offset).limit(size)
        items = list(self.session.execute(stmt).scalars().all())
        return items, total

    def get_global_stats(
        self,
        *,
        keyword: list[str] | None,
        departement: list[str] | None,
        experience: list[str] | None,
        type_contrat: list[str] | None,
        date_from: str | None = None,
    ) -> dict[str, Any]:
        base_stmt = self._build_filtered_query(
            keyword=keyword,
            departement=departement,
            experience=experience,
            type_contrat=type_contrat,
            date_from=date_from,
        )

        subq = base_stmt.subquery()

        total_offers = self.session.execute(select(func.count(subq.c.id))).scalar_one()

        total_companies = self.session.execute(
            select(func.count(func.distinct(subq.c.entreprise_nom)))
        ).scalar_one()

        total_departments = self.session.execute(
            select(func.count(func.distinct(subq.c.departement)))
        ).scalar_one()

        last_date_raw = self.session.execute(select(func.max(subq.c.date_creation))).scalar_one()

        if isinstance(last_date_raw, (datetime, date)):
            last_date: str | None = last_date_raw.isoformat()
        elif last_date_raw is None:
            last_date = None
        else:
            last_date = str(last_date_raw)

        return {
            "total_offers": total_offers,
            "total_departments": total_departments,
            "total_companies": total_companies,
            "last_date": last_date,
        }

    def get_department_stats(
        self,
        *,
        keyword: list[str] | None,
        departement: list[str] | None,
        experience: list[str] | None,
        type_contrat: list[str] | None,
        date_from: str | None = None,
    ) -> list[dict[str, Any]]:
        base_stmt = self._build_filtered_query(
            keyword=keyword,
            departement=departement,
            experience=experience,
            type_contrat=type_contrat,
            date_from=date_from,
        )
        subq = base_stmt.subquery()

        rows = self.session.execute(
            select(
                subq.c.departement,
                func.count().label("nb_offres"),
            )
            .where(subq.c.departement.isnot(None))
            .group_by(subq.c.departement)
            .order_by(subq.c.departement)
        ).all()

        return [{"departement": row.departement, "nb_offres": row.nb_offres} for row in rows]

    def get_contrat_stats(
        self,
        *,
        keyword: list[str] | None,
        departement: list[str] | None,
        experience: list[str] | None,
        type_contrat: list[str] | None,
        date_from: str | None = None,
    ) -> list[dict[str, Any]]:
        base_stmt = self._build_filtered_query(
            keyword=keyword,
            departement=departement,
            experience=experience,
            type_contrat=type_contrat,
            date_from=date_from,
        )
        subq = base_stmt.subquery()

        rows = self.session.execute(
            select(
                subq.c.type_contrat,
                func.count().label("nb_offres"),
            )
            .where(subq.c.type_contrat.isnot(None))
            .group_by(subq.c.type_contrat)
            .order_by(subq.c.type_contrat)
        ).all()

        return [{"type_contrat": row.type_contrat, "nb_offres": row.nb_offres} for row in rows]

    def get_timeline_stats(
        self,
        *,
        keyword: list[str] | None,
        departement: list[str] | None,
        experience: list[str] | None,
        type_contrat: list[str] | None,
        date_from: str | None = None,
    ) -> list[dict[str, Any]]:
        base_stmt = self._build_filtered_query(
            keyword=keyword,
            departement=departement,
            experience=experience,
            type_contrat=type_contrat,
            date_from=date_from,
        )
        subq = base_stmt.subquery()

        rows = self.session.execute(
            select(
                func.date(subq.c.date_creation).label("date"),
                func.count().label("nb_offres"),
            )
            .group_by("date")
            .order_by("date")
        ).all()

        result: list[dict[str, Any]] = []
        for row in rows:
            d = row.date
            if isinstance(d, (datetime, date)):
                date_str = d.isoformat()
            elif d is None:
                date_str = None
            else:
                date_str = str(d)

            result.append(
                {
                    "date": date_str,
                    "nb_offres": int(row.nb_offres),
                }
            )

        return result

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

    def _build_filtered_query(
        self,
        *,
        keyword: list[str] | None,
        departement: list[str] | None,
        experience: list[str] | None,
        type_contrat: list[str] | None,
        date_from: str | None = None,
    ) -> Select[tuple[Offre]]:
        stmt: Select[tuple[Offre]] = select(Offre)

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

        return stmt
