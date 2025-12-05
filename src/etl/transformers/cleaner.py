from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Any

HTML_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str | None) -> str | None:
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


def normalize_date(date_str: str | None) -> str | None:
    """
    Normalise une date au format ISO8601 (string).
    L'API renvoie typiquement '2022-10-23T08:15:42Z'.
    """
    if not date_str:
        return None

    s = date_str.strip()
    if not s:
        return None

    # Gestion du 'Z' terminal (UTC)
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"

    for fmt in (None, "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            if fmt is None:
                dt = datetime.fromisoformat(s)
            else:
                dt = datetime.strptime(s, fmt)
            return dt.isoformat()
        except Exception:
            continue

    # En cas d'échec, on renvoie la valeur brute
    return date_str


def extract_departement_from_code_postal(code_postal: str | None) -> str | None:
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


def simple_markdown_format(text: str | None) -> str | None:
    """
    Mise en forme très légère pour un rendu Markdown.
    N’essaie pas de “rendre joli”, juste structure un peu.
    """
    if not text:
        return None

    # Puces : "* " -> "• "
    text = re.sub(r"^\*\s+", "• ", text, flags=re.MULTILINE)

    # Sauts de ligne après phrase terminée suivie d'une majuscule
    text = re.sub(r"\.\s+(?=[A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜ])", ".\n\n", text)

    sections = [
        "Missions principales",
        "De formation technique",
        "Les avantages",
        "Vous maîtrisez",
        "Rigoureux",
        "Profil recherché",
        "Vos missions",
        "Compétences requises",
    ]
    for section in sections:
        text = text.replace(section, f"**{section}**")

    return text


def clean_offer(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Applique les transformations de nettoyage / normalisation sur une offre brute.
    - description : strip HTML + léger format Markdown
    - dates : normalisées ISO
    - lieuTravail.departement : complété à partir du codePostal si absent
    """
    offer = dict(raw)

    # Description
    description_raw = offer.get("description")
    cleaned_desc = strip_html(description_raw)
    formatted_desc = simple_markdown_format(cleaned_desc)
    offer["description"] = formatted_desc

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
