from __future__ import annotations

import argparse

from config.logging_config import get_logger, setup_logging
from etl.extractors.france_travail_api import FranceTravailClient
from kafka_producer.producer import OfferKafkaProducer

logger = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Produce France Travail offers to Kafka")
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="Nombre d'offres à produire (approx, selon ce que renvoie l'API)",
    )
    args = parser.parse_args()

    setup_logging()

    client = FranceTravailClient()
    producer = OfferKafkaProducer()

    logger.info("Fetching offers from France Travail API...")
    offers = client.search_offers(
        limit=args.count,
        publiee_depuis=7,
    )

    if not offers:
        logger.warning("No offers returned by API")
        return

    # On tronque au count demandé si besoin
    offers_to_send = offers[: args.count]
    logger.info("Publishing %d offers to Kafka...", len(offers_to_send))
    producer.produce_offers(offers_to_send)


if __name__ == "__main__":
    main()
