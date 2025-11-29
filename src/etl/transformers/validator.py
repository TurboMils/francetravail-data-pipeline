from __future__ import annotations

from typing import Any


def validate_offer(raw: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Valide une offre brute.
    Règles :
      - id non vide
      - intitule non vide
      - dateCreation non vide
    Retourne (is_valid, [erreurs]).
    """
    errors: list[str] = []

    offer_id = raw.get("id") or raw.get("idOffre")
    if not offer_id:
        errors.append("id manquant")

    intitule = raw.get("intitule")
    if not intitule or not str(intitule).strip():
        errors.append("intitule manquant")

    date_creation = raw.get("dateCreation")
    if not date_creation or not str(date_creation).strip():
        errors.append("dateCreation manquante")

    return len(errors) == 0, errors


def filter_valid_offers(raw_offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Filtre les offres invalides (validation basique).
    """
    valid: list[dict[str, Any]] = []
    for offer in raw_offers:
        ok, _ = validate_offer(offer)
        if ok:
            valid.append(offer)
    return valid
