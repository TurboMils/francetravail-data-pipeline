from __future__ import annotations

from etl.transformers.cleaner import (
    clean_offer,
    extract_departement_from_code_postal,
    normalize_date,
    strip_html,
)
from etl.transformers.validator import validate_offer


def test_strip_html_basic():
    raw = "<p>Hello <b>mon app</b> &amp; test</p>"
    cleaned = strip_html(raw)
    assert cleaned == "Hello mon app & test"


def test_normalize_date_iso_z():
    s = "2022-10-23T08:15:42Z"
    out = normalize_date(s)
    # Doit devenir un ISO complet avec timezone explicite
    assert out.startswith("2022-10-23T08:15:42")
    assert "+00:00" in out


def test_extract_departement_from_code_postal():
    assert extract_departement_from_code_postal("75001") == "75"
    assert extract_departement_from_code_postal("33100") == "33"
    assert extract_departement_from_code_postal("97410") == "974"
    assert extract_departement_from_code_postal(None) is None


def test_clean_offer_enriches_departement_from_code_postal():
    raw = {
        "id": "OFFRE1",
        "intitule": "Dev Python",
        "description": "<p>CDI en <b>remote</b></p>",
        "dateCreation": "2022-10-23T08:15:42Z",
        "lieuTravail": {
            "libelle": "Paris 1er",
            "codePostal": "75001",
        },
    }

    cleaned = clean_offer(raw)

    # description doit être nettoyée
    assert cleaned["description"] == "CDI en remote"

    # dateCreation normalisée
    assert "T" in cleaned["dateCreation"]

    # departement déduit du codePostal
    lieu = cleaned["lieuTravail"]
    assert lieu["codePostal"] == "75001"
    assert lieu["departement"] == "75"


def test_validate_offer_success():
    raw = {
        "id": "OFFRE2",
        "intitule": "Dev Python",
        "dateCreation": "2022-10-23T08:15:42Z",
    }
    ok, errors = validate_offer(raw)
    assert ok is True
    assert errors == []


def test_validate_offer_failure_missing_fields():
    raw = {
        "intitule": "",
        "dateCreation": "",
    }
    ok, errors = validate_offer(raw)
    assert ok is False
    assert "id manquant" in errors
    assert "intitule manquant" in errors
    assert "dateCreation manquante" in errors
