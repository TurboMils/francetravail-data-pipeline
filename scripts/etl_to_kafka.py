#!/usr/bin/env python3

import argparse

from config.logging_config import get_logger
from etl.extractors.france_travail_api import FranceTravailClient, FranceTravailApiError
from kafka_producer.producer import OfferKafkaProducer
from config.settings import settings

logger = get_logger(__name__)


def run_etl_to_kafka(limit: int) -> None:
    client = FranceTravailClient()
    producer = OfferKafkaProducer()

    departements = ",".join(settings.etl_default_departments) if settings.etl_default_departments else None
    keywords = " ".join(settings.etl_default_keywords) if settings.etl_default_keywords else None

    logger.info(
        "Running ETL→Kafka with limit=%d, departements=%s, keywords=%s",
        limit,
        departements or "all",
        keywords or "none",
    )

    # ========== Extract ==========
    try:
        raw_offers = client.search_offers(
            keyword=keywords,
            departement=departements,
            limit=limit,
            sort=1,
        )
    except FranceTravailApiError as exc:
        logger.error("API error while fetching offers: %s", exc)
        return

    logger.info("Extracted %d raw offers from API", len(raw_offers))

    if not raw_offers:
        logger.info("No offers to send to Kafka, exiting.")
        return

    # ========== Load → Kafka ==========
    sent = producer.produce_offers(raw_offers)
    logger.info("ETL→Kafka complete: extracted=%d, sent_to_kafka=%d", len(raw_offers), sent)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ETL pipeline to Kafka for France Travail offers")
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Nombre maximum d'offres à récupérer",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_etl_to_kafka(limit=args.limit)
