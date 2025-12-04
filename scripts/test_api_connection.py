#!/usr/bin/env python3

from config.logging_config import get_logger
from etl.extractors.france_travail_api import FranceTravailClient, FranceTravailApiError

logger = get_logger(__name__)

def main() -> None:
    logger.info("Starting manual France Travail API test")

    client = FranceTravailClient()

    keyword = "coiffeur"
    departement = ""
    limit = 150

    try:
        offres = client.search_offers(
            keyword=keyword,
            departement=departement,
            limit=limit,
            publiee_depuis=31,
            sort=1,
        )
    except FranceTravailApiError as exc:
        logger.error("API error: %s", exc)
        return

    print(f"\nNombre d'offres reçues : {len(offres)}\n")
    for i, offre in enumerate(offres, start=1):
        oid = offre.get("id") or offre.get("idOffre")
        titre = offre.get("intitule")
        lieu_travail = offre.get("lieuTravail") or {}
        lieu = lieu_travail.get("libelle")
        type_contrat = offre.get("typeContrat")
        print(f"{i:02d}. id={oid} | {titre} | {lieu} | contrat={type_contrat}")
    print()


if __name__ == "__main__":
    main()
