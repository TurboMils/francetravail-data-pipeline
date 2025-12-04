# src/airflow_dags/extract_offers.py
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from config.logging_config import get_logger
from config.settings import settings
from etl.extractors.auth import FranceTravailAuth
from etl.extractors.france_travail_api import FranceTravailClient
from etl.loaders.kafka_loader import publish_offers_batch_to_kafka

logger = get_logger(__name__)

DAG_ID = "francetravail_extract_offers"


def task_check_api_health(**context) -> None:
    """
    Vérifie qu'on peut s'authentifier auprès de France Travail.
    En cas d'échec → la tâche échoue, le DAG sera retenté.
    """
    logger.info("Checking France Travail API health...")
    auth = FranceTravailAuth()
    token = auth.get_access_token()
    if not token:
        raise RuntimeError("Unable to obtain France Travail access token")
    logger.info("France Travail API health OK (token length=%d)", len(token))


def task_extract_and_publish(**context) -> dict:
    """
    Extrait les offres des dernières 24h et les publie sur Kafka (topic raw).
    Retourne un dict avec les stats, stocké en XCom.
    """
    departements = (
        ",".join(settings.etl_default_departments) if settings.etl_default_departments else None
    )
    keywords = ",".join(settings.etl_default_keywords) if settings.etl_default_keywords else None
    logger.info("Extracting offers for departements: %s", departements or "all")

    try:
        client = FranceTravailClient()
        logger.info("Connected to France Travail API")

        raw_offers = client.search_offers(
            keyword=keywords,
            departement=departements,
            publiee_depuis=settings.etl_lookback_days,
            limit=settings.france_travail_max_results_per_page,
        )
    except Exception as e:
        logger.error("Error during offer extraction: %s", e, exc_info=True)
        raise

    nb_extraites = len(raw_offers)
    logger.info("Extracted %d raw offers from France Travail", nb_extraites)

    if nb_extraites > 0:
        publish_offers_batch_to_kafka(
            offers=raw_offers,
            topic=settings.kafka_topic_raw_offers,
        )
        logger.info(
            "Published %d raw offers to Kafka topic '%s'",
            nb_extraites,
            settings.kafka_topic_raw_offers,
        )
    else:
        logger.info("No offers to publish for this run")

    # Ce dict sera récupéré par log_stats via XCom
    return {
        "nb_offres_extraites": nb_extraites,
        "nb_offres_publiees": nb_extraites,
        "params": {
            "departement": settings.etl_default_departments,
            "publieeDepuis": settings.etl_lookback_days,
        },
    }


def task_log_stats(**context) -> None:
    """
    Logue les stats dans la table ingestion_logs.
    """
    ti = context["ti"]
    stats = ti.xcom_pull(task_ids="extract_and_publish", key="return_value") or {}

    nb_offres_extraites = stats.get("nb_offres_extraites", 0)
    nb_offres_publiees = stats.get("nb_offres_publiees", 0)

    logger.info(
        "Logging ingestion stats: extracted=%d, published=%d",
        nb_offres_extraites,
        nb_offres_publiees,
    )


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id=DAG_ID,
    default_args=default_args,
    description="Extraction périodique des offres France Travail et publication vers Kafka",
    schedule=settings.etl_schedule_interval,
    start_date=datetime(2025, 1, 1),
    catchup=settings.etl_catchup,
    max_active_runs=settings.etl_max_active_runs,
    tags=["francetravail", "etl", "kafka"],
) as dag:

    check_api = PythonOperator(
        task_id="check_api_health",
        python_callable=task_check_api_health,
        provide_context=True,
    )

    extract_and_publish = PythonOperator(
        task_id="extract_and_publish",
        python_callable=task_extract_and_publish,
        provide_context=True,
    )

    log_stats = PythonOperator(
        task_id="log_stats",
        python_callable=task_log_stats,
        provide_context=True,
    )

    check_api >> extract_and_publish >> log_stats
