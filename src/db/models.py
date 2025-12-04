from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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

    entreprise_nom: Mapped[str | None] = mapped_column(String(200))

    # 7. Code ROME
    rome_code: Mapped[str | None] = mapped_column(String(10))

    # 8. Libellé ROME
    rome_libelle: Mapped[str | None] = mapped_column(String(255))

    # 9. Type de contrat
    type_contrat: Mapped[str | None] = mapped_column(String(20))
    type_contrat_libelle: Mapped[str | None] = mapped_column(String(100))

    experience_libelle: Mapped[str | None] = mapped_column(String(100))
    experience_commentaire: Mapped[str | None] = mapped_column(String(200))

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
