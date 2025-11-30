from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration globale de l'application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ============================================
    # Environment
    # ============================================
    environment: Literal["development", "staging", "production"] = "development"

    # ============================================
    # API France Travail
    # ============================================
    france_travail_client_id: str = Field(..., description="Client ID API France Travail")
    france_travail_client_secret: str = Field(..., description="Client Secret API France Travail")
    france_travail_api_url: str = "https://api.francetravail.io/partenaire"
    france_travail_token_url: str = (
        "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire"
    )
    france_travail_scope: str = "api_offresdemploiv2 o2dsoffre"

    france_travail_max_results_per_page: int = 150
    france_travail_max_pages: int = 10
    france_travail_request_timeout: int = 30
    france_travail_retry_attempts: int = 3
    france_travail_retry_delay: int = 5

    @property
    def france_travail_offers_url(self) -> str:
        return f"{self.france_travail_api_url}/offresdemploi/v2/offres"

    # ============================================
    # PostgreSQL
    # ============================================
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "francetravail_jobs"
    postgres_user: str = "ft_user"
    postgres_password: str = Field(..., description="PostgreSQL password")

    postgres_pool_size: int = 5
    postgres_max_overflow: int = 10
    postgres_pool_timeout: int = 30
    postgres_pool_recycle: int = 3600

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def async_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ============================================
    # Kafka
    # ============================================
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_raw_offers: str = "francetravail_offres_raw"
    kafka_topic_dlq: str = "francetravail_offres_dlq"
    kafka_consumer_group: str = "francetravail-consumer"
    kafka_auto_offset_reset: Literal["earliest", "latest"] = "earliest"
    kafka_enable_auto_commit: bool = False
    kafka_max_poll_records: int = 100
    kafka_session_timeout_ms: int = 30000

    kafka_producer_acks: Literal["0", "1", "all"] = "all"
    kafka_producer_retries: int = 3
    kafka_producer_compression_type: str = "gzip"

    # ============================================
    # Airflow
    # ============================================
    airflow_home: str = "/opt/airflow"
    airflow_dags_folder: str = "/opt/airflow/dags"

    # ============================================
    # FastAPI
    # ============================================
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    api_workers: int = 1
    api_title: str = "France Travail Data API"
    api_version: str = "1.0.0"
    api_description: str = "API d'accès aux offres d'emploi France Travail"

    api_cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:8501", "http://localhost:3000"]
    )
    api_cors_allow_credentials: bool = True
    api_cors_allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    api_cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])

    # ============================================
    # Streamlit
    # ============================================
    streamlit_port: int = 8501
    streamlit_api_url: str = "http://localhost:8000"

    # ============================================
    # Logging
    # ============================================
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "text"] = "text"
    log_file: str | None = None

    # ============================================
    # ETL / DAG
    # ============================================
    etl_schedule_interval: str = "0 * * * *"
    etl_catchup: bool = False
    etl_max_active_runs: int = 1

    etl_default_departments: list[str] = Field(default_factory=lambda: ["75", "92", "93", "94"])
    etl_default_contract_types: list[str] = Field(default_factory=lambda: ["CDI", "CDD"])
    etl_lookback_days: int = 7

    @field_validator("kafka_bootstrap_servers")
    @classmethod
    def validate_kafka_servers(cls, v: str) -> str:
        if not v:
            raise ValueError("Kafka bootstrap servers cannot be empty")
        return v

    @field_validator("api_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
