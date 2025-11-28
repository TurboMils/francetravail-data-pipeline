from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Any, Dict, Optional


HTML_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: Optional[str]) -> Optional[str]:
    """Supprime les balises HTML simples et dés-échappe les entités."""
    if text is None:
        return None
    # Dés-échappe les entités HTML
    text = html.unescape(text)
    # Supprime les balises
    text = HTML_TAG_RE.sub(" ", text)
    # Normalise les espaces
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def normalize_date(date_str: Optional[str]) -> Optional[str]:
    """
    Normalise une date au format ISO8601 (string).
    L'API renvoie typiquement '2022-10-23T08:15:42Z'.
    """
    if not date_str:
        return None

    s = date_str.strip()
    # Gestion du 'Z' terminal (UTC)
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"

    # Essaie plusieurs parseurs simples si besoin
    for fmt in (None, "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            if fmt is None:
                dt = datetime.fromisoformat(s)
            else:
                dt = datetime.strptime(s, fmt)
            return dt.isoformat()
        except Exception:
            continue

    # En cas d'échec, on loguera côté usage si besoin, mais on renvoie la valeur brute
    return date_str


def extract_departement_from_code_postal(code_postal: Optional[str]) -> Optional[str]:
    """
    Extrait un code département probable à partir du code postal.
    Règle simplifiée (France métropolitaine) :
      - 2 premiers caractères, sauf DOM/TOM (97, 98) où il faudrait 3.
    """
    if not code_postal:
        return None
    cp = code_postal.strip()
    if len(cp) < 2:
        return None

    # DOM/TOM simplifié : 97x / 98x -> on renvoie les 3 premiers caractères
    if cp.startswith(("97", "98")) and len(cp) >= 3:
        return cp[:3]

    return cp[:2]


def clean_offer(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applique les transformations de nettoyage / normalisation sur une offre brute.
    On travaille sur une copie, on retourne un nouveau Dict.
    - description : strip HTML
    - dates : normalisées ISO
    - lieuTravail.departement : complété à partir du codePostal si absent
    """
    offer = dict(raw) 

    # Description
    description = offer.get("description")
    offer["description"] = strip_html(description)

    # Dates
    if "dateCreation" in offer:
        offer["dateCreation"] = normalize_date(offer.get("dateCreation"))
    if "dateActualisation" in offer:
        offer["dateActualisation"] = normalize_date(offer.get("dateActualisation"))

    # Lieu de travail
    lieu = dict(offer.get("lieuTravail") or {})
    code_postal = lieu.get("codePostal")
    departement = lieu.get("departement")

    if not departement:
        departement = extract_departement_from_code_postal(code_postal)
        if departement:
            lieu["departement"] = departement

    offer["lieuTravail"] = lieu

    return offer
