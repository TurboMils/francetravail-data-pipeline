#!/usr/bin/env python3
"""
Pipeline ETL simple :
- Extract : FranceTravailClient
- Transform : cleaner + validator
- Load : repository vers SQLite
"""

import argparse

from config.logging_config import get_logger
from db.repository import OfferRepository
from db.sessions import get_session, init_db
from etl.extractors.france_travail_api import FranceTravailClient, FranceTravailApiError
from etl.transformers.cleaner import clean_offer
from etl.transformers.validator import validate_offer

logger = get_logger(__name__)


def run_etl(limit: int) -> None:
    logger.info("Initializing database...")
    init_db()

    client = FranceTravailClient()

    keyword = "developpeur python"
    departement = "75"

    # ========== Extract ==========
    try:
        raw_offers = client.search_offers(
            keyword=keyword,
            departement=departement,
            limit=limit,
            publiee_depuis=7,
            sort=1,
        )
    except FranceTravailApiError as exc:
        logger.error("API error while fetching offers: %s", exc)
        return

    logger.info("Extracted %d raw offers from API", len(raw_offers))

    # ========== Transform ==========
    cleaned_offers = []
    skipped_invalid = 0

    for raw in raw_offers:
        ok, errors = validate_offer(raw)
        if not ok:
            skipped_invalid += 1
            logger.warning("Skipping invalid offer (id=%s): %s", raw.get("id"), errors)
            continue

        cleaned = clean_offer(raw)
        cleaned_offers.append(cleaned)

    logger.info(
        "Transform step complete: %d cleaned offers, %d invalid skipped",
        len(cleaned_offers),
        skipped_invalid,
    )

    if not cleaned_offers:
        logger.warning("No valid offers to load. Exiting.")
        return

    # ========== Load ==========
    session = get_session()
    try:
        repo = OfferRepository(session)
        created, updated = repo.upsert_many_from_api(cleaned_offers)
    finally:
        session.close()

    logger.info(
        "Load step complete: created=%d, updated=%d (total persisted=%d)",
        created,
        updated,
        created + updated,
    )
    print(
        f"ETL complete: extracted={len(raw_offers)}, cleaned={len(cleaned_offers)}, "
        f"created={created}, updated={updated}, skipped_invalid={skipped_invalid}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run simple ETL pipeline for France Travail offers")
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Nombre maximum d'offres à récupérer",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_etl(limit=args.limit)
