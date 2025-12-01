#!/usr/bin/env python3
from config.logging_config import get_logger
from etl.loaders.kafka_loader import publish_offers_batch_to_kafka

logger = get_logger(__name__)

def main() -> None:
    # 3-4 offres factices
    offers = [
        {"id": "test-1", "intitule": "Offre test 1", "departement": "75"},
        {"id": "test-2", "intitule": "Offre test 2", "departement": "92"},
        {"id": "test-3", "intitule": "Offre test 3", "departement": "93"},
    ]

    logger.info("Sending %d test offers to Kafka...", len(offers))
    sent = publish_offers_batch_to_kafka(
        offers=offers,
        topic="francetravail_offres_raw",
        key_field="id",
    )
    logger.info("Test complete, sent=%d", sent)


if __name__ == "__main__":
    main()
