from __future__ import annotations

from typing import Any, Dict, List, Tuple


def validate_offer(raw: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Valide une offre brute.
    Règles :
      - id non vide
      - intitule non vide
      - dateCreation non vide
    Retourne (is_valid, [erreurs]).
    """
    errors: List[str] = []

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


def filter_valid_offers(raw_offers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filtre les offres invalides (validation basique).
    """
    valid: List[Dict[str, Any]] = []
    for offer in raw_offers:
        ok, _ = validate_offer(offer)
        if ok:
            valid.append(offer)
    return valid
