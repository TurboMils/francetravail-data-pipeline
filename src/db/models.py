from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Any

from sqlalchemy import Integer, DateTime, Text, String, DECIMAL, func, text
from sqlalchemy.dialects.postgresql import JSONB

class Base(DeclarativeBase):
    """Base pour tous les modèles."""

    pass


class Offre(Base):
    """Modèle simplifié des offres d'emploi"""

    __tablename__ = "offres"

    # 1. Identifiant France Travail
    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)

    # 2. Intitulé
    intitule: Mapped[str | None] = mapped_column(String(500))

    # 3. Description
    description: Mapped[str | None] = mapped_column(Text)

    # 4. Date de création (stockée en texte ISO pour le moment)
    date_creation: Mapped[str | None] = mapped_column(String(32))

    # 5. Date d’actualisation
    date_actualisation: Mapped[str | None] = mapped_column(String(32))

    # 6. Lieu (libellé)
    lieu_travail: Mapped[str | None] = mapped_column(String(255))

    # 7. Code ROME
    rome_code: Mapped[str | None] = mapped_column(String(10))

    # 8. Libellé ROME
    rome_libelle: Mapped[str | None] = mapped_column(String(255))

    # 9. Type de contrat
    type_contrat: Mapped[str | None] = mapped_column(String(20))

    # 10. Salaire (libellé)
    salaire_libelle: Mapped[str | None] = mapped_column(String(255))

    # 11. Département
    departement: Mapped[str | None] = mapped_column(String(5))

    # Métadonnée interne
    date_ingestion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Offre(id={self.id}, intitule={self.intitule!r})>"
    

class IngestionLog(Base):
    """Modèle pour tracker les ingestions ETL."""

    __tablename__ = "ingestion_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    nb_offres_extraites: Mapped[int | None] = mapped_column(Integer)
    nb_offres_inserees: Mapped[int | None] = mapped_column(Integer)
    nb_offres_mises_a_jour: Mapped[int | None] = mapped_column(Integer)
    nb_erreurs: Mapped[int | None] = mapped_column(Integer)
    duree_secondes: Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    statut: Mapped[str | None] = mapped_column(String(20))
    message_erreur: Mapped[str | None] = mapped_column(Text)
    parametres: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    def __repr__(self) -> str:
        return f"<IngestionLog(id={self.id}, timestamp={self.timestamp}, statut={self.statut})>"
