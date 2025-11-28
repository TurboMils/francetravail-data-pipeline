# src/db/repository.py
from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Offre


class OfferRepository:
    """Repository basique pour la table offres."""

    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _map_api_offer(raw: Dict) -> Dict:
        """Mappe une offre API brute -> Dict de colonnes Offre."""
        lieu_travail = (raw.get("lieuTravail") or {}).get("libelle")
        salaire = raw.get("salaire") or {}
        salaire_libelle = (
            salaire.get("libelle")
            or salaire.get("commentaire")
            or salaire.get("complement")
            or None
        )

        return {
            "id": raw.get("id") or raw.get("idOffre"),
            "intitule": raw.get("intitule"),
            "description": raw.get("description"),
            "date_creation": raw.get("dateCreation"),
            "date_actualisation": raw.get("dateActualisation"),
            "lieu_travail": lieu_travail,
            "rome_code": raw.get("romeCode"),
            "rome_libelle": raw.get("romeLibelle"),
            "type_contrat": raw.get("typeContrat"),
            "salaire_libelle": salaire_libelle,
        }

    def upsert_from_api(self, raw: Dict) -> Tuple[bool, Offre | None]:
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

    def upsert_many_from_api(self, raws: Iterable[Dict]) -> Tuple[int, int]:
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

    def list_all(self) -> List[Offre]:
        stmt = select(Offre).order_by(Offre.date_creation.desc().nullslast())
        return List(self.session.execute(stmt).scalars().all())
